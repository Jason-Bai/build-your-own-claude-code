# Architecture Design Document

This document describes the complete architecture design of the Build Your Own Claude Code project in detail.

## Table of Contents

- [Overall Layered Architecture](#overall-layered-architecture)
- [Core Component Relationships](#core-component-relationships)
- [Data Flow Diagram](#data-flow-diagram)
- [Agent State Machine](#agent-state-machine)
- [Tool System Architecture](#tool-system-architecture)
- [Context Management Strategy](#context-management-strategy)
- [Directory Structure Hierarchy](#directory-structure-hierarchy)
- [Extension Points Design](#extension-points-design)

---

## Overall Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Interface                          │
│                  (User input/output, command processing)    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Enhanced Agent                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  State Manager      Context Manager    Tool Manager    │ │
│  │  (State tracking)   (Context mgmt)     (Tool orchestration)│
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  - Conversation loop control                                │
│  - Multi-turn interaction orchestration                     │
│  - Statistics collection                                    │
└────────┬─────────────────────┬──────────────────────────────┘
         │                     │
    ┌────▼────┐           ┌────▼─────────────────┐
    │ Client  │           │   Tool Ecosystem     │
    │ Layer   │           └──────┬───────────────┘
    └────┬────┘                  │
         │              ┌─────────┼──────────────┐
         │              │         │              │
    ┌────▼─────┐  ┌─────▼────┐ ┌▼──────────┐ ┌─▼────────┐
    │Anthropic │  │Built-in  │ │    MCP    │ │Commands  │
    │  Client  │  │  Tools   │ │  Adapter  │ │  System  │
    └──────────┘  └──────────┘ └───┬───────┘ └──────────┘
                                    │
                          ┌─────────┼──────────┐
                          │         │          │
                     ┌────▼───┐ ┌───▼────┐ ┌──▼─────┐
                     │MCP     │ │MCP     │ │  MCP   │
                     │Server1 │ │Server2 │ │Server3 │
                     └────────┘ └────────┘ └────────┘
```

### Architecture Description

- **CLI Interface**: User interaction layer handling input/output and command parsing
- **Enhanced Agent**: Core control layer integrating three major managers
- **Client Layer**: LLM client abstraction layer supporting multiple models
- **Tool Ecosystem**: Tool ecosystem system including built-in tools, MCP tools, and command system

---

## Core Component Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                     EnhancedAgent                           │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │  StateManager    │  │ ContextManager   │               │
│  │                  │  │                  │               │
│  │ • current_state  │  │ • messages       │               │
│  │ • tool_calls     │  │ • summary        │               │
│  │ • statistics     │  │ • metadata       │               │
│  │ • turn_count     │  │ • token_est      │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                             │
│  ┌──────────────────────────────────────────────┐          │
│  │           ToolManager                        │          │
│  │                                              │          │
│  │  ┌────────────┐         ┌────────────┐      │          │
│  │  │ Built-in   │         │    MCP     │      │          │
│  │  │   Tools    │◄────────┤   Client   │      │          │
│  │  └────────────┘         └────────────┘      │          │
│  │                                              │          │
│  │  • register_tool()                           │          │
│  │  • execute_tool() - intelligent retry        │          │
│  │  • get_tool_definitions()                    │          │
│  │  • usage_statistics                          │          │
│  └──────────────────────────────────────────────┘          │
│                                                             │
│  ┌──────────────────────────────────────────────┐          │
│  │            BaseClient                        │          │
│  │  • create_message()                          │          │
│  │  • generate_summary()                        │          │
│  │  • model_name, context_window                │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### StateManager
- Manages Agent runtime state (IDLE, THINKING, USING_TOOL, COMPLETED, ERROR)
- Records tool call history
- Collects and aggregates performance metrics
- Controls conversation turns

#### ContextManager
- Manages conversation message history
- Estimates token usage
- Performs automatic compression and summarization
- Maintains metadata

#### ToolManager
- Registers and manages all tools (built-in + MCP)
- Executes tool calls (with intelligent retry)
- Gathers tool usage statistics
- Provides unified tool interface

---

## Data Flow Diagram

```
User input "Create a hello.py file"
    │
    ▼
┌─────────────────────────────────────┐
│  CLI command check                   │
│  Is command? No → Continue           │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│  EnhancedAgent.run()                │
│  • StateManager → THINKING          │
│  • ContextManager.add_user_message  │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│  Context compression check           │
│  • estimate_tokens()                │
│  • compress_if_needed()             │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│  Call LLM                            │
│  • Client.create_message()          │
│  • tools = ToolManager.get_defs()   │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│  Parse response                      │
│  • text_blocks: display to user     │
│  • tool_uses: extract tool calls    │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│  Execute tools                       │
│  • StateManager → USING_TOOL        │
│  • ToolManager.execute_tool()       │
│    - Built-in tools → ToolExecutor  │
│    - MCP tools → MCPClient          │
│  • Intelligent retry (max 2 times)  │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│  Update state                        │
│  • StateManager.record_tool_call()  │
│  • StateManager.add_tokens()        │
│  • ContextManager.add_results()     │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│  Continue loop or complete           │
│  • More tool calls? → Continue      │
│  • No tool calls? → COMPLETED       │
│  • Exceeded max_turns? → ERROR      │
└─────────────────────────────────────┘
```

---

## Agent State Machine

```
          [Start]
             │
             ▼
         ┌────────┐
         │  IDLE  │
         └───┬────┘
             │ run()
             ▼
      ┌──────────────┐
      │   THINKING   │◄─────────┐
      └──────┬───────┘          │
             │                  │
   ┌─────────▼─────────┐        │
   │ Need tool call?    │        │
   └─────┬──────┬──────┘        │
         │ Yes  │ No            │
         │      │               │
         │      └───────────────┼──────┐
         │                      │      │
         ▼                      ▼      ▼
  ┌─────────────┐         ┌──────────────┐
  │ USING_TOOL  │         │  COMPLETED   │
  └──────┬──────┘         └──────────────┘
         │
         ▼
  ┌──────────────────┐
  │ WAITING_FOR_     │
  │    RESULT        │
  └──────┬───────────┘
         │
         └──────────────┘

  [Exceeded max_turns or error]
         │
         ▼
    ┌────────┐
    │ ERROR  │
    └────────┘
```

### State Description

- **IDLE**: Initial state, waiting for user input
- **THINKING**: LLM is thinking, generating response
- **USING_TOOL**: Executing tool call
- **WAITING_FOR_RESULT**: Waiting for tool execution result
- **COMPLETED**: Task completed
- **ERROR**: Error occurred or maximum turns exceeded

---

## Tool System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    ToolManager                           │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │           ToolExecutor (Intelligent Retry)      │    │
│  │  ┌──────────────────────────────────────────┐   │    │
│  │  │  for attempt in range(max_retries=2):    │   │    │
│  │  │    result = await tool.execute()         │   │    │
│  │  │    if success: return result             │   │    │
│  │  │    if non_retryable: break               │   │    │
│  │  │    await asyncio.sleep(backoff)          │   │    │
│  │  │  return error to Claude                  │   │    │
│  │  └──────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────┐              ┌──────────────────┐   │
│  │  Built-in      │              │   MCP Tools      │   │
│  │  Tools         │              │                  │   │
│  ├────────────────┤              ├──────────────────┤   │
│  │ • ReadTool     │              │ • mcp_fs_read    │   │
│  │ • WriteTool    │              │ • mcp_gh_pr      │   │
│  │ • EditTool     │              │ • mcp_db_query   │   │
│  │ • BashTool     │              │ • ...            │   │
│  │ • GlobTool     │              └──────────────────┘   │
│  │ • GrepTool     │                                     │
│  │ • TodoWrite    │                                     │
│  └────────────────┘                                     │
└──────────────────────────────────────────────────────────┘
```

### Intelligent Retry Mechanism

1. **Maximum 2 retries**: Automatically retry for retryable errors
2. **Exponential backoff**: Increasing retry intervals (0.5s, 1s)
3. **Non-retryable errors**: Identify errors that should not be retried (file not found, permission denied, etc.)
4. **Post-failure decision**: After all retries fail, return error to Claude for decision-making

---

## Context Management Strategy

```
┌──────────────────────────────────────────────────────────┐
│               ContextManager                             │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Messages: [msg1, msg2, ..., msgN]                      │
│  Summary: "Previous conversation summary..."            │
│  Max Tokens: 150,000 (80% of 200K)                      │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │  Token Estimation (before each conversation)   │     │
│  │  • total = system + summary + messages         │     │
│  │  • chars ≈ tokens * 3 (conservative estimate)  │     │
│  └────────────────────────────────────────────────┘     │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │  Auto Compression (when threshold exceeded)    │     │
│  │                                                 │     │
│  │  [msg1...msg90] + [msg91...msg100]             │     │
│  │       ↓                    ↓                   │     │
│  │   Generate summary     Retain last 10          │     │
│  │       ↓                    ↓                   │     │
│  │   Summary         [msg91...msg100]             │     │
│  └────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────┘
```

### Compression Strategy

1. **Token estimation**: Use character count estimation (1 token ≈ 3 chars)
2. **Trigger condition**: Exceeds max_tokens (default 150K)
3. **Retention strategy**: Retain last 10 messages
4. **Summary generation**: Use Claude to generate summary of old messages
5. **Summary content**: Focus on file modifications, command execution, key decisions, task status

---

## Directory Structure Hierarchy

```
src/
├── agents/                 # 🧠 Agent Core Layer
│   ├── enhanced_agent.py   # Main Agent (integrating all managers)
│   ├── state.py            # State Management (FSM + statistics)
│   ├── context_manager.py  # Context Management (compression + summarization)
│   └── tool_manager.py     # Tool Management (registration + execution)
│
├── clients/                # 🌐 LLM Client Layer
│   ├── base.py             # Abstract Interface
│   └── anthropic.py        # Anthropic Implementation
│
├── tools/                  # 🛠️ Tool Layer
│   ├── base.py             # Tool Base Class
│   ├── file_ops.py         # File Operation Tools
│   ├── bash.py             # Command Execution Tool
│   ├── search.py           # Search Tools
│   └── todo.py             # Todo Management Tool
│
├── commands/               # ⌨️ Command Layer
│   ├── base.py             # Command Base Class + Registry
│   ├── builtin.py          # Built-in Commands
│   └── persistence_commands.py  # Persistence Commands
│
├── mcp_integration.py      # 🔌 MCP Integration Layer
├── persistence.py          # 💾 Persistence Layer
├── registry.py             # 📋 Tool Registry Layer
├── prompt.py               # 📝 Prompt Layer
└── main.py                 # 🚀 Entry Point Layer
```

### Layer Description

- **Agent Core Layer**: Core Agent implementation and managers
- **LLM Client Layer**: Abstraction for interaction with LLM service providers
- **Tool Layer**: Actual tool collection for executing tasks
- **Command Layer**: CLI command system
- **Integration Layer**: MCP, persistence, and other external integrations
- **Entry Point Layer**: Application startup and initialization

---

## Extension Points Design

```
┌─────────────────────────────────────────────────────────┐
│              Extension Interface                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Add New LLM Provider                               │
│     └─ Implement BaseClient interface                  │
│        • create_message()                               │
│        • generate_summary()                             │
│        • model_name, context_window                     │
│                                                         │
│  2. Add New Tool                                        │
│     └─ Inherit from BaseTool                            │
│        • name, description, input_schema                │
│        • execute()                                      │
│        • register with ToolManager                      │
│                                                         │
│  3. Add New Command                                     │
│     └─ Inherit from Command                             │
│        • name, description, aliases                     │
│        • execute()                                      │
│        • register with CommandRegistry                  │
│                                                         │
│  4. Add New MCP Server                                  │
│     └─ Configure in ~/.tiny-claude-code/settings.json                         │
│        • name, command, args, env                       │
│        • enabled: true/false                            │
│                                                         │
│  5. LangGraph Integration                               │
│     └─ Leverage StateManager interface                  │
│        • Listen to state changes: on_state_change       │
│        • Access state: get_current_state()              │
│        • Retrieve statistics: get_statistics()          │
│                                                         │
│  6. Streaming Output                                    │
│     └─ Use BaseClient.create_message(stream=True)       │
│        • async for chunk in stream                      │
│        • Display in real-time to user                   │
│                                                         │
│  7. Custom State Hooks                                  │
│     └─ EnhancedAgent(on_state_change=callback)          │
│        • def callback(old_state, new_state)             │
│        • Can be used for logging, monitoring, UI update  │
│                                                         │
│  8. Custom Compression Strategy                         │
│     └─ Extend ContextManager                            │
│        • Customize compress_if_needed()                 │
│        • Customize summary prompt                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Extension Examples

#### Adding a New LLM Provider

```python
from src.clients.base import BaseClient, ModelResponse

class OpenAIClient(BaseClient):
    async def create_message(self, system, messages, tools, **kwargs):
        # Implement OpenAI API call
        response = await openai.chat.completions.create(...)
        return ModelResponse(...)

    async def generate_summary(self, prompt):
        # Implement summary generation
        pass

    @property
    def model_name(self):
        return "gpt-4"

    @property
    def context_window(self):
        return 128000
```

#### Adding a New Tool

```python
from src.tools.base import BaseTool, ToolResult

class WebSearchTool(BaseTool):
    @property
    def name(self):
        return "WebSearch"

    @property
    def description(self):
        return "Search the web for information"

    @property
    def input_schema(self):
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }

    async def execute(self, query: str) -> ToolResult:
        # Implement web search
        results = await search_web(query)
        return ToolResult(success=True, output=results)
```

#### LangGraph Integration

```python
from langgraph.graph import StateGraph
from src.agents import EnhancedAgent, AgentState

def create_langgraph_agent(agent: EnhancedAgent):
    workflow = StateGraph(AgentState)

    # Define nodes
    workflow.add_node("think", agent.run)
    workflow.add_node("use_tool", lambda x: x)

    # Define edges
    workflow.add_edge("think", "use_tool")
    workflow.add_edge("use_tool", "think")

    return workflow.compile()
```

---

## Design Principles

### 1. Separation of Concerns
Each component is responsible for exactly one concern:
- StateManager only manages state
- ContextManager only manages context
- ToolManager only manages tools

### 2. Dependency Inversion
Decouple through abstract interfaces:
- BaseClient abstracts LLM providers
- BaseTool abstracts tool implementations
- Command abstracts command implementations

### 3. Open/Closed Principle
Open for extension, closed for modification:
- Adding new tools requires no core code changes
- Adding new LLM providers does not affect Agent logic
- Adding new commands does not affect existing commands

### 4. Single Responsibility
Each class has only one reason to change:
- Agent changes only due to conversation flow changes
- ToolManager changes only due to tool management strategy changes
- ContextManager changes only due to context strategy changes

---

## Performance Considerations

### Token Usage Optimization
1. **Estimation rather than exact calculation**: Avoid calling tokenizer API
2. **Conservative estimation**: Better to overestimate than underestimate
3. **On-demand compression**: Compress only when approaching limits
4. **Batch operations**: Process multiple messages at once

### Tool Execution Optimization
1. **Intelligent retry**: Only retry errors that may succeed
2. **Parallel execution**: Future support for parallel tool calls
3. **Result caching**: Optional tool result caching
4. **Timeout control**: Prevent tools from executing too long

### Memory Management
1. **Message compression**: Automatically clean old messages
2. **Summary replacement**: Replace detailed history with summary
3. **Streaming processing**: Use streaming for large files
4. **Timely cleanup**: Clean resources after session ends

---

## Security Considerations

### 1. Input Validation
- File path validation (prevent path traversal)
- Command injection protection
- JSON Schema validation for tool parameters

### 2. Resource Limits
- Maximum conversation turns limit
- Tool execution timeout
- File size limits
- Token usage limits

### 3. Error Handling
- Sensitive information not written to logs
- Error message sanitization
- Exception catching and recovery

### 4. Permission Control
- Tool execution permission checks
- File access permission control
- MCP server authentication

---

## Testability

### Unit Tests
Each component can be tested independently:
```python
# Test StateManager
def test_state_transition():
    manager = AgentStateManager()
    manager.transition_to(AgentState.THINKING)
    assert manager.current_state == AgentState.THINKING

# Test ToolManager
async def test_tool_execution():
    manager = AgentToolManager()
    manager.register_tool(MockTool())
    result = await manager.execute_tool("MockTool", {})
    assert result.success

# Test ContextManager
async def test_context_compression():
    manager = AgentContextManager(max_tokens=100)
    # Add large number of messages
    # Verify compression logic
```

### Integration Tests
Test component interactions:
```python
async def test_agent_flow():
    agent = EnhancedAgent(client, system_prompt)
    agent.tool_manager.register_tools([...])
    result = await agent.run("Create a file")
    assert result["agent_state"]["state"] == "completed"
```

---

## Summary

Core advantages of this architecture design:

1. **Clear Layering**: Well-defined responsibilities, easy to understand
2. **High Decoupling**: Minimal dependencies between components
3. **Easy to Test**: Each component can be tested independently
4. **Strong Extensibility**: Multiple reserved extension points
5. **Production Ready**: Complete error handling, monitoring, statistics

Suitable as:
- **Learning Project**: Understanding AI Agent architecture
- **Production Foundation**: Building actual applications
- **Research Platform**: Experimenting with new Agent strategies

---