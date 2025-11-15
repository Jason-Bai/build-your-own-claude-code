"""Context manager for agent conversations"""

import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from ..clients import BaseClient
from ..prompts import get_summarization_prompt


class Message(BaseModel):
    """消息模型"""
    role: str  # "user" | "assistant"
    content: List[Dict[str, Any]]  # text blocks or tool_use/tool_result


class AgentContextManager:
    """Agent 上下文管理器"""

    def __init__(self, max_tokens: int = 150000):
        self.messages: List[Message] = []
        self.system_prompt: str = ""
        self.max_tokens = max_tokens
        self.summary: str = ""  # 历史摘要
        self.metadata: Dict[str, Any] = {}  # 额外元数据

    def set_system_prompt(self, prompt: str):
        """设置系统提示"""
        self.system_prompt = prompt

    def add_user_message(self, text: str):
        """添加用户消息"""
        self.messages.append(Message(
            role="user",
            content=[{"type": "text", "text": text}]
        ))

    def add_assistant_message(self, content: List[Dict]):
        """添加助手消息"""
        self.messages.append(Message(
            role="assistant",
            content=content
        ))

    def add_tool_results(self, tool_results: List[Dict], provider: str = "anthropic"):
        """
        添加工具结果（支持不同提供商的格式差异）

        对于 Kimi/OpenAI，工具结果需要转换为标准格式，其中：
        - tool_use_id 转换为 tool_call_id（OpenAI/Kimi 期望的格式）
        - 必须作为 role="user" 消息添加（不是 role="tool"）

        Args:
            tool_results: 工具结果列表（Anthropic 格式）
            provider: 提供商名称 ("anthropic" | "openai" | "kimi")
        """
        if not tool_results:
            return

        # 根据提供商转换消息格式
        if provider in ["openai", "kimi"]:
            # OpenAI/Kimi 格式：转换 tool_use_id 为 tool_call_id
            converted = []
            for result in tool_results:
                # 获取 tool_call_id，确保不为 None/空
                tool_call_id = result.get("tool_use_id") or result.get("tool_call_id")

                converted_result = {
                    "type": "tool_result",
                    "content": result.get("content", "")
                }

                # 只有在 tool_call_id 不为空时才添加
                if tool_call_id:
                    converted_result["tool_call_id"] = tool_call_id

                converted.append(converted_result)

            # 工具结果作为用户消息添加
            self.messages.append(Message(
                role="user",
                content=converted
            ))
        else:
            # Anthropic 格式（保持原样）
            self.messages.append(Message(
                role="user",
                content=tool_results
            ))

    def get_messages(self) -> List[Dict]:
        """获取消息列表（API 格式）"""
        return [msg.model_dump() for msg in self.messages]

    def get_last_message(self) -> Optional[Message]:
        """获取最后一条消息"""
        return self.messages[-1] if self.messages else None

    def estimate_tokens(self) -> int:
        """估算 token 使用（粗略）"""
        total_chars = len(self.system_prompt)
        total_chars += len(self.summary)

        for msg in self.messages:
            total_chars += len(json.dumps(msg.model_dump()))

        # 1 token ≈ 3 chars (保守估计)
        return total_chars // 3

    async def compress_if_needed(self, client: BaseClient):
        """如果超过限制，压缩上下文"""
        if self.estimate_tokens() < self.max_tokens:
            return

        # 策略：保留最近 N 条消息，其余生成摘要
        messages_to_keep = 10

        if len(self.messages) <= messages_to_keep:
            # 消息不多但很长，只能删除
            self.messages = self.messages[-messages_to_keep:]
            return

        # 生成摘要
        old_messages = self.messages[:-messages_to_keep]
        recent_messages = self.messages[-messages_to_keep:]

        # 使用统一的摘要 prompt
        formatted_messages = self._format_messages_for_summary(old_messages)
        summary_prompt = get_summarization_prompt(
            formatted_messages,
            self.summary
        )

        new_summary = await client.generate_summary(summary_prompt)
        self.summary = new_summary
        self.messages = recent_messages

    def _format_messages_for_summary(self, messages: List[Message]) -> str:
        """格式化消息用于摘要"""
        formatted = []
        for msg in messages:
            role = msg.role
            text_parts = [
                block.get("text", "")
                for block in msg.content
                if block.get("type") == "text"
            ]
            if text_parts:
                formatted.append(f"{role}: {' '.join(text_parts)[:200]}")
        return "\n".join(formatted)

    def clear(self):
        """清空上下文"""
        self.messages.clear()
        self.summary = ""
        self.metadata.clear()

    def get_context_info(self) -> Dict[str, Any]:
        """获取上下文信息"""
        return {
            "message_count": len(self.messages),
            "estimated_tokens": self.estimate_tokens(),
            "max_tokens": self.max_tokens,
            "usage_percentage": (self.estimate_tokens() / self.max_tokens * 100) if self.max_tokens > 0 else 0,
            "has_summary": bool(self.summary),
            "summary_length": len(self.summary)
        }

    def set_metadata(self, key: str, value: Any):
        """设置元数据"""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self.metadata.get(key, default)
