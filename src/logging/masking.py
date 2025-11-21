"""
数据脱敏模块

负责：
1. 敏感字段识别和脱敏
2. 基于正则的模式匹配脱敏
3. 递归处理嵌套字典
4. 可配置的脱敏规则
"""
import re
import logging
from typing import Dict, Any, List, Set

from .constants import (
    SENSITIVE_FIELD_NAMES,
    SENSITIVE_PATTERNS,
    LOG_OUTPUT_MAX_CHARS,
)

logger = logging.getLogger(__name__)


class DataMasker:
    """
    数据脱敏器

    功能：
    - 敏感字段名脱敏（password, api_key等）
    - 敏感模式脱敏（API密钥、Bearer token、文件路径）
    - 超长输出截断
    """

    def __init__(
        self,
        enabled: bool = True,
        custom_sensitive_fields: List[str] = None,
        truncate_large_output: bool = True,
        max_output_chars: int = LOG_OUTPUT_MAX_CHARS,
    ):
        """
        初始化脱敏器

        Args:
            enabled: 是否启用脱敏
            custom_sensitive_fields: 自定义敏感字段名列表
            truncate_large_output: 是否截断超长输出
            max_output_chars: 输出最大字符数
        """
        self.enabled = enabled
        self.truncate_large_output = truncate_large_output
        self.max_output_chars = max_output_chars

        # 敏感字段名集合（包含默认 + 自定义）
        self.sensitive_fields: Set[str] = set(SENSITIVE_FIELD_NAMES)
        if custom_sensitive_fields:
            self.sensitive_fields.update(custom_sensitive_fields)

        # 编译正则模式
        self._compiled_patterns = [
            (re.compile(pattern), replacement)
            for pattern, replacement in SENSITIVE_PATTERNS
        ]

        logger.info(
            f"DataMasker initialized: enabled={enabled}, "
            f"sensitive_fields={len(self.sensitive_fields)}"
        )

    def mask(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        脱敏字典数据（递归处理）

        Args:
            data: 原始数据字典

        Returns:
            脱敏后的数据字典
        """
        if not self.enabled:
            return data

        return self._mask_recursive(data)

    def _mask_recursive(self, obj: Any, depth: int = 0) -> Any:
        """
        递归脱敏对象

        Args:
            obj: 对象（可能是dict, list, str等）
            depth: 递归深度（防止无限递归）

        Returns:
            脱敏后的对象
        """
        # 防止无限递归
        if depth > 10:
            return "[MASKED: TOO_DEEP]"

        # 字典：递归处理每个字段
        if isinstance(obj, dict):
            masked = {}
            for key, value in obj.items():
                # 检查字段名是否敏感
                if self._is_sensitive_field(key):
                    masked[key] = "[MASKED]"
                else:
                    masked[key] = self._mask_recursive(value, depth + 1)
            return masked

        # 列表：递归处理每个元素
        elif isinstance(obj, list):
            return [self._mask_recursive(item, depth + 1) for item in obj]

        # 字符串：模式脱敏 + 截断
        elif isinstance(obj, str):
            masked_str = self._mask_patterns(obj)
            if self.truncate_large_output and len(masked_str) > self.max_output_chars:
                return self._truncate_string(masked_str)
            return masked_str

        # 其他类型：直接返回
        else:
            return obj

    def _is_sensitive_field(self, field_name: str) -> bool:
        """
        检查字段名是否敏感

        Args:
            field_name: 字段名

        Returns:
            是否敏感
        """
        # 不区分大小写匹配
        field_lower = field_name.lower()
        return field_lower in self.sensitive_fields

    def _mask_patterns(self, text: str) -> str:
        """
        基于正则模式的脱敏

        Args:
            text: 原始文本

        Returns:
            脱敏后的文本
        """
        masked = text

        for pattern, replacement in self._compiled_patterns:
            masked = pattern.sub(replacement, masked)

        return masked

    def _truncate_string(self, text: str) -> str:
        """
        截断超长字符串

        Args:
            text: 原始文本

        Returns:
            截断后的文本
        """
        truncated = text[: self.max_output_chars]
        remaining = len(text) - self.max_output_chars
        return f"{truncated}...[TRUNCATED {remaining} chars]"


# 全局脱敏器实例
_masker_instance: DataMasker = None


def init_masker(**kwargs) -> DataMasker:
    """
    初始化全局脱敏器

    Args:
        **kwargs: 配置参数

    Returns:
        DataMasker实例
    """
    global _masker_instance

    if _masker_instance is not None:
        return _masker_instance

    _masker_instance = DataMasker(**kwargs)
    return _masker_instance


def get_masker() -> DataMasker:
    """
    获取全局脱敏器实例

    Returns:
        DataMasker实例
    """
    global _masker_instance

    if _masker_instance is None:
        _masker_instance = init_masker()

    return _masker_instance
