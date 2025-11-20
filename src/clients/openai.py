"""OpenAI client implementation"""

from typing import List, Dict, AsyncIterator
from .base import BaseClient, ModelResponse, StreamChunk

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIClient(BaseClient):
    """OpenAI 客户端实现"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        api_base: str = None,
        temperature: float = None,
        max_tokens: int = None
    ):
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install openai"
            )

        self.client = AsyncOpenAI(
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

        # 转换消息格式：Anthropic -> OpenAI
        openai_messages = [{"role": "system", "content": system}]

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            # 处理不同的内容格式
            if isinstance(content, str):
                openai_messages.append({"role": role, "content": content})
            elif isinstance(content, list):
                # 处理包含 tool_result 的情况
                for block in content:
                    if block.get("type") == "text":
                        openai_messages.append({
                            "role": role,
                            "content": block.get("text", "")
                        })
                    elif block.get("type") == "tool_result":
                        # OpenAI 格式的工具结果
                        openai_messages.append({
                            "role": "tool",
                            "tool_call_id": block.get("tool_use_id"),
                            "content": block.get("content", "")
                        })

        # 转换工具格式：Anthropic -> OpenAI
        openai_tools = []
        if tools:
            for tool in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("input_schema", {})
                    }
                })

        # 调用 OpenAI API
        kwargs = {
            "model": self.model,
            "messages": openai_messages,
            "max_tokens": actual_max_tokens,
            "temperature": actual_temperature,
            "stream": stream
        }

        if openai_tools:
            kwargs["tools"] = openai_tools

        response = await self.client.chat.completions.create(**kwargs)

        if stream:
            return self._stream_response(response)

        # 转换为统一格式：OpenAI -> Anthropic
        content = []

        message = response.choices[0].message

        # 文本内容
        if message.content:
            content.append({"type": "text", "text": message.content})

        # 工具调用
        if message.tool_calls:
            for tool_call in message.tool_calls:
                # 安全地解析JSON参数（避免eval的安全风险和true/false/null问题）
                try:
                    tool_input = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    # 如果JSON解析失败，尝试作为空对象
                    tool_input = {}

                content.append({
                    "type": "tool_use",
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "input": tool_input
                })

        return ModelResponse(
            content=content,
            stop_reason=self._convert_finish_reason(response.choices[0].finish_reason),
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens
            },
            model=response.model
        )

    def _convert_finish_reason(self, finish_reason: str) -> str:
        """转换 OpenAI finish_reason 到 Anthropic 格式"""
        mapping = {
            "stop": "end_turn",
            "length": "max_tokens",
            "tool_calls": "tool_use",
            "content_filter": "stop_sequence"
        }
        return mapping.get(finish_reason, finish_reason)

    async def _stream_response(self, stream) -> AsyncIterator[StreamChunk]:
        """处理流式响应"""
        async for chunk in stream:
            delta = chunk.choices[0].delta

            if delta.content:
                yield StreamChunk("text", delta.content)

            if delta.tool_calls:
                for tool_call in delta.tool_calls:
                    yield StreamChunk("tool_use_start", tool_call)

    async def generate_summary(self, prompt: str) -> str:
        """生成摘要"""
        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=500,
            temperature=0.5,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def context_window(self) -> int:
        # 根据模型返回不同的上下文窗口
        if "gpt-4" in self.model.lower():
            if "turbo" in self.model.lower() or "gpt-4o" in self.model.lower():
                return 128000  # GPT-4 Turbo / GPT-4o
            else:
                return 8192    # GPT-4
        elif "gpt-3.5" in self.model.lower():
            if "16k" in self.model.lower():
                return 16384   # GPT-3.5 Turbo 16K
            else:
                return 4096    # GPT-3.5 Turbo
        else:
            return 8192  # 默认

    @property
    def provider_name(self) -> str:
        """返回提供商名称"""
        return "openai"
