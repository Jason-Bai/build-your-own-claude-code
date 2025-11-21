"""
单元测试：ActionLogger

测试内容：
1. 日志写入
2. 队列操作
3. 健康检查
4. 信号处理
5. 批量写入
"""
import json
import tempfile
import time
from pathlib import Path
from datetime import datetime

import pytest

from src.logging.action_logger import ActionLogger
from src.logging.types import ActionType, ActionStatus


@pytest.fixture
def temp_log_dir():
    """临时日志目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def logger(temp_log_dir):
    """测试日志器实例"""
    logger_instance = ActionLogger(
        log_dir=temp_log_dir,
        queue_size=10,
        batch_size=5,
        batch_timeout=0.5
    )
    yield logger_instance
    logger_instance.shutdown()


class TestActionLoggerBasics:
    """基础功能测试"""

    def test_logger_initialization(self, logger, temp_log_dir):
        """测试日志器初始化"""
        assert logger.enabled is True
        assert logger.log_dir == temp_log_dir
        assert logger._running is True
        assert logger._worker_thread is not None
        assert logger._worker_thread.is_alive()

    def test_log_single_action(self, logger, temp_log_dir):
        """测试单条日志记录"""
        logger.log(
            action_type=ActionType.USER_INPUT,
            session_id="test-session-001",
            content="Hello world",
            input_mode="interactive"
        )

        # 等待后台线程处理
        time.sleep(1)
        logger.flush()

        # 验证日志文件存在
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = temp_log_dir / f"{today}.jsonl"
        assert log_file.exists()

        # 验证日志内容
        with open(log_file, "r") as f:
            line = f.readline()
            record = json.loads(line)
            assert record["action_type"] == ActionType.USER_INPUT
            assert record["session_id"] == "test-session-001"
            assert record["content"] == "Hello world"
            assert record["action_number"] == 1

    def test_log_multiple_actions(self, logger, temp_log_dir):
        """测试多条日志记录"""
        for i in range(10):
            logger.log(
                action_type=ActionType.USER_INPUT,
                session_id=f"session-{i}",
                content=f"Message {i}"
            )

        # 刷新并验证
        time.sleep(1)
        logger.flush()

        today = datetime.now().strftime("%Y-%m-%d")
        log_file = temp_log_dir / f"{today}.jsonl"

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 10

        for i, line in enumerate(lines):
            record = json.loads(line)
            assert record["action_number"] == i + 1
            assert record["content"] == f"Message {i}"

    def test_action_counter_increment(self, logger):
        """测试行动计数器递增"""
        logger.log(ActionType.USER_INPUT, "session-1", content="Test 1")
        logger.log(ActionType.USER_COMMAND, "session-1", command="/status")
        logger.log(ActionType.AGENT_STATE_CHANGE, "session-1", from_state="IDLE")

        time.sleep(1)
        logger.flush()

        assert logger._action_counter == 3


class TestQueueOperations:
    """队列操作测试"""

    def test_queue_full_behavior(self, temp_log_dir):
        """测试队列满时的行为（丢弃策略）"""
        logger_instance = ActionLogger(
            log_dir=temp_log_dir,
            queue_size=5,  # 小队列
            batch_size=100,  # 大批次（让队列更容易满）
            batch_timeout=10  # 长超时（延迟处理）
        )

        # 快速填满队列
        for i in range(20):
            logger_instance.log(
                ActionType.USER_INPUT,
                "session-1",
                content=f"Message {i}"
            )

        # 验证队列大小不超过限制
        assert logger_instance._queue.qsize() <= 5

        logger_instance.shutdown()

    def test_flush_empties_queue(self, logger, temp_log_dir):
        """测试 flush() 清空队列"""
        # 添加日志但不让后台线程处理
        for i in range(5):
            logger.log(ActionType.USER_INPUT, "session-1", content=f"Test {i}")

        # 队列应该有数据
        assert logger._queue.qsize() > 0

        # 刷新队列
        logger.flush()

        # 队列应该为空
        assert logger._queue.qsize() == 0


class TestWorkerHealth:
    """后台线程健康检查测试"""

    def test_worker_is_healthy_initially(self, logger):
        """测试初始状态健康"""
        assert logger._is_worker_healthy() is True

    def test_worker_heartbeat_updates(self, logger):
        """测试心跳更新"""
        initial_heartbeat = logger._last_heartbeat

        # 记录日志触发后台线程活动
        logger.log(ActionType.USER_INPUT, "session-1", content="Test")
        time.sleep(1)

        # 心跳应该更新
        assert logger._last_heartbeat > initial_heartbeat


class TestBatchWriting:
    """批量写入测试"""

    def test_batch_collection(self, logger):
        """测试批量收集逻辑"""
        # 添加多条日志
        for i in range(3):
            logger._queue.put({"test": i})

        # 收集批次（batch_size=5, 应该收集3条）
        batch = logger._collect_batch()
        assert len(batch) == 3

    def test_batch_timeout(self, logger):
        """测试批量超时逻辑"""
        # 添加少量日志（少于batch_size）
        logger._queue.put({"test": 1})

        # 等待超时（batch_timeout=0.5s）
        start = time.time()
        batch = logger._collect_batch()
        elapsed = time.time() - start

        # 应该收集到1条，且耗时接近batch_timeout
        assert len(batch) == 1
        assert 0.4 < elapsed < 0.7


class TestSignalHandling:
    """信号处理测试"""

    def test_flush_on_shutdown(self, logger, temp_log_dir):
        """测试关闭时刷新队列"""
        # 添加日志
        for i in range(5):
            logger.log(ActionType.USER_INPUT, "session-1", content=f"Test {i}")

        # 关闭（应该自动刷新）
        logger.shutdown()

        # 验证所有日志都写入了
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = temp_log_dir / f"{today}.jsonl"

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 5


class TestDisabledLogger:
    """禁用日志器测试"""

    def test_disabled_logger_no_files(self, temp_log_dir):
        """测试禁用日志器不创建文件"""
        logger_instance = ActionLogger(
            log_dir=temp_log_dir,
            enabled=False
        )

        # 尝试记录日志
        logger_instance.log(ActionType.USER_INPUT, "session-1", content="Test")
        time.sleep(1)

        # 应该没有日志文件
        log_files = list(temp_log_dir.glob("*.jsonl"))
        assert len(log_files) == 0

        logger_instance.shutdown()
