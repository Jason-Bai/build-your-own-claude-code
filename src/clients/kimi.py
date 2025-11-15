"""Kimi client implementation (OpenAI-compatible)"""

from typing import List, Dict, AsyncIterator
from .base import ModelResponse, StreamChunk
from .openai import OpenAIClient


class KimiClient(OpenAIClient):
    """Kimi客户端 - 继承OpenAI但处理Kimi特定的API差异"""

    def __init__(
        self,
        api_key: str,
        model: str = "kimi-k2-thinking",
        api_base: str = "https://api.moonshot.cn/v1",
        temperature: float = None,
        max_tokens: int = None
    ):
        """
        初始化Kimi客户端

        Args:
            api_key: Kimi API密钥
            model: 模型名称，默认为kimi-k2-thinking
            api_base: Kimi API基础URL，默认为官方地址
            temperature: 温度参数
            max_tokens: 最大token数
        """
        # 确保使用Kimi的API基础URL
        if api_base is None:
            api_base = "https://api.moonshot.cn/v1"

        super().__init__(
            api_key=api_key,
            model=model,
            api_base=api_base,
            temperature=temperature,
            max_tokens=max_tokens
        )

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
        创建消息（处理Kimi特定的差异）

        Kimi作为OpenAI兼容API，大部分逻辑复用OpenAI实现
        但需要处理tool_use_id的特殊情况

        重要：Kimi期望tool_result消息中使用tool_use_id而不是tool_call_id
        """

        # 规范化消息：处理Kimi对tool_use_id的特殊处理
        normalized_messages = self._normalize_messages_for_kimi(messages)

        # 直接实现消息处理，避免OpenAI客户端将tool_use_id转换为tool_call_id
        return await self._create_message_with_kimi_formatting(
            system=system,
            messages=normalized_messages,
            tools=tools,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=stream
        )

    async def _create_message_with_kimi_formatting(
        self,
        system: str,
        messages: List[Dict],
        tools: List[Dict],
        max_tokens: int = 8000,
        temperature: float = 1.0,
        stream: bool = False
    ) -> ModelResponse | AsyncIterator[StreamChunk]:
        """
        直接实现Kimi的消息发送，避免OpenAI客户端将tool_use_id转换为tool_call_id
        """
        import json
        from .base import ModelResponse

        # 使用配置的默认值（如果提供了）
        actual_max_tokens = self.default_max_tokens or max_tokens
        actual_temperature = self.default_temperature if self.default_temperature is not None else temperature

        # 为Kimi构建消息列表（保持tool_use_id）
        openai_messages = [{"role": "system", "content": system}]

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if isinstance(content, str):
                openai_messages.append({"role": role, "content": content})
            elif isinstance(content, list):
                if role == "user":
                    # 处理user消息中的tool_result（对于Kimi使用tool_use_id）
                    for block in content:
                        if block.get("type") == "text":
                            openai_messages.append({
                                "role": role,
                                "content": block.get("text", "")
                            })
                        elif block.get("type") == "tool_result":
                            # 对于Kimi，使用tool_call_id在一个单独的tool消息中
                            tool_use_id = block.get("tool_use_id", "")
                            openai_messages.append({
                                "role": "tool",
                                "tool_call_id": tool_use_id,
                                "content": block.get("content", "")
                            })
                elif role == "assistant":
                    # 处理assistant消息中的tool_use
                    assistant_msg = {"role": "assistant"}
                    text_content = ""
                    tool_calls = []

                    for block in content:
                        if block.get("type") == "text":
                            text_content += block.get("text", "")
                        elif block.get("type") == "tool_use":
                            tool_calls.append({
                                "id": block.get("id"),
                                "type": "function",
                                "function": {
                                    "name": block.get("name"),
                                    "arguments": json.dumps(block.get("input", {}))
                                }
                            })

                    if text_content:
                        assistant_msg["content"] = text_content
                    else:
                        assistant_msg["content"] = ""

                    if tool_calls:
                        assistant_msg["tool_calls"] = tool_calls

                    openai_messages.append(assistant_msg)

        # 转换工具格式
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

        # 调用 Kimi API
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
                content.append({
                    "type": "tool_use",
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "input": eval(tool_call.function.arguments)  # JSON string -> dict
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
        """转换 finish_reason 到 Anthropic 格式"""
        mapping = {
            "stop": "end_turn",
            "length": "max_tokens",
            "tool_calls": "tool_use",
            "content_filter": "stop_sequence"
        }
        return mapping.get(finish_reason, finish_reason)

    def _normalize_messages_for_kimi(self, messages: List[Dict]) -> List[Dict]:
        """
        为Kimi规范化消息格式

        处理tool_use_id可能为空或格式不同的情况
        确保tool_result消息中的tool_call_id正确传递
        """
        normalized = []

        for msg in messages:
            if msg.get("role") == "assistant" and isinstance(msg.get("content"), list):
                # 处理assistant消息中可能包含的tool_use块
                new_msg = {
                    "role": msg["role"],
                    "content": []
                }

                for block in msg["content"]:
                    if block.get("type") == "tool_use":
                        # 保留tool_use块，确保id字段存在
                        tool_use_block = {
                            "type": "tool_use",
                            "id": block.get("id", ""),
                            "name": block.get("name", ""),
                            "input": block.get("input", {})
                        }
                        new_msg["content"].append(tool_use_block)
                    elif block.get("type") == "text":
                        # 保留文本块
                        new_msg["content"].append({
                            "type": "text",
                            "text": block.get("text", "")
                        })

                if new_msg["content"]:
                    normalized.append(new_msg)

            elif msg.get("role") == "user" and isinstance(msg.get("content"), list):
                # 处理user消息中的tool_result
                new_msg = {
                    "role": msg["role"],
                    "content": []
                }

                for block in msg["content"]:
                    if block.get("type") == "tool_result":
                        # 确保tool_use_id存在，这是Kimi期望的字段
                        # 从tool_call_id或tool_use_id中获取，优先使用tool_call_id（由Anthropic格式转换过来的）
                        tool_id = block.get("tool_call_id") or block.get("tool_use_id") or block.get("id", "")
                        tool_result_block = {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": block.get("content", "")
                        }
                        new_msg["content"].append(tool_result_block)
                    elif block.get("type") == "text":
                        new_msg["content"].append({
                            "type": "text",
                            "text": block.get("text", "")
                        })

                if new_msg["content"]:
                    normalized.append(new_msg)

            else:
                # 其他消息直接传递
                normalized.append(msg)

        return normalized if normalized else messages

    @property
    def context_window(self) -> int:
        """
        返回Kimi的上下文窗口大小

        Kimi的上下文窗口取决于具体模型：
        - kimi-k2-thinking: 200,000 tokens
        - 其他kimi模型: 通常也很大
        """
        if "thinking" in self.model.lower():
            return 200000  # kimi-k2-thinking context window
        else:
            return 128000  # 其他Kimi模型默认值

    @property
    def provider_name(self) -> str:
        return "kimi"
