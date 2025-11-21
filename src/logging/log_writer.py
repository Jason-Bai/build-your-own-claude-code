"""
日志文件写入器

负责：
1. JSON Lines 格式写入
2. 按日期分割文件
3. 批量写入优化
4. 文件句柄管理
"""
import json
import logging
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Any, Optional

from .constants import (
    LOG_FILE_DATE_FORMAT,
    LOG_FILE_EXTENSION,
)

logger = logging.getLogger(__name__)


class LogWriter:
    """日志文件写入器"""

    def __init__(self, log_dir: Path):
        """
        初始化写入器

        Args:
            log_dir: 日志目录路径
        """
        self.log_dir = Path(log_dir).expanduser()
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._current_date: Optional[date] = None
        self._file_handle: Optional[Any] = None

        logger.info(f"LogWriter initialized with log_dir: {self.log_dir}")

    def write_batch(self, records: List[Dict[str, Any]]) -> None:
        """
        批量写入日志记录

        Args:
            records: 日志记录列表
        """
        if not records:
            return

        try:
            # 检查是否需要轮转文件
            self._rotate_if_needed()

            # 批量写入
            for record in records:
                json_line = json.dumps(record, ensure_ascii=False)
                self._file_handle.write(json_line + "\n")

            # 强制刷新到磁盘
            self._file_handle.flush()
            import os
            os.fsync(self._file_handle.fileno())  # 确保数据真正写入磁盘

            logger.debug(f"Successfully wrote {len(records)} records")

        except Exception as e:
            logger.error(f"Failed to write batch: {e}", exc_info=True)
            # 重新抛出异常，让上层处理（降级到stderr）
            raise

    def flush(self) -> None:
        """强制刷新缓冲区"""
        if self._file_handle:
            try:
                self._file_handle.flush()
                logger.debug("Flushed log file buffer")
            except Exception as e:
                logger.error(f"Failed to flush: {e}")

    def close(self) -> None:
        """关闭文件句柄"""
        if self._file_handle:
            try:
                self._file_handle.flush()
                self._file_handle.close()
                self._file_handle = None
                logger.info("LogWriter closed")
            except Exception as e:
                logger.error(f"Failed to close file handle: {e}")

    def _rotate_if_needed(self) -> None:
        """
        检查是否需要轮转日志文件（按日期）

        当日期变化时，关闭旧文件，打开新文件
        """
        today = datetime.now().date()

        if self._current_date == today and self._file_handle:
            # 日期未变化，无需轮转
            return

        # 关闭旧文件
        if self._file_handle:
            logger.info(f"Rotating log file from {self._current_date} to {today}")
            self._file_handle.close()

        # 打开新文件
        self._current_date = today
        log_file = self._get_log_file_path(today)

        # 追加模式打开（支持程序重启后继续写入同一天的日志）
        self._file_handle = open(log_file, "a", encoding="utf-8")

        logger.info(f"Opened log file: {log_file}")

    def _get_log_file_path(self, target_date: date) -> Path:
        """
        获取指定日期的日志文件路径

        Args:
            target_date: 目标日期

        Returns:
            日志文件路径
        """
        filename = target_date.strftime(LOG_FILE_DATE_FORMAT) + LOG_FILE_EXTENSION
        return self.log_dir / filename

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
