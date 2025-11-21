"Enhanced agent with state, context, and tool management"

import uuid
from pathlib import Path
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
from ..events import EventBus, EventType, Event, get_event_bus

# P6 Imports
from ..persistence.manager import PersistenceManager
from ..persistence.storage import JSONStorage
from ..checkpoint.manager import CheckpointManager
from ..checkpoint.recovery import ExecutionRecovery
from ..checkpoint.tracker import ExecutionTracker
from ..checkpoint.types import Checkpoint, ExecutionResult

# P11 Imports - Logging
from ..logging import get_action_logger
from ..logging.types import ActionType

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
        hook_manager: Optional[HookManager] = None,
        persistence_manager: Optional[PersistenceManager] = None
    ):
        # 核心组件
        self.client = client
        self.mcp_client = mcp_client
        self.event_bus = get_event_bus()

        # 管理器
        self.state_manager = AgentStateManager(max_turns=max_turns)
        self.context_manager = AgentContextManager(max_tokens=max_context_tokens)
        self.tool_manager = AgentToolManager(mcp_client=mcp_client)
        self.permission_manager = PermissionManager(mode=permission_mode)
        self.hook_manager = hook_manager or HookManager()

        # P6: Persistence and Checkpoint System
        self.persistence = persistence_manager or PersistenceManager(self._get_configured_storage())
        self.checkpoint_manager = CheckpointManager(self.persistence)
        self.execution_tracker = ExecutionTracker(self.persistence)
        self.execution_recovery = ExecutionRecovery(self.checkpoint_manager, self.persistence)

        # 其他组件
        self.todo_manager = TodoManager()
        self._hook_context_builder: Optional[HookContextBuilder] = None

        # P11: Action Logger
        self.action_logger = get_action_logger()

        # 设置系统提示
        if system_prompt:
            self.context_manager.set_system_prompt(system_prompt)

        # 回调
        self.on_state_change = on_state_change

    def _get_configured_storage(self):
        project_name = Path.cwd().name
        return JSONStorage(project_name)

    def restore_state_from_checkpoint(self, checkpoint: Checkpoint):
        """Restores the agent's internal state and context from a checkpoint."""
        # This is a simplified restoration. A real implementation might need more logic.
        if checkpoint.state:
            self.state_manager.restore_state(checkpoint.state)
        if checkpoint.context:
            self.context_manager.restore_context(checkpoint.context)

    async def _transition_state(self, new_state: AgentState):
        """状态转换，触发回调"""
        old_state = self.state_manager.current_state
        self.state_manager.transition_to(new_state)

        # P11: Log state change
        self.action_logger.log(
            action_type=ActionType.AGENT_STATE_CHANGE,
            from_state=old_state.value,
            to_state=new_state.value,
            reason="user_request"
        )

        # Emit state change event for UI
        await self.event_bus.emit(Event(
            EventType.AGENT_STATE_CHANGED,
            state=new_state,
            old_state=old_state
        ))

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
        execution_id = str(uuid.uuid4())
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL if verbose else FeedbackLevel.SILENT)
        self._hook_context_builder = HookContextBuilder()

        await self.hook_manager.trigger(
            HookEvent.ON_USER_INPUT,
            self._hook_context_builder.build(HookEvent.ON_USER_INPUT, input=user_input)
        )
        await self.event_bus.emit(Event(EventType.AGENT_START, user_input=user_input))

        self.context_manager.add_user_message(user_input)
        await self._transition_state(AgentState.THINKING)
        feedback.add_thinking()

        await self.event_bus.emit(Event(EventType.AGENT_THINKING, turn=self.state_manager.current_turn))
        await self.hook_manager.trigger(
            HookEvent.ON_AGENT_START,
            self._hook_context_builder.build(HookEvent.ON_AGENT_START)
        )

        await self.execution_tracker.track_step(
            execution_id=execution_id, step_name="Agent Start", step_index=0, status="success",
            result={"user_input": user_input}
        )

        await self.context_manager.compress_if_needed(self.client)

        while True:
            if self.state_manager.increment_turn():
                if verbose: print("\n⚠️ Reached maximum turn limit")
                await self._transition_state(AgentState.ERROR)
                break

            try:
                response = await self._call_llm()
                # 安全地提取 token 使用量
                usage = response.usage or {}
                self.state_manager.add_tokens(
                    usage.get("input_tokens", 0), usage.get("output_tokens", 0)
                )
                text_blocks, tool_uses = self._parse_response(response)
                final_response = text_blocks[0] if text_blocks else ""

                current_state_data = self.state_manager.get_statistics()
                current_context_info = self.context_manager.get_context_info()
                
                await self.checkpoint_manager.create_checkpoint(
                    execution_id=execution_id, step_name=f"LLM Call Turn {self.state_manager.current_turn}",
                    step_index=self.state_manager.current_turn, state=current_state_data,
                    context=current_context_info, variables={}
                )
                await self.execution_tracker.track_step(
                    execution_id=execution_id, step_name=f"LLM Call Turn {self.state_manager.current_turn}",
                    step_index=self.state_manager.current_turn, status="success"
                )

                if not tool_uses:
                    self.context_manager.add_assistant_message(response.content)
                    await self._transition_state(AgentState.COMPLETED)
                    await self.event_bus.emit(Event(
                        EventType.AGENT_END, success=True, final_response=final_response,
                        turn=self.state_manager.current_turn
                    ))
                    await self.hook_manager.trigger(
                        HookEvent.ON_AGENT_END,
                        self._hook_context_builder.build(HookEvent.ON_AGENT_END, success=True)
                    )
                    await self.execution_tracker.track_step(
                        execution_id=execution_id, step_name="Agent End",
                        step_index=self.state_manager.current_turn + 1, status="success",
                        result={"final_response": final_response}
                    )
                    return {
                        "final_response": final_response, "feedback": feedback.get_all(),
                        "agent_state": self.state_manager.get_statistics(),
                        "context": self.context_manager.get_context_info(),
                    }

                await self._transition_state(AgentState.USING_TOOL)
                tool_results = await self._execute_tools(tool_uses, verbose, feedback)
                self.context_manager.add_assistant_message(response.content)
                self.context_manager.add_tool_results(tool_results, provider=self.client.provider_name)

                await self.execution_tracker.track_step(
                    execution_id=execution_id, step_name=f"Tool Execution Turn {self.state_manager.current_turn}",
                    step_index=self.state_manager.current_turn + 0.5, status="success",
                    result={"tool_results": tool_results}
                )

                await self._transition_state(AgentState.THINKING)
                await self.event_bus.emit(Event(EventType.AGENT_THINKING, turn=self.state_manager.current_turn + 1))

            except Exception as e:
                if verbose: print(f"\n❌ Error: {str(e)}")
                
                await self.execution_tracker.track_error(
                    execution_id=execution_id, step_name=f"Error at Turn {self.state_manager.current_turn}",
                    step_index=self.state_manager.current_turn, error=e
                )
                
                recovery_result = await self.execution_recovery.retry_from_step(
                    execution_id=execution_id, step_index=self.state_manager.current_turn,
                    agent_instance=self
                )
                
                if recovery_result.success:
                    feedback.add_info("Attempting recovery from last checkpoint...")
                    continue
                else:
                    await self._transition_state(AgentState.ERROR)
                    await self.event_bus.emit(Event(EventType.AGENT_ERROR, error=str(e), error_type=type(e).__name__))
                    await self.hook_manager.trigger(
                        HookEvent.ON_ERROR,
                        self._hook_context_builder.build(HookEvent.ON_ERROR, error=str(e), error_type=type(e).__name__)
                    )
                    break

        await self.hook_manager.trigger(
            HookEvent.ON_SHUTDOWN,
            self._hook_context_builder.build(HookEvent.ON_SHUTDOWN, final_state=self.state_manager.current_state.value)
        )
        return {
            "final_response": "", "feedback": feedback.get_all(),
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

        # P11: Log agent thinking
        import time
        thinking_start = time.time()
        self.action_logger.log(
            action_type=ActionType.AGENT_THINKING,
            message_count=len(self.context_manager.get_messages()),
            tool_count=len(self.tool_manager.get_tool_definitions())
        )

        # P11: Log LLM request
        messages = self.context_manager.get_messages()
        tools = self.tool_manager.get_tool_definitions()
        self.action_logger.log(
            action_type=ActionType.LLM_REQUEST,
            provider=self.client.provider_name,
            model=self.client.model_name,
            messages_count=len(messages),
            tools_count=len(tools),
            max_tokens=8000
        )

        try:
            response = await self.client.create_message(
                system=self.context_manager.system_prompt,
                messages=messages,
                tools=tools,
                max_tokens=8000,
                stream=False
            )

            # P11: Log LLM response
            usage = response.usage or {}
            self.action_logger.log(
                action_type=ActionType.LLM_RESPONSE,
                provider=self.client.provider_name,
                model=response.model,
                stop_reason=response.stop_reason,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                content_blocks=len(response.content)
            )

            return response

        except Exception as e:
            # P11: Log LLM error
            self.action_logger.log(
                action_type=ActionType.LLM_ERROR,
                status="error",
                provider=self.client.provider_name,
                model=self.client.model_name,
                error=str(e),
                error_type=type(e).__name__
            )
            # Re-raise to be handled by outer exception handler
            raise

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

            # P11: Log tool call
            self.action_logger.log(
                action_type=ActionType.TOOL_CALL,
                tool_name=tool_name,
                tool_id=tool_id,
                tool_input=tool_input
            )

            # 生成简短描述用于反馈
            brief_description = self._generate_brief_description(tool_name, tool_input)

            # 添加工具调用反馈
            if feedback:
                feedback.add_tool_call(tool_name, brief_description)

            # Emit: TOOL_SELECTED
            await self.event_bus.emit(Event(
                EventType.TOOL_SELECTED,
                tool_name=tool_name,
                tool_id=tool_id,
                brief_description=brief_description
            ))

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

                    # Emit: TOOL_ERROR (permission denied)
                    await self.event_bus.emit(Event(
                        EventType.TOOL_ERROR,
                        tool_name=tool_name,
                        tool_id=tool_id,
                        error=deny_message,
                        error_type="permission_denied"
                    ))

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": f"Permission denied: {deny_message}",
                        "is_error": True
                    })
                    continue

            if verbose:
                print(f"\n[Using tool: {tool_name}]", flush=True)

            # Emit: TOOL_EXECUTING
            await self.event_bus.emit(Event(
                EventType.TOOL_EXECUTING,
                tool_name=tool_name,
                tool_id=tool_id
            ))

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

            # Define stream bridge for real-time UI updates
            async def _stream_bridge(chunk: str):
                await self.event_bus.emit(Event(
                    EventType.TOOL_OUTPUT_CHUNK,
                    tool_name=tool_name,
                    tool_id=tool_id,
                    chunk=chunk
                ))

            # 执行工具
            result = await self.tool_manager.execute_tool(
                tool_name, 
                tool_input, 
                on_chunk=_stream_bridge
            )

            # 更新工具调用结果
            self.state_manager.update_tool_call_result(
                tool_id,
                result=result if result.success else None,
                error=result.error
            )

            # Trigger: on_tool_result or on_tool_error
            if result.success:
                # Emit: TOOL_COMPLETED
                await self.event_bus.emit(Event(
                    EventType.TOOL_COMPLETED,
                    tool_name=tool_name,
                    tool_id=tool_id,
                    output=result.output
                ))

                # P11: Log successful tool result
                self.action_logger.log(
                    action_type=ActionType.TOOL_RESULT,
                    tool_name=tool_name,
                    tool_id=tool_id,
                    output=result.output,
                    metadata=result.metadata or {}
                )

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
                # Emit: TOOL_ERROR
                await self.event_bus.emit(Event(
                    EventType.TOOL_ERROR,
                    tool_name=tool_name,
                    tool_id=tool_id,
                    error=result.error
                ))

                # P11: Log tool error
                self.action_logger.log(
                    action_type=ActionType.TOOL_ERROR,
                    status="error",
                    tool_name=tool_name,
                    tool_id=tool_id,
                    error=result.error,
                    metadata=result.metadata or {}
                )

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
