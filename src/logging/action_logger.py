"""
核心行动日志器

负责：
1. 异步日志记录（QueueHandler + 后台线程）
2. 后台线程健康检查和自动恢复（11.2.2 高风险项）
3. Ctrl+C 信号处理（SIGINT）
4. 队列管理和批量写入
"""
import logging
import queue
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

from .types import ActionData, ActionStatus
from .log_writer import LogWriter
from .masking import DataMasker
from .constants import (
    DEFAULT_QUEUE_SIZE,
    DEFAULT_BATCH_SIZE,
    DEFAULT_BATCH_TIMEOUT,
    WORKER_HEARTBEAT_TIMEOUT,
    WORKER_RESTART_MAX_ATTEMPTS,
)

logger = logging.getLogger(__name__)


class ActionLogger:
    """
    行动日志器

    核心功能：
    - 异步日志记录（非阻塞）
    - 后台线程批量写入
    - 健康检查和自动恢复
    - Ctrl+C 安全退出
    """

    _instance: Optional["ActionLogger"] = None
    _lock = threading.Lock()

    def __init__(
        self,
        log_dir: Path,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        batch_size: int = DEFAULT_BATCH_SIZE,
        batch_timeout: float = DEFAULT_BATCH_TIMEOUT,
        enabled: bool = True,
        masker: Optional[DataMasker] = None,
        session_manager=None,
    ):
        """
        初始化日志器

        Args:
            log_dir: 日志目录
            queue_size: 队列大小
            batch_size: 批量写入大小
            batch_timeout: 批量写入超时（秒）
            enabled: 是否启用日志
            masker: 数据脱敏器（可选）
            session_manager: SessionManager实例（用于获取当前session_id）
        """
        self.enabled = enabled
        if not self.enabled:
            logger.info("ActionLogger disabled by configuration")
            return

        self.log_dir = Path(log_dir).expanduser()
        self.queue_size = queue_size
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout

        # 队列和线程
        self._queue: queue.Queue = queue.Queue(maxsize=queue_size)
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False

        # 健康检查
        self._last_heartbeat = time.time()
        self._worker_alive = True
        self._restart_attempts = 0

        # 日志写入器
        self._writer = LogWriter(self.log_dir)

        # 数据脱敏器
        self._masker = masker or DataMasker(enabled=True)

        # SessionManager（用于获取当前session_id）
        self._session_manager = session_manager

        # 行动计数器（全局递增）
        self._action_counter = 0
        self._counter_lock = threading.Lock()

        # 启动后台线程
        self._start_worker()

        # 注册信号处理器（Ctrl+C）
        self._register_signal_handlers()

        logger.info(
            f"ActionLogger initialized: queue_size={queue_size}, "
            f"batch_size={batch_size}, batch_timeout={batch_timeout}s"
        )

    @classmethod
    def get_instance(cls, **kwargs) -> "ActionLogger":
        """获取单例实例（线程安全）"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(**kwargs)
        return cls._instance

    def set_session_manager(self, session_manager) -> None:
        """
        设置SessionManager实例

        Args:
            session_manager: SessionManager实例
        """
        self._session_manager = session_manager

    def log(
        self,
        action_type: str,
        session_id: Optional[str] = None,
        status: str = ActionStatus.SUCCESS,
        execution_id: Optional[str] = None,
        **data
    ) -> None:
        """
        记录行动（异步，非阻塞）

        Args:
            action_type: 行动类型
            session_id: 会话ID（可选，默认从session_manager获取）
            status: 状态
            execution_id: 执行ID（可选）
            **data: 具体数据字段
        """
        if not self.enabled:
            return

        try:
            # 如果没有传入session_id，从session_manager获取
            if session_id is None and self._session_manager:
                session_id = self._session_manager.get_current_session_id()

            # 如果仍然没有session_id，使用默认值
            if session_id is None:
                session_id = "unknown"

            # 健康检查
            if not self._is_worker_healthy():
                self._handle_unhealthy_worker()

            # 创建行动数据
            action_data = ActionData.create(
                action_type=action_type,
                session_id=session_id,
                status=status,
                execution_id=execution_id,
                **data
            )

            # 分配全局行动序号
            with self._counter_lock:
                self._action_counter += 1
                action_data.action_number = self._action_counter

            # 数据脱敏
            raw_dict = action_data.to_dict()
            masked_dict = self._masker.mask(raw_dict)

            # 放入队列（非阻塞）
            self._queue.put_nowait(masked_dict)

        except queue.Full:
            # Phase 1: 简单丢弃策略
            logger.warning(
                f"Log queue full (size={self.queue_size}), dropping log: "
                f"{action_type}"
            )
        except Exception as e:
            logger.error(f"Failed to log action: {e}", exc_info=True)

    def flush(self) -> None:
        """
        强制刷新队列中的所有日志

        用途：
        1. Ctrl+C 退出时确保数据不丢失
        2. 程序正常退出前
        """
        if not self.enabled:
            return

        logger.info("Flushing log queue...")

        # 收集队列中的所有数据
        batch = []
        try:
            while not self._queue.empty():
                try:
                    record = self._queue.get_nowait()
                    batch.append(record)
                except queue.Empty:
                    break

            # 批量写入
            if batch:
                self._writer.write_batch(batch)
                logger.info(f"Flushed {len(batch)} records")

        except Exception as e:
            logger.error(f"Failed to flush queue: {e}", exc_info=True)

    def shutdown(self) -> None:
        """
        关闭日志器

        步骤：
        1. 停止后台线程
        2. 刷新队列
        3. 关闭文件句柄
        """
        if not self.enabled:
            return

        logger.info("Shutting down ActionLogger...")

        # 停止后台线程
        self._running = False
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5)

        # 刷新剩余日志
        self.flush()

        # 关闭文件
        self._writer.close()

        logger.info("ActionLogger shut down")

    # ========== 后台线程管理 ==========

    def _start_worker(self) -> None:
        """启动后台线程"""
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._worker,
            name="ActionLogger-Worker",
            daemon=True
        )
        self._worker_thread.start()
        logger.info("Worker thread started")

    def _worker(self) -> None:
        """
        后台线程：批量写入日志

        逻辑：
        1. 从队列收集一批日志（最多batch_size条或等待batch_timeout秒）
        2. 批量写入文件
        3. 更新心跳时间
        4. 捕获所有异常，避免线程崩溃
        """
        logger.info("Worker thread running")

        try:
            while self._running:
                # 收集一批日志
                batch = self._collect_batch()

                # 批量写入
                if batch:
                    try:
                        self._writer.write_batch(batch)
                    except Exception as e:
                        logger.error(f"Worker failed to write batch: {e}")
                        # 降级到 stderr
                        self._fallback_to_stderr(batch)

                # 更新心跳
                self._last_heartbeat = time.time()

        except Exception as e:
            # 捕获所有未预期的异常
            logger.error(f"Worker thread crashed: {e}", exc_info=True)
            self._worker_alive = False

        logger.info("Worker thread exited")

    def _collect_batch(self) -> List[Dict[str, Any]]:
        """
        从队列收集一批日志

        策略：
        - 收集最多 batch_size 条日志
        - 或者等待 batch_timeout 秒超时

        Returns:
            日志记录列表
        """
        batch = []
        deadline = time.time() + self.batch_timeout

        while len(batch) < self.batch_size and time.time() < deadline:
            try:
                # 计算剩余时间
                timeout = max(0.01, deadline - time.time())
                record = self._queue.get(timeout=timeout)
                batch.append(record)
            except queue.Empty:
                break

        return batch

    # ========== 健康检查和恢复（11.2.2 高风险项） ==========

    def _is_worker_healthy(self) -> bool:
        """
        检查后台线程是否健康

        检查项：
        1. 线程存活
        2. 心跳正常（10秒内有心跳）

        Returns:
            是否健康
        """
        if not self._worker_thread or not self._worker_thread.is_alive():
            logger.warning("Worker thread is not alive")
            return False

        if time.time() - self._last_heartbeat > WORKER_HEARTBEAT_TIMEOUT:
            logger.warning(
                f"Worker heartbeat timeout "
                f"(last: {time.time() - self._last_heartbeat:.1f}s ago)"
            )
            return False

        return True

    def _handle_unhealthy_worker(self) -> None:
        """
        处理不健康的后台线程

        策略：
        1. 尝试重启（最多3次）
        2. 重启失败后降级到同步模式
        """
        if self._restart_attempts >= WORKER_RESTART_MAX_ATTEMPTS:
            logger.error(
                f"Worker restart failed after {WORKER_RESTART_MAX_ATTEMPTS} attempts, "
                "future logs will be written synchronously"
            )
            return

        logger.warning(f"Attempting to restart worker (attempt {self._restart_attempts + 1})")

        try:
            # 停止旧线程
            self._running = False
            if self._worker_thread and self._worker_thread.is_alive():
                self._worker_thread.join(timeout=2)

            # 重置状态
            self._worker_alive = True
            self._last_heartbeat = time.time()

            # 启动新线程
            self._start_worker()

            self._restart_attempts += 1
            logger.info("Worker restarted successfully")

        except Exception as e:
            logger.error(f"Failed to restart worker: {e}", exc_info=True)
            self._restart_attempts += 1

    def _fallback_to_stderr(self, batch: List[Dict[str, Any]]) -> None:
        """
        降级到 stderr（当文件写入失败时）

        Args:
            batch: 日志批次
        """
        for record in batch:
            try:
                sys.stderr.write(f"[LOG FALLBACK] {record}\n")
            except Exception:
                pass  # 最后的降级手段，忽略所有错误

    # ========== Ctrl+C 信号处理 ==========

    def _register_signal_handlers(self) -> None:
        """注册信号处理器（SIGINT - Ctrl+C）"""
        def signal_handler(sig, frame):
            logger.info("Interrupt signal received (Ctrl+C), flushing logs...")
            self.flush()
            sys.exit(0)

        try:
            signal.signal(signal.SIGINT, signal_handler)
            logger.info("SIGINT handler registered")
        except Exception as e:
            logger.warning(f"Failed to register signal handler: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
