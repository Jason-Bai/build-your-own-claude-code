"""Google Gemini client implementation"""

from typing import List, Dict, AsyncIterator
from .base import BaseClient, ModelResponse, StreamChunk

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


class GoogleClient(BaseClient):
    """Google Gemini 客户端实现"""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        api_base: str = None,
        temperature: float = None,
        max_tokens: int = None
    ):
        if not GOOGLE_AVAILABLE:
            raise ImportError(
                "Google AI package not installed. Install with: pip install google-generativeai"
            )

        genai.configure(api_key=api_key)

        # 确保模型名称格式正确
        if not model.startswith("models/"):
            model = f"models/{model}"

        self.model_name_str = model.replace("models/", "")
        self.model = genai.GenerativeModel(model)
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

        # 转换消息格式为 Google Gemini 格式
        gemini_messages = []

        # 添加系统提示（作为用户消息的一部分）
        if system:
            gemini_messages.append({"role": "user", "parts": [system]})
            gemini_messages.append({"role": "model", "parts": ["Understood. I will follow these instructions."]})

        # 转换消息历史
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            # 转换角色
            gemini_role = "user" if role == "user" else "model"

            # 处理不同的内容格式
            if isinstance(content, str):
                gemini_messages.append({
                    "role": gemini_role,
                    "parts": [content]
                })
            elif isinstance(content, list):
                parts = []
                for block in content:
                    if block.get("type") == "text":
                        parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_result":
                        # 包含工具结果
                        parts.append(f"Tool result: {block.get('content', '')}")

                if parts:
                    gemini_messages.append({
                        "role": gemini_role,
                        "parts": parts
                    })

        # Google Gemini 目前不完全支持工具调用，所以我们使用文本生成
        # 创建生成配置
        generation_config = {
            "temperature": actual_temperature,
            "max_output_tokens": actual_max_tokens,
        }

        # 发送请求
        try:
            response = await self.model.generate_content_async(
                gemini_messages,
                generation_config=genai.types.GenerationConfig(**generation_config),
                stream=stream
            )
        except Exception as e:
            # 处理请求失败的情况
            return ModelResponse(
                content=[{"type": "text", "text": f"Error: {str(e)}"}],
                stop_reason="error",
                usage={"input_tokens": 0, "output_tokens": 0},
                model=self.model_name_str
            )

        if stream:
            return self._stream_response(response)

        # 转换为统一格式
        content = []

        # 安全地访问响应文本（处理可能没有有效文本的情况）
        try:
            if response.text:
                content.append({"type": "text", "text": response.text})
            elif response.candidates and len(response.candidates) > 0:
                # 如果没有 text，尝试从候选项构建内容
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            content.append({"type": "text", "text": part.text})
        except Exception as e:
            # 如果访问失败，记录错误但继续
            content.append({"type": "text", "text": f"Warning: Could not extract response text: {str(e)}"})

        # 获取 finish_reason（安全处理）
        finish_reason = "end_turn"
        if response.candidates and len(response.candidates) > 0:
            try:
                finish_reason_value = response.candidates[0].finish_reason
                if finish_reason_value:
                    # 处理整数类型的 finish_reason
                    if isinstance(finish_reason_value, int):
                        finish_reason = self._convert_finish_reason(str(finish_reason_value))
                    else:
                        finish_reason = self._convert_finish_reason(finish_reason_value.name if hasattr(finish_reason_value, 'name') else str(finish_reason_value))
            except Exception:
                finish_reason = "end_turn"

        # 注意：Google Gemini 的免费版本不支持工具调用
        # 所以这里我们只返回文本内容

        return ModelResponse(
            content=content,
            stop_reason=finish_reason,
            usage={
                "input_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                "output_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0
            },
            model=self.model_name_str
        )

    def _convert_finish_reason(self, finish_reason: str) -> str:
        """转换 Google 的 finish_reason 到 Anthropic 格式"""
        mapping = {
            "STOP": "end_turn",
            "MAX_TOKENS": "max_tokens",
            "SAFETY": "stop_sequence",
            "RECITATION": "stop_sequence",
            "0": "end_turn",      # FINISH_REASON_UNSPECIFIED
            "1": "end_turn",      # STOP
            "2": "max_tokens",    # MAX_TOKENS
            "3": "stop_sequence", # SAFETY
            "4": "stop_sequence", # RECITATION
            "5": "stop_sequence", # OTHER
        }
        return mapping.get(str(finish_reason), "end_turn")

    async def _stream_response(self, stream) -> AsyncIterator[StreamChunk]:
        """处理流式响应"""
        async for chunk in stream:
            if chunk.text:
                yield StreamChunk("text", chunk.text)

    async def generate_summary(self, prompt: str) -> str:
        """生成摘要"""
        response = await self.model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,
                max_output_tokens=500
            )
        )

        return response.text or ""

    @property
    def model_name(self) -> str:
        return self.model_name_str

    @property
    def context_window(self) -> int:
        # Google Gemini 的上下文窗口
        if "1.5" in self.model_name_str:
            return 1000000  # Gemini 1.5 支持 1M tokens
        elif "1.0" in self.model_name_str:
            return 32000  # Gemini 1.0 / Pro
        else:
            return 100000  # 默认值
