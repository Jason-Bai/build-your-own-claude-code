"""Client implementations for different LLM providers"""

from .base import BaseClient, ModelResponse, StreamChunk
from .factory import create_client, check_provider_available

# 延迟导入可选的客户端，避免在未安装依赖时出错
# OpenAI 客户端 - 可选
OpenAIClient = None
try:
    from .openai import OpenAIClient
except Exception:
    # 如果 openai 包未安装，就保持 None
    pass

# Google 客户端 - 可选
GoogleClient = None
try:
    from .google import GoogleClient
except Exception:
    # 如果 google 包未安装，就保持 None
    pass

# Anthropic 客户端
from .anthropic import AnthropicClient

__all__ = [
    "BaseClient",
    "ModelResponse",
    "StreamChunk",
    "AnthropicClient",
    "OpenAIClient",
    "GoogleClient",
    "create_client",
    "check_provider_available",
]
