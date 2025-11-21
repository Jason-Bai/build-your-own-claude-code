"""
Log maintenance and disk management

Handles:
- Log rotation (by date)
- Retention policies (keep last N days)
- Cleanup (delete old logs)
- Disk usage monitoring
"""
import os
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class LogMaintenance:
    """Log maintenance manager for disk management"""

    def __init__(
        self,
        log_dir: Path,
        retention_days: int = 30,
        max_size_mb: int = 1000,
        compress_after_days: int = 7,
        enabled: bool = True
    ):
        """
        Initialize log maintenance

        Args:
            log_dir: Log directory path
            retention_days: Keep logs for this many days (default: 30)
            max_size_mb: Maximum total log size in MB (default: 1000)
            compress_after_days: Compress logs older than N days (default: 7)
            enabled: Enable maintenance (default: True)
        """
        self.log_dir = Path(log_dir).expanduser()
        self.retention_days = retention_days
        self.max_size_mb = max_size_mb
        self.compress_after_days = compress_after_days
        self.enabled = enabled

    def run_maintenance(self) -> Dict[str, any]:
        """
        Run full maintenance cycle

        Returns:
            Statistics dict with deleted/compressed file counts and space freed
        """
        if not self.enabled:
            return {"enabled": False}

        stats = {
            "deleted_files": 0,
            "compressed_files": 0,
            "space_freed_mb": 0,
            "total_size_mb": 0
        }

        try:
            # 1. Compress old logs
            compressed = self._compress_old_logs()
            stats["compressed_files"] = len(compressed)

            # 2. Delete logs past retention
            deleted, space_freed = self._delete_old_logs()
            stats["deleted_files"] = len(deleted)
            stats["space_freed_mb"] = space_freed / (1024 * 1024)

            # 3. Check if we exceed max size
            total_size = self._get_total_size()
            stats["total_size_mb"] = total_size / (1024 * 1024)

            if total_size > self.max_size_mb * 1024 * 1024:
                # Delete oldest logs until under limit
                additional_deleted, additional_freed = self._cleanup_to_size_limit()
                stats["deleted_files"] += len(additional_deleted)
                stats["space_freed_mb"] += additional_freed / (1024 * 1024)

            logger.info(f"Maintenance complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Maintenance failed: {e}", exc_info=True)
            return {"error": str(e)}

    def _compress_old_logs(self) -> List[Path]:
        """
        Compress logs older than compress_after_days

        Returns:
            List of compressed file paths
        """
        compressed = []
        cutoff_date = datetime.now() - timedelta(days=self.compress_after_days)

        if not self.log_dir.exists():
            return compressed

        for log_file in self.log_dir.glob("*.jsonl"):
            try:
                # Parse date from filename (YYYY-MM-DD.jsonl)
                date_str = log_file.stem
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                if file_date < cutoff_date:
                    # Compress the file
                    compressed_path = log_file.with_suffix(".jsonl.gz")
                    if not compressed_path.exists():
                        with open(log_file, "rb") as f_in:
                            with gzip.open(compressed_path, "wb") as f_out:
                                shutil.copyfileobj(f_in, f_out)

                        # Delete original after successful compression
                        log_file.unlink()
                        compressed.append(compressed_path)
                        logger.debug(f"Compressed: {log_file} -> {compressed_path}")

            except (ValueError, Exception) as e:
                logger.warning(f"Failed to compress {log_file}: {e}")
                continue

        return compressed

    def _delete_old_logs(self) -> tuple[List[Path], int]:
        """
        Delete logs older than retention_days

        Returns:
            Tuple of (deleted file paths, total space freed in bytes)
        """
        deleted = []
        space_freed = 0
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        if not self.log_dir.exists():
            return deleted, space_freed

        # Check both .jsonl and .jsonl.gz files
        for pattern in ["*.jsonl", "*.jsonl.gz"]:
            for log_file in self.log_dir.glob(pattern):
                try:
                    # Parse date from filename
                    if pattern == "*.jsonl.gz":
                        date_str = log_file.stem.replace(".jsonl", "")
                    else:
                        date_str = log_file.stem

                    file_date = datetime.strptime(date_str, "%Y-%m-%d")

                    if file_date < cutoff_date:
                        file_size = log_file.stat().st_size
                        log_file.unlink()
                        deleted.append(log_file)
                        space_freed += file_size
                        logger.debug(f"Deleted old log: {log_file}")

                except (ValueError, Exception) as e:
                    logger.warning(f"Failed to delete {log_file}: {e}")
                    continue

        return deleted, space_freed

    def _cleanup_to_size_limit(self) -> tuple[List[Path], int]:
        """
        Delete oldest logs to get under max_size_mb limit

        Returns:
            Tuple of (deleted file paths, total space freed in bytes)
        """
        deleted = []
        space_freed = 0

        if not self.log_dir.exists():
            return deleted, space_freed

        # Get all log files sorted by date (oldest first)
        log_files = []
        for pattern in ["*.jsonl", "*.jsonl.gz"]:
            for log_file in self.log_dir.glob(pattern):
                try:
                    if pattern == "*.jsonl.gz":
                        date_str = log_file.stem.replace(".jsonl", "")
                    else:
                        date_str = log_file.stem
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    log_files.append((file_date, log_file))
                except ValueError:
                    continue

        log_files.sort(key=lambda x: x[0])  # Sort by date

        # Delete oldest until under limit
        current_size = self._get_total_size()
        max_size_bytes = self.max_size_mb * 1024 * 1024

        for file_date, log_file in log_files:
            if current_size <= max_size_bytes:
                break

            try:
                file_size = log_file.stat().st_size
                log_file.unlink()
                deleted.append(log_file)
                space_freed += file_size
                current_size -= file_size
                logger.debug(f"Deleted to free space: {log_file}")
            except Exception as e:
                logger.warning(f"Failed to delete {log_file}: {e}")
                continue

        return deleted, space_freed

    def _get_total_size(self) -> int:
        """
        Get total size of all log files in bytes

        Returns:
            Total size in bytes
        """
        total = 0

        if not self.log_dir.exists():
            return total

        for pattern in ["*.jsonl", "*.jsonl.gz"]:
            for log_file in self.log_dir.glob(pattern):
                try:
                    total += log_file.stat().st_size
                except Exception:
                    continue

        return total

    def get_disk_usage_stats(self) -> Dict[str, any]:
        """
        Get disk usage statistics

        Returns:
            Dict with file counts, sizes, and oldest/newest dates
        """
        stats = {
            "total_files": 0,
            "uncompressed_files": 0,
            "compressed_files": 0,
            "total_size_mb": 0,
            "oldest_log": None,
            "newest_log": None
        }

        if not self.log_dir.exists():
            return stats

        dates = []

        # Count uncompressed files
        for log_file in self.log_dir.glob("*.jsonl"):
            stats["uncompressed_files"] += 1
            try:
                date_str = log_file.stem
                dates.append(datetime.strptime(date_str, "%Y-%m-%d"))
            except ValueError:
                pass

        # Count compressed files
        for log_file in self.log_dir.glob("*.jsonl.gz"):
            stats["compressed_files"] += 1
            try:
                date_str = log_file.stem.replace(".jsonl", "")
                dates.append(datetime.strptime(date_str, "%Y-%m-%d"))
            except ValueError:
                pass

        stats["total_files"] = stats["uncompressed_files"] + stats["compressed_files"]
        stats["total_size_mb"] = self._get_total_size() / (1024 * 1024)

        if dates:
            stats["oldest_log"] = min(dates).strftime("%Y-%m-%d")
            stats["newest_log"] = max(dates).strftime("%Y-%m-%d")

        return stats
