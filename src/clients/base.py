"""Base client interface for multi-model support"""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncIterator, Optional, TYPE_CHECKING
from dataclasses import dataclass
import logging

if TYPE_CHECKING:
    from ..utils.cancellation import CancellationToken

logger = logging.getLogger(__name__)


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

    # 通用的 finish_reason 映射表 - 各 provider 可以覆盖这个
    FINISH_REASON_MAPPING = {
        "STOP": "end_turn",
        "END_TURN": "end_turn",
        "MAX_TOKENS": "max_tokens",
        "SAFETY": "stop_sequence",
        "RECITATION": "stop_sequence",
        "OTHER": "stop_sequence",
        "TOOL_CALLS": "tool_use",
        "UNSPECIFIED": "end_turn",
    }

    def _normalize_finish_reason(self, finish_reason: Any) -> str:
        """
        标准化 finish_reason，处理各种格式（字符串、整数、对象等）

        Args:
            finish_reason: 原始 finish_reason（可能是字符串、整数或枚举对象）

        Returns:
            标准化的 finish_reason 字符串
        """
        if not finish_reason:
            return "end_turn"

        # 如果是整数，转换为字符串
        finish_reason_str = str(finish_reason)

        # 如果有 name 属性（枚举对象），使用 name
        if hasattr(finish_reason, 'name'):
            finish_reason_str = finish_reason.name

        # 转换为大写用于查找
        finish_reason_upper = finish_reason_str.upper()

        # 查找映射表
        return self.FINISH_REASON_MAPPING.get(finish_reason_upper, "end_turn")

    def _extract_text_content(self, content_obj: Any) -> Optional[str]:
        """
        从响应对象中安全地提取文本内容
        处理各种异常情况（无文本、受阻内容等）

        Args:
            content_obj: 响应对象

        Returns:
            文本内容或 None
        """
        try:
            # 尝试直接访问 text 属性
            if hasattr(content_obj, 'text') and content_obj.text:
                return content_obj.text
        except Exception as e:
            logger.debug(f"Failed to access response.text: {e}")

        # 尝试从 candidates 中提取文本
        try:
            if hasattr(content_obj, 'candidates') and content_obj.candidates:
                candidate = content_obj.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        parts = candidate.content.parts
                        text_parts = []
                        for part in parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            return " ".join(text_parts)
        except Exception as e:
            logger.debug(f"Failed to extract from candidates: {e}")

        return None

    def _safe_create_response(
        self,
        content: List[Dict[str, Any]],
        stop_reason: str,
        usage: Dict[str, int],
        model: str,
        fallback_text: Optional[str] = None
    ) -> ModelResponse:
        """
        安全创建 ModelResponse，确保内容不为空

        Args:
            content: 内容列表
            stop_reason: 停止原因
            usage: 使用统计
            model: 模型名称
            fallback_text: 如果内容为空时使用的回退文本

        Returns:
            ModelResponse 对象
        """
        # 如果内容为空，添加回退文本
        if not content and fallback_text:
            content = [{"type": "text", "text": fallback_text}]

        # 如果仍然为空，添加一个安全的空响应
        if not content:
            content = [{"type": "text", "text": ""}]

        return ModelResponse(
            content=content,
            stop_reason=stop_reason,
            usage=usage or {"input_tokens": 0, "output_tokens": 0},
            model=model
        )

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

    async def create_message_with_cancellation(
        self,
        system: str,
        messages: List[Dict],
        tools: List[Dict],
        max_tokens: int = 8000,
        temperature: float = 1.0,
        stream: bool = False,
        cancellation_token: Optional["CancellationToken"] = None
    ) -> ModelResponse | AsyncIterator[StreamChunk]:
        """Create message with cancellation support

        Uses asyncio.wait() with FIRST_COMPLETED to immediately respond to
        cancellation requests without polling delays.

        Args:
            system: System prompt
            messages: Message history
            tools: Tool definitions
            max_tokens: Maximum output tokens
            temperature: Temperature parameter
            stream: Whether to stream output
            cancellation_token: Cancellation token for interrupt

        Returns:
            ModelResponse or stream iterator

        Raises:
            asyncio.CancelledError: If cancellation_token is cancelled
        """
        if not cancellation_token:
            # No cancellation support, call directly
            return await self.create_message(
                system, messages, tools, max_tokens, temperature, stream
            )

        # Create task for LLM call
        llm_task = asyncio.create_task(
            self.create_message(
                system, messages, tools, max_tokens, temperature, stream
            )
        )

        # Create cancellation monitoring task
        cancel_task = asyncio.create_task(
            cancellation_token.wait()
        )

        try:
            # Wait for whichever completes first
            done, pending = await asyncio.wait(
                [llm_task, cancel_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Check if cancellation happened
            if cancel_task in done:
                # Cancel the LLM task
                llm_task.cancel()

                # Wait for it to actually cancel (with timeout)
                try:
                    await asyncio.wait_for(llm_task, timeout=1.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass

                # Raise cancellation
                raise asyncio.CancelledError(cancellation_token.reason)

            # LLM task completed normally
            cancel_task.cancel()
            return await llm_task

        finally:
            # Cleanup: ensure all tasks are cancelled
            for task in [llm_task, cancel_task]:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
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

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """返回提供商名称 ("anthropic" | "openai" | "kimi")"""
        pass

