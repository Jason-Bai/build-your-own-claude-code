"""
日志系统模块

提供结构化行动日志功能：
- 实时日志持久化
- Ctrl+C 安全
- 异步非阻塞
- 数据脱敏
- EventBus 集成
"""
from .action_logger import ActionLogger
from .types import ActionData, ActionType, ActionStatus
from .constants import DEFAULT_LOG_DIR
from .event_listener import LoggingEventListener, setup_logging_event_listener

# 全局日志器实例
_logger_instance: ActionLogger = None


def init_logger(
    log_dir: str = DEFAULT_LOG_DIR,
    enabled: bool = True,
    force_reinit: bool = False,
    **kwargs
) -> ActionLogger:
    """
    初始化全局日志器

    Args:
        log_dir: 日志目录
        enabled: 是否启用
        force_reinit: 强制重新初始化（测试用）
        **kwargs: 其他配置参数

    Returns:
        ActionLogger 实例
    """
    global _logger_instance

    if _logger_instance is not None and not force_reinit:
        return _logger_instance

    # 如果需要重新初始化，先关闭旧实例
    if _logger_instance is not None and force_reinit:
        _logger_instance.shutdown()

    _logger_instance = ActionLogger(
        log_dir=log_dir,
        enabled=enabled,
        **kwargs
    )

    return _logger_instance


def get_action_logger() -> ActionLogger:
    """
    获取全局日志器实例

    如果未初始化，则使用默认配置初始化

    Returns:
        ActionLogger 实例
    """
    global _logger_instance

    if _logger_instance is None:
        _logger_instance = init_logger()

    return _logger_instance


def shutdown_logger() -> None:
    """关闭全局日志器"""
    global _logger_instance

    if _logger_instance is not None:
        _logger_instance.shutdown()
        _logger_instance = None


__all__ = [
    "ActionLogger",
    "ActionData",
    "ActionType",
    "ActionStatus",
    "init_logger",
    "get_action_logger",
    "shutdown_logger",
    "LoggingEventListener",
    "setup_logging_event_listener",
]
