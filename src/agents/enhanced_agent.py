"""Enhanced agent with state, context, and tool management"""

from typing import Dict, List, Optional, Callable, TYPE_CHECKING
from datetime import datetime

from ..clients import BaseClient, ModelResponse
from ..tools import TodoManager
from .state import AgentState, AgentStateManager, ToolCall
from .context_manager import AgentContextManager
from .tool_manager import AgentToolManager
from .permission_manager import PermissionManager, PermissionMode
from .feedback import AgentFeedback, FeedbackLevel
from ..hooks import HookManager, HookContextBuilder, HookEvent

if TYPE_CHECKING:
    from ..mcps import MCPClient


class EnhancedAgent:
    """增强的 Agent，支持完整的状态、上下文和工具管理，支持 MCP"""

    def __init__(
        self,
        client: BaseClient,
        system_prompt: str = "",
        max_turns: int = 20,
        max_context_tokens: int = 150000,
        mcp_client: Optional["MCPClient"] = None,
        permission_mode: PermissionMode = PermissionMode.AUTO_APPROVE_SAFE,
        on_state_change: Optional[Callable] = None,
        hook_manager: Optional[HookManager] = None
    ):
        # 核心组件
        self.client = client
        self.mcp_client = mcp_client

        # 管理器
        self.state_manager = AgentStateManager(max_turns=max_turns)
        self.context_manager = AgentContextManager(max_tokens=max_context_tokens)
        self.tool_manager = AgentToolManager(mcp_client=mcp_client)
        self.permission_manager = PermissionManager(mode=permission_mode)
        self.hook_manager = hook_manager or HookManager()

        # 其他组件
        self.todo_manager = TodoManager()
        self._hook_context_builder: Optional[HookContextBuilder] = None

        # 设置系统提示
        if system_prompt:
            self.context_manager.set_system_prompt(system_prompt)

        # 回调
        self.on_state_change = on_state_change

    def _transition_state(self, new_state: AgentState):
        """状态转换，触发回调"""
        old_state = self.state_manager.current_state
        self.state_manager.transition_to(new_state)

        if self.on_state_change:
            self.on_state_change(old_state, new_state)

    async def run(self, user_input: str, verbose: bool = True) -> Dict:
        """
        运行 Agent 处理用户输入

        Args:
            user_input: 用户输入
            verbose: 是否打印详细信息

        Returns:
            执行结果统计
        """
        # 初始化反馈收集器
        feedback_level = FeedbackLevel.MINIMAL if verbose else FeedbackLevel.SILENT
        feedback = AgentFeedback(level=feedback_level)

        # Initialize hook context builder for this run
        self._hook_context_builder = HookContextBuilder()

        # Trigger: on_user_input
        await self.hook_manager.trigger(
            HookEvent.ON_USER_INPUT,
            self._hook_context_builder.build(
                HookEvent.ON_USER_INPUT,
                input=user_input
            )
        )

        # 1. 添加用户消息
        self.context_manager.add_user_message(user_input)

        # 2. 状态：开始思考
        self._transition_state(AgentState.THINKING)
        feedback.add_thinking()

        # Trigger: on_agent_start
        await self.hook_manager.trigger(
            HookEvent.ON_AGENT_START,
            self._hook_context_builder.build(HookEvent.ON_AGENT_START)
        )

        # 3. 压缩上下文（如果需要）
        await self.context_manager.compress_if_needed(self.client)

        # 4. 主循环
        while True:
            # 检查是否超过最大回合数
            if self.state_manager.increment_turn():
                if verbose:
                    print("\n⚠️ Reached maximum turn limit")
                self._transition_state(AgentState.ERROR)
                break

            try:
                # 5. 调用 LLM
                response = await self._call_llm()

                # 6. 更新 token 统计
                self.state_manager.add_tokens(
                    response.usage.get("input_tokens", 0),
                    response.usage.get("output_tokens", 0)
                )

                # 7. 解析响应
                text_blocks, tool_uses = self._parse_response(response)

                # 8. 暂存文本（不在循环中打印）
                final_response = ""
                if text_blocks:
                    final_response = text_blocks[0]

                # 9. 如果没有工具调用，完成
                if not tool_uses:
                    self.context_manager.add_assistant_message(response.content)
                    self._transition_state(AgentState.COMPLETED)

                    # Trigger: on_agent_end
                    await self.hook_manager.trigger(
                        HookEvent.ON_AGENT_END,
                        self._hook_context_builder.build(
                            HookEvent.ON_AGENT_END,
                            success=True
                        )
                    )

                    # 返回结构化数据给main.py，由main.py统一输出
                    return {
                        "final_response": final_response,
                        "feedback": feedback.get_all(),
                        "agent_state": self.state_manager.get_statistics(),
                        "context": self.context_manager.get_context_info(),
                    }

                # 10. 执行工具
                self._transition_state(AgentState.USING_TOOL)
                tool_results = await self._execute_tools(tool_uses, verbose, feedback)

                # 11. 添加消息到上下文
                self.context_manager.add_assistant_message(response.content)
                self.context_manager.add_tool_results(tool_results)

                # 12. 继续下一轮
                self._transition_state(AgentState.THINKING)

            except Exception as e:
                if verbose:
                    print(f"\n❌ Error: {str(e)}")
                self._transition_state(AgentState.ERROR)

                # Trigger: on_error
                await self.hook_manager.trigger(
                    HookEvent.ON_ERROR,
                    self._hook_context_builder.build(
                        HookEvent.ON_ERROR,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                )
                break

        # Trigger: on_shutdown
        await self.hook_manager.trigger(
            HookEvent.ON_SHUTDOWN,
            self._hook_context_builder.build(
                HookEvent.ON_SHUTDOWN,
                final_state=self.state_manager.current_state.value
            )
        )

        # 返回统计信息（包含反馈）
        return {
            "final_response": "",
            "feedback": feedback.get_all(),
            "agent_state": self.state_manager.get_statistics(),
            "context": self.context_manager.get_context_info(),
        }

    async def _call_llm(self) -> ModelResponse:
        """调用 LLM"""
        # Trigger: on_thinking
        await self.hook_manager.trigger(
            HookEvent.ON_THINKING,
            self._hook_context_builder.build(
                HookEvent.ON_THINKING,
                message_count=len(self.context_manager.get_messages()),
                tool_count=len(self.tool_manager.get_tool_definitions())
            )
        )

        return await self.client.create_message(
            system=self.context_manager.system_prompt,
            messages=self.context_manager.get_messages(),
            tools=self.tool_manager.get_tool_definitions(),
            max_tokens=8000,
            stream=False
        )

    def _parse_response(self, response: ModelResponse) -> tuple[List[str], List[Dict]]:
        """解析 LLM 响应"""
        text_blocks = []
        tool_uses = []

        for block in response.content:
            if block.get("type") == "text":
                text_blocks.append(block["text"])
            elif block.get("type") == "tool_use":
                tool_uses.append(block)

        return text_blocks, tool_uses

    def _generate_brief_description(self, tool_name: str, tool_input: Dict) -> str:
        """生成工具调用的简短描述用于反馈"""
        if not isinstance(tool_input, dict):
            return str(tool_input)[:50]

        # 为常见工具生成简洁描述
        if tool_name == "Bash":
            command = tool_input.get("command", "")[:40]
            return f"execute: {command}"
        elif tool_name == "Read":
            file_path = tool_input.get("file_path", "")
            return f"read: {file_path}"
        elif tool_name == "Write":
            file_path = tool_input.get("file_path", "")
            return f"write: {file_path}"
        elif tool_name == "Edit":
            file_path = tool_input.get("file_path", "")
            return f"edit: {file_path}"
        elif tool_name == "Glob":
            pattern = tool_input.get("pattern", "")[:40]
            return f"search: {pattern}"
        elif tool_name == "Grep":
            pattern = tool_input.get("pattern", "")[:40]
            return f"grep: {pattern}"
        elif tool_name == "TodoWrite":
            return "update todos"
        else:
            # 通用描述
            first_key = next(iter(tool_input.keys())) if tool_input else "?"
            first_val = str(tool_input.get(first_key, ""))[:30]
            return f"{first_key}: {first_val}"

    async def _execute_tools(self, tool_uses: List[Dict], verbose: bool = True, feedback: "AgentFeedback" = None) -> List[Dict]:
        """执行工具调用"""
        tool_results = []

        for tool_use in tool_uses:
            tool_name = tool_use["name"]
            tool_input = tool_use["input"]
            tool_id = tool_use["id"]

            # 记录工具调用
            tool_call = ToolCall(
                id=tool_id,
                name=tool_name,
                input=tool_input
            )
            self.state_manager.record_tool_call(tool_call)

            # 生成简短描述用于反馈
            brief_description = self._generate_brief_description(tool_name, tool_input)

            # 添加工具调用反馈
            if feedback:
                feedback.add_tool_call(tool_name, brief_description)

            # Trigger: on_tool_select
            await self.hook_manager.trigger(
                HookEvent.ON_TOOL_SELECT,
                self._hook_context_builder.build(
                    HookEvent.ON_TOOL_SELECT,
                    tool_name=tool_name,
                    tool_id=tool_id
                )
            )

            # 🔐 权限检查
            tool = self.tool_manager.get_tool(tool_name)
            if tool:
                # Trigger: on_permission_check
                await self.hook_manager.trigger(
                    HookEvent.ON_PERMISSION_CHECK,
                    self._hook_context_builder.build(
                        HookEvent.ON_PERMISSION_CHECK,
                        tool_name=tool_name,
                        tool_input=tool_input
                    )
                )

                is_approved, deny_message = await self.permission_manager.request_permission(
                    tool, tool_input
                )

                if not is_approved:
                    # 权限被拒绝
                    self.state_manager.update_tool_call_result(
                        tool_id,
                        result=None,
                        error=deny_message
                    )
                    # 添加权限拒绝反馈
                    if feedback:
                        feedback.add_error(f"Permission denied: {deny_message}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": f"Permission denied: {deny_message}",
                        "is_error": True
                    })
                    continue

            if verbose:
                print(f"\n[Using tool: {tool_name}]", flush=True)

            # Trigger: on_tool_execute
            await self.hook_manager.trigger(
                HookEvent.ON_TOOL_EXECUTE,
                self._hook_context_builder.build(
                    HookEvent.ON_TOOL_EXECUTE,
                    tool_name=tool_name,
                    tool_id=tool_id,
                    tool_input=tool_input
                )
            )

            # 执行工具
            result = await self.tool_manager.execute_tool(tool_name, tool_input)

            # 更新工具调用结果
            self.state_manager.update_tool_call_result(
                tool_id,
                result=result if result.success else None,
                error=result.error
            )

            # Trigger: on_tool_result or on_tool_error
            if result.success:
                await self.hook_manager.trigger(
                    HookEvent.ON_TOOL_RESULT,
                    self._hook_context_builder.build(
                        HookEvent.ON_TOOL_RESULT,
                        tool_name=tool_name,
                        tool_id=tool_id,
                        result=result.output
                    )
                )
                # 添加工具完成反馈
                if feedback:
                    feedback.add_tool_completed(tool_name)
            else:
                await self.hook_manager.trigger(
                    HookEvent.ON_TOOL_ERROR,
                    self._hook_context_builder.build(
                        HookEvent.ON_TOOL_ERROR,
                        tool_name=tool_name,
                        tool_id=tool_id,
                        error=result.error
                    )
                )
                # 添加工具错误反馈
                if feedback:
                    feedback.add_error(f"{tool_name}: {result.error}")

            # 特殊处理：TodoWrite 更新本地状态
            if tool_name == "TodoWrite" and result.success:
                self.todo_manager.update(tool_input.get("todos", []))

            # 构造工具结果
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": result.output if result.success else result.error,
                "is_error": not result.success
            })

        return tool_results

    def get_statistics(self) -> Dict:
        """获取完整统计信息"""
        return {
            "agent_state": self.state_manager.get_statistics(),
            "context": self.context_manager.get_context_info(),
            "tool_usage": self.tool_manager.get_usage_statistics(),
            "todos": {
                "total": len(self.todo_manager.get_all()),
                "pending": sum(1 for t in self.todo_manager.get_all() if t["status"] == "pending"),
                "in_progress": sum(1 for t in self.todo_manager.get_all() if t["status"] == "in_progress"),
                "completed": sum(1 for t in self.todo_manager.get_all() if t["status"] == "completed"),
            }
        }

    def reset(self):
        """重置 Agent 状态"""
        self.state_manager.reset()
        self.context_manager.clear()
        self.tool_manager.reset_statistics()
        self.todo_manager.clear()

    # 便捷方法
    def get_current_state(self) -> AgentState:
        """获取当前状态"""
        return self.state_manager.current_state

    def get_todos(self) -> List[Dict]:
        """获取 todos"""
        return self.todo_manager.get_all()

    def get_message_count(self) -> int:
        """获取消息数量"""
        return len(self.context_manager.messages)
