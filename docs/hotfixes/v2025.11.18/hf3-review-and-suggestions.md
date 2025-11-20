# Review & Suggestions: HF3 Comprehensive UX Revamp

## 1. Overall Assessment

The design proposed in `hf3-comprehensive-ux-revamp.md` is excellent and directly addresses the critical UX issues (abrupt start, lack of control, blocking feedback). The three-pillar approach (Welcome, Input Control, Dynamic Feedback) is well-structured.

## 2. Architectural Improvements

### 2.1. Decoupling UI from Agent Logic (Critical)

**Current Design Concern:**
The design introduces `CLICallbackManager` and injects it into `EnhancedAgent.run`.
- **Issue:** This creates a direct dependency between the Agent core logic (`src/agents/`) and the CLI UI implementation (`src/cli/` + `rich`). The Agent should ideally remain UI-agnostic.
- **Risk:** Makes it harder to reuse the Agent in other interfaces (e.g., a Web API or GUI) later.

**Proposed Improvement:**
Leverage the existing `EventBus` system to decouple the UI updates.

1.  **Define New Event:** Add `EventType.TOOL_OUTPUT_CHUNK` to `src/events.py`.
2.  **Agent Emits Events:** Instead of calling `callback_manager.on_tool_chunk`, the `BashTool` (or `ToolExecutor`) emits `TOOL_OUTPUT_CHUNK` events.
3.  **CLI Listens:** The `main.py` (or a dedicated `UIEventHandler`) subscribes to the EventBus. When it receives `TOOL_START`, `TOOL_OUTPUT_CHUNK`, and `TOOL_END` events, *it* updates the `rich.Live` display.

**Benefit:** `EnhancedAgent` remains pure. It just emits events. The CLI decides how to render them.

### 2.2. Tool Interface Compatibility

**Current Design Concern:**
The design changes `BashTool.execute` signature to:
`async def execute(self, command: str, on_chunk: callable) -> ToolResult:`

**Proposed Improvement:**
Ensure backward compatibility with `BaseTool` and other tools.
1.  Update `BaseTool.execute` signature or `BashTool.execute` to make `on_chunk` optional:
    ```python
    async def execute(self, command: str, on_chunk: Callable = None, **kwargs) -> ToolResult:
    ```
2.  Update `ToolExecutor` to handle the `on_chunk` callback injection dynamically if the tool supports it.

## 3. Implementation Details

### 3.1. Input Manager
The design correctly identifies the need for `PromptInputManager` updates.
- **Note:** Ensure `_create_key_bindings` is properly implemented as a method within the class, as it's currently missing.

### 3.2. Event-Driven Streaming Flow (Recommended)

If adopting the EventBus approach:

1.  **`src/events.py`**: Add `TOOL_OUTPUT_CHUNK`.
2.  **`src/tools/bash.py`**:
    ```python
    # In execute method
    if on_chunk:
        on_chunk(decoded_line)
    # OR if we pass event_bus to tools (less ideal)
    # OR Agent passes a wrapper callback that emits the event
    ```
3.  **`src/agents/enhanced_agent.py`**:
    - Pass a callback to `tool_manager.execute_tool` that emits `TOOL_OUTPUT_CHUNK`.
    ```python
    async def _emit_chunk(chunk, tool_id):
        await self.event_bus.emit(Event(EventType.TOOL_OUTPUT_CHUNK, tool_id=tool_id, chunk=chunk))
    ```

## 4. Conclusion

The functionality is perfect. The only major suggestion is to **use the EventBus for the streaming feedback** instead of injecting a UI callback manager directly into the Agent. This aligns better with the project's "Event-Driven Extensibility" architecture.
