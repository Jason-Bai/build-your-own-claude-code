"""Client factory for creating appropriate LLM clients"""

from typing import Optional
from .base import BaseClient


def create_client(provider: str, api_key: str, **kwargs) -> BaseClient:
    """
    创建客户端工厂函数

    Args:
        provider: "anthropic" | "openai" | "kimi"
        api_key: API key
        **kwargs: 其他参数（如 model、api_base 等）

    Returns:
        BaseClient 实例
    """
    if provider == "anthropic":
        from .anthropic import AnthropicClient
        return AnthropicClient(api_key, **kwargs)
    elif provider == "openai":
        try:
            from .openai import OpenAIClient
            return OpenAIClient(api_key, **kwargs)
        except ImportError as e:
            raise ImportError(
                f"Cannot use OpenAI provider: {e}\n"
                "Please install the openai package: pip install openai"
            )
    elif provider == "kimi":
        try:
            from .kimi import KimiClient
            return KimiClient(api_key, **kwargs)
        except ImportError as e:
            raise ImportError(
                f"Cannot use Kimi provider: {e}\n"
                "Please install the openai package: pip install openai"
            )
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def check_provider_available(provider: str) -> bool:
    """
    检查提供商是否可用（包是否安装）

    Args:
        provider: "anthropic" | "openai" | "kimi"

    Returns:
        True 如果包已安装，False 否则
    """
    if provider == "anthropic":
        try:
            import anthropic
            return True
        except ImportError:
            return False
    elif provider == "openai":
        try:
            import openai
            return True
        except ImportError:
            return False
    elif provider == "kimi":
        try:
            import openai
            return True
        except ImportError:
            return False
    else:
        return False
