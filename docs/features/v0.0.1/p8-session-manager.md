# 功能：P8 - 会话管理器（Session Manager）

**日期**: 待规划
**优先级**: P2 🟢
**难度**: ⭐⭐⭐⭐
**预计周期**: 2 周
**状态**: 📋 未开始
**架构设计**: ✅ v1.0

---

## 核心改进（v1.0）

✅ **统一会话模型** - 引入 `Session`
- 将分散的上下文（对话、命令、执行历史）统一管理。
- 实现完整的会话保存、加载和恢复能力。

✅ **分层状态管理** - `SessionManager` 作为顶层协调者
- `SessionManager` 负责宏观的会话生命周期。
- `EnhancedAgent` 专注于单次任务的执行逻辑。
- 职责更清晰，降低系统复杂度。

✅ **增强的用户体验**
- 支持跨会话恢复工作状态。
- 为未来实现多会话、多任务并行奠定基础。

---

## 概述

实现一个顶层的**会话管理器（Session Manager）**，用于统一管理用户与 AI 助手的整个交互生命周期。它将协调对话历史、命令历史和长流程任务的执行历史（`ExecutionHistory`），提供一个完整的、可持久化的会话上下文。

---

## 问题描述

### 当前状况

随着 `P6 - Checkpoint Persistence` 的引入，系统将拥有多种类型的状态和历史，但它们是分散管理的：

-   **对话历史**: 由 `AgentContextManager` 管理，存在于内存中。
-   **命令历史**: 由 `prompt_toolkit` 的 `InputManager` 管理，通常保存在一个简单的历史文件中。
-   **执行历史 (`ExecutionHistory`)**: 由 `CheckpointManager` 和 `ExecutionTracker` 管理，通过 `PersistenceManager` 持久化。

**限制**：

-   **状态分散**：没有单一的入口点来获取或恢复用户的完整工作状态。
-   **无法完整恢复**：虽然可以保存/加载对话，但无法恢复命令历史和正在进行中的复杂任务。
-   **架构耦合**：`EnhancedAgent` 承担了过多的状态管理职责，既要处理对话上下文，又要处理任务执行。
-   **扩展性受限**：难以支持更高级的功能，如并行任务执行或在多个会话之间切换。

### 期望改进

需要一个**顶层协调者**，能够：

-   将所有类型的历史记录聚合到一个统一的 `Session` 对象中。
-   管理 `Session` 的生命周期（开始、结束、暂停）。
-   提供保存和加载整个 `Session` 的能力。
-   解耦 `EnhancedAgent` 的状态管理职责，使其更专注于“执行”。

---

## 设计方案

### 核心架构

引入 `SessionManager` 作为 `main` 循环和 `EnhancedAgent` 之间的协调层。

```
+---------------------+
|      main.py        | (应用主循环)
| (CLI Input/Output)  |
+----------+----------+
           |
           | (start_session, process_input)
           v
+---------------------+
|   SessionManager    | (管理 Session 生命周期)
+----------+----------+
           |
           | (delegates tasks)
           |
+----------v----------+      +---------------------+
|   EnhancedAgent     |----->|  ExecutionHistory   | (执行长流程任务)
+---------------------+      +---------------------+
           |
           | (updates session state)
           v
+---------------------+
|       Session       | (数据模型：聚合所有历史)
| - Conversation      |
| - Command History   |
| - ExecutionHistory  |
+----------+----------+
           |
           | (save/load)
           v
+---------------------+
| PersistenceManager  | (负责物理存储)
+---------------------+
```

### 数据结构

#### Session

```python
# src/sessions/types.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict

# 假设 ExecutionHistory 已定义
from ..checkpoint.types import ExecutionHistory

@dataclass
class Session:
    """代表一个完整的用户交互会话"""

    session_id: str
    project_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "active"  # active, paused, completed

    # 聚合的历史记录
    conversation_history: List[Dict] = field(default_factory=list)
    command_history: List[str] = field(default_factory=list)
    execution_histories: List[ExecutionHistory] = field(default_factory=list)

    # 其他元数据
    metadata: Dict = field(default_factory=dict)
```

### 会话存储结构

根据 `P6 - Checkpoint Persistence` 中定义的集中式缓存策略，所有会话数据将存储在用户主目录下的 `.cache/tiny-claude-code/` 目录中，并按项目名称进行隔离。每个会话文件将位于 `session` 类别子目录下。

```
~/.cache/tiny-claude-code/project-name/persistence/
├── session/
│  ├── session-20251114103000.json  # 示例：一个会话文件
│  └── session-20251114110000.json
├── checkpoint/
│  ├── ckpt-execution-001-0.json
│  └── ckpt-execution-001-1.json
├── conversation/
│  └── conv-auto-save-123.json
└── history/
   └── execution-001.json
```

