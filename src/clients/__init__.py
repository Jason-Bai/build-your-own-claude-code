"""Client implementations for different LLM providers"""

from .base import BaseClient, ModelResponse, StreamChunk
from .factory import create_client, check_provider_available

# Anthropic 客户端
from .anthropic import AnthropicClient

# 延迟导入可选的客户端，避免在未安装依赖时出错
# OpenAI 客户端 - 可选
OpenAIClient = None
KimiClient = None
try:
    from .openai import OpenAIClient
    from .kimi import KimiClient
except Exception:
    # 如果 openai 包未安装，就保持 None
    pass

__all__ = [
    "BaseClient",
    "ModelResponse",
    "StreamChunk",
    "AnthropicClient",
    "OpenAIClient",
    "KimiClient",
    "create_client",
    "check_provider_available",
]
