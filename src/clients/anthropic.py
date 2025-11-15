"""Anthropic Claude client implementation"""

import anthropic
from typing import List, Dict, AsyncIterator
from .base import BaseClient, ModelResponse, StreamChunk


class AnthropicClient(BaseClient):
    """Anthropic Claude 客户端实现"""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
        api_base: str = None,
        temperature: float = None,
        max_tokens: int = None
    ):
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key,
            base_url=api_base
        )
        self.model = model
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens

    async def create_message(
        self,
        system: str,
        messages: List[Dict],
        tools: List[Dict],
        max_tokens: int = 8000,
        temperature: float = 1.0,
        stream: bool = False
    ) -> ModelResponse | AsyncIterator[StreamChunk]:

        # 使用配置的默认值（如果提供了）
        actual_max_tokens = self.default_max_tokens or max_tokens
        actual_temperature = self.default_temperature if self.default_temperature is not None else temperature

        response = await self.client.messages.create(
            model=self.model,
            system=system,
            messages=messages,
            tools=tools,
            max_tokens=actual_max_tokens,
            temperature=actual_temperature,
            stream=stream
        )

        if stream:
            return self._stream_response(response)

        # 转换为统一格式
        content = []
        for block in response.content:
            if block.type == "text":
                content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })

        return ModelResponse(
            content=content,
            stop_reason=response.stop_reason,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            },
            model=response.model
        )

    async def _stream_response(self, stream) -> AsyncIterator[StreamChunk]:
        """处理流式响应"""
        async for event in stream:
            if event.type == "content_block_start":
                if event.content_block.type == "text":
                    yield StreamChunk("text", "")
                elif event.content_block.type == "tool_use":
                    yield StreamChunk("tool_use_start", event.content_block)

            elif event.type == "content_block_delta":
                if hasattr(event.delta, "text"):
                    yield StreamChunk("text", event.delta.text)

    async def generate_summary(self, prompt: str) -> str:
        """生成摘要"""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0.5,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def context_window(self) -> int:
        return 200000  # Claude 3.5 Sonnet

    @property
    def provider_name(self) -> str:
        return "anthropic"