-   **`~/.cache/tiny-claude-code/`**: 统一的根缓存目录。
-   **`project-name/`**: 当前项目的工作目录名称，用于隔离不同项目的持久化数据。
-   **`persistence/`**: 持久化数据的根目录。
-   **`session/`**: 专门用于存放 `Session` 对象的 JSON 文件（或 SQLite 数据库中的表）。每个文件（或记录）的名称将是 `session-<session_id>.json`。

---

## 实现细节

### 核心组件

#### 1. SessionManager

这是新的核心协调器，负责管理会话状态。

```python
# src/sessions/manager.py

class SessionManager:
    """管理会话的创建、加载、保存和状态变更"""

    def __init__(self, persistence_manager: PersistenceManager):
        self.persistence = persistence_manager
        self.current_session: Optional[Session] = None

    def start_session(self, project_name: str, session_id: Optional[str] = None) -> Session:
        """开始一个新会话或加载一个现有会话"""
        if session_id:
            # 加载会话
            session_data = self.persistence.load_session(session_id)
            if session_data:
                self.current_session = Session(**session_data)
                self.current_session.status = "active"
                return self.current_session

        # 创建新会话
        self.current_session = Session(
            session_id=f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            project_name=project_name,
            start_time=datetime.now()
        )
        return self.current_session

    def record_message(self, message: Dict):
        """记录一条对话消息"""
        if self.current_session:
            self.current_session.conversation_history.append(message)

    def record_command(self, command: str):
        """记录一条命令"""
        if self.current_session:
            self.current_session.command_history.append(command)

    def start_new_execution(self) -> ExecutionHistory:
        """为长流程任务创建一个新的 ExecutionHistory"""
        # ... 创建并返回一个新的 ExecutionHistory 实例 ...
        # ... 并将其添加到 self.current_session.execution_histories ...
        pass

    async def save_session(self):
        """使用 PersistenceManager 持久化当前会话"""
        if self.current_session:
            await self.persistence.save_session(
                self.current_session.session_id,
                self.current_session.__dict__  # Or a to_dict() method
            )

    def end_session(self):
        """结束当前会话"""
        if self.current_session:
            self.current_session.end_time = datetime.now()
            self.current_session.status = "completed"
            await self.save_session()
            self.current_session = None

```

#### 2. 与 `PersistenceManager` 的集成

`PersistenceManager` 需要增加与 `Session` 相关的方法。

```python
# src/persistence/manager.py

class PersistenceManager:
    # ... 现有方法 ...

    # ======== Session 相关 ========
    async def save_session(self, session_id: str, session_data: Dict) -> str:
        """保存会话"""
        return await self.storage.save("session", session_id, session_data)

    async def load_session(self, session_id: str) -> Optional[Dict]:
        """加载会话"""
        return await self.storage.load("session", session_id)

    async def list_sessions(self) -> List[str]:
        """列出所有会话"""
        return await self.storage.list("session")
```

### 架构演进路径

#### 第 1 步：引入 `Session` 数据模型和 `SessionManager`

-   创建 `src/sessions/types.py` 和 `src/sessions/manager.py`。
-   在 `PersistenceManager` 中添加 `save/load/list_session` 方法。

#### 第 2 步：重构 `main.py`

`main` 循环将不再直接与 `EnhancedAgent` 交互，而是通过 `SessionManager`。

```python
# src/main.py (伪代码)

async def main():
    # ... 初始化 ...
    persistence = initialize_persistence()
    session_manager = SessionManager(persistence)
    agent = EnhancedAgent(...) # Agent 不再管理顶层对话历史

    # 开始或加载会话
    project_name = Path.cwd().name
    session = session_manager.start_session(project_name)

    # 将会话历史注入 Agent 的上下文
    agent.context_manager.load_messages(session.conversation_history)

    # 主循环
    while True:
        user_input = await get_input()

        if is_command(user_input):
            session_manager.record_command(user_input)
            # ... 执行命令 ...
        else:
            # 将用户输入交给 Agent 处理
            # Agent 的 run 方法现在只关注执行，不直接修改会话历史
            result = await agent.run(user_input)

            # 从 Agent 的结果中更新会话历史
            session_manager.record_message({"role": "user", "content": user_input})
            session_manager.record_message({"role": "assistant", "content": result['final_response']})

        # 每轮交互后自动保存会话
        await session_manager.save_session()
```

#### 第 3 步：解耦 `EnhancedAgent`

-   修改 `EnhancedAgent.run` 方法。它现在接收用户输入，执行任务，然后返回结果，但**不**直接将用户输入和最终响应添加到自己的 `ContextManager` 中。
-   `ContextManager` 的角色变为**单次任务**的上下文管理者，其初始状态由 `SessionManager` 在任务开始前注入。

---

## 应用场景

### 场景 1: 完整会话恢复

用户昨天工作到一半，关闭了终端。今天回来后，可以执行 `/session load <session_id>` 或自动加载上一次的会话。系统将恢复：

