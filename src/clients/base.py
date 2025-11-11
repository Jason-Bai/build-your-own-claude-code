"""Base client interface for multi-model support"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncIterator
from dataclasses import dataclass


@dataclass
class ModelResponse:
    """统一的模型响应格式"""
    content: List[Dict[str, Any]]  # text blocks 和 tool_use blocks
    stop_reason: str
    usage: Dict[str, int]  # input_tokens, output_tokens
    model: str


@dataclass
class StreamChunk:
    """流式响应的数据块"""
    type: str  # "text" | "tool_use"
    content: Any


class BaseClient(ABC):
    """模型客户端抽象基类"""

    @abstractmethod
    async def create_message(
        self,
        system: str,
        messages: List[Dict],
        tools: List[Dict],
        max_tokens: int = 8000,
        temperature: float = 1.0,
        stream: bool = False
    ) -> ModelResponse | AsyncIterator[StreamChunk]:
        """
        创建消息

        Args:
            system: System prompt
            messages: 消息历史
            tools: 工具定义
            max_tokens: 最大输出 tokens
            temperature: 温度参数
            stream: 是否流式输出

        Returns:
            ModelResponse 或流式迭代器
        """
        pass

    @abstractmethod
    async def generate_summary(self, prompt: str) -> str:
        """
        生成摘要（用于上下文压缩）

        Args:
            prompt: 摘要提示

        Returns:
            摘要文本
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """返回模型名称"""
        pass

    @property
    @abstractmethod
    def context_window(self) -> int:
        """返回上下文窗口大小（tokens）"""
        pass