-   完整的对话历史。
-   所有执行过的命令历史。
-   所有长流程任务的状态，包括失败、成功或进行中的任务。

### 场景 2: 任务审计和回顾

可以查看一个 `Session` 的完整历史，精确地回顾在解决某个问题时，与 AI 的所有交互，包括简单的问答、执行的命令、以及启动的复杂任务的每一步。

### 场景 3: 多任务处理（未来）

用户可以暂停当前会话（`/session pause`），然后开始一个新会话来处理一个不相关的问题（`/session start new-task`）。完成后，可以随时切回之前的会话（`/session resume <session_id>`）。

---

## 测试验证

### 单元测试

1.  **SessionManager 生命周期测试**：
    *   验证 `start_session` 能正确创建新会话或加载现有会话。
    *   验证 `record_message` 和 `record_command` 能正确将数据添加到 `current_session` 的对应历史列表中。
    *   验证 `start_new_execution` 能正确创建 `ExecutionHistory` 并将其添加到 `current_session.execution_histories`。
    *   验证 `save_session` 能通过 `PersistenceManager` 正确持久化 `Session` 对象。
    *   验证 `end_session` 能正确更新会话状态、结束时间并保存会话。
    *   测试加载不存在的 `session_id` 时，`start_session` 能创建新会话。

2.  **Session 数据模型测试**：
    *   验证 `Session` dataclass 的实例化和属性访问。
    *   验证 `conversation_history`, `command_history`, `execution_histories` 默认是空列表。
    *   验证 `to_dict()` 和 `from_dict()` 方法（如果实现）能正确序列化和反序列化 `Session` 对象及其嵌套的历史数据。

3.  **PersistenceManager Session 相关方法测试**：
    *   验证 `save_session`, `load_session`, `list_sessions` 方法在 `PersistenceManager` 中的正确性。
    *   测试 `load_session` 加载不存在的会话时返回 `None`。

### 集成测试

1.  **`main.py` 重构后的行为验证**：
    *   **会话启动**：验证 `main.py` 启动时能正确初始化 `SessionManager` 并开始/加载会话。
    *   **对话流**：模拟用户输入和 Agent 响应，验证 `SessionManager` 能正确记录对话历史，并且 `EnhancedAgent` 的 `ContextManager` 在每次 `run` 前被正确注入。
    *   **命令流**：模拟用户输入 CLI 命令，验证 `SessionManager` 能正确记录命令历史。
    *   **任务流**：模拟启动一个长流程任务（依赖 P6），验证 `SessionManager` 能正确管理 `ExecutionHistory`。
    *   **自动保存**：验证 `main.py` 在每轮交互后能通过 `SessionManager` 自动保存会话状态。

2.  **完整会话恢复测试**：
    *   模拟一个包含对话、命令和长流程任务的完整会话。
    *   在会话进行中强制退出应用。
    *   重新启动应用，并尝试加载该会话，验证所有历史数据（对话、命令、执行历史）都能被正确恢复。

3.  **CLI 命令测试**：
    *   测试 `/session list` 能正确列出所有可用会话。
    *   测试 `/session load <session_id>` 能正确加载指定会话。
    *   测试 `/session pause` 和 `/session resume` 能正确切换会话状态。
    *   测试 `/session end` 能正确结束会话并保存最终状态。

4.  **跨存储后端测试**：
    *   验证 `SessionManager` 在 `JSONStorage` 和 `SQLiteStorage` 下都能正常工作，并且会话数据能在不同后端之间迁移（如果支持）。

---

## 实现建议与注意事项

1.  **`types.py` 的规划**：
    随着 `Checkpoint`, `ExecutionHistory`, `Session` 等数据类的增多，建议将它们统一放在一个或多个 `types.py` 文件中（例如 `src/persistence/types.py`, `src/sessions/types.py`），以便于管理和导入。

2.  **`main.py` 的重构复杂度**：
    P8 设想的对 `main.py` 的重构是正确的，但在实际操作中可能会比较复杂。需要仔细处理 `SessionManager`、`EnhancedAgent` 和 `InputManager`（用于命令历史）之间的交互。建议在实现时，为 `main.py` 的新逻辑编写详尽的单元测试。

3.  **命令历史的集成**：
    P8 的 `Session` 数据结构中包含了 `command_history`。目前这部分是由 `prompt_toolkit` 独立管理的。在实现 P8 时，需要设计一个机制，在会话开始时将 `Session` 中的命令历史加载到 `prompt_toolkit` 的 `InMemoryHistory` 中，并在会话结束时将其保存回 `Session`。这需要一些额外的“胶水代码”。

---

**实现者**: 待安排
**状态**: 📋 未开始
**依赖**: P6 (Checkpoint Persistence)
**相关 Phase**: P7 (Multi-Agent Orchestration)
