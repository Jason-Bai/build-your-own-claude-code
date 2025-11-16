# 功能：P8 - 会话管理器（Session Manager）v2 - 精细化设计

**日期**: 待规划
**优先级**: P2 🟢
**难度**: ⭐⭐⭐⭐
**预计周期**: 2-3 周
**状态**: 📋 设计中
**架构设计**: ✅ v2.0（精细化）

---

## 核心改进（v2.0）

✅ **统一会话模型** - 引入 `Session` 数据类
- 将分散的上下文（对话、命令、执行历史）统一管理。
- 实现完整的会话保存、加载和恢复能力。

✅ **分层状态管理** - `SessionManager` 作为顶层协调者
- `SessionManager` 负责宏观的会话生命周期。
- `EnhancedAgent` 专注于单次任务的执行逻辑。
- 职责更清晰，降低系统复杂度。

✅ **增强的用户体验**
- 支持跨会话恢复工作状态。
- 完整的命令历史回放和审计。
- 为未来实现多会话、多任务并行奠定基础。

✅ **渐进式迁移策略** - Feature Toggle 方案
- 新旧系统共存，使用功能开关控制切换。
- 低风险、可回退、用户可选。

---

## 问题描述

### 当前状况

随着 `P6 - Checkpoint Persistence` 的引入，系统拥有多种类型的状态和历史，但它们是分散管理的：

- **对话历史**: 由 `AgentContextManager` 管理，存在于内存中。
- **命令历史**: 由 `prompt_toolkit` 的 `InputManager` 管理，保存在文件历史中。
- **执行历史 (`ExecutionHistory`)**: 由 `CheckpointManager` 和 `ExecutionTracker` 管理，通过 `PersistenceManager` 持久化。

**限制**：

- **状态分散**：没有单一的入口点来获取或恢复用户的完整工作状态。
- **无法完整恢复**：虽然可以保存/加载对话，但无法恢复命令历史和正在进行中的复杂任务。
- **架构耦合**：`EnhancedAgent` 承担了过多的状态管理职责。
- **扩展性受限**：难以支持更高级的功能，如并行任务执行或在多个会话之间切换。

### 期望改进

需要一个**顶层协调者**，能够：

- 将所有类型的历史记录聚合到一个统一的 `Session` 对象中。
- 管理 `Session` 的生命周期（开始、结束、暂停）。
- 提供保存和加载整个 `Session` 的能力。
- 完全接管命令历史管理，提供完整的命令回放能力。
- 解耦 `EnhancedAgent` 的状态管理职责，使其更专注于"执行"。

---

## 设计方案

### 核心架构

```
┌─────────────────────────────────────┐
│         src/cli/main.py             │ (CLI 主循环)
│      (REPL Input/Output)            │
└────────────────┬────────────────────┘
                 │ (start_session, process_input)
                 ▼
┌─────────────────────────────────────┐
│     SessionManager (新建)           │ (管理会话生命周期)
│  - 创建位置: src/initialization/    │
│  - 所有权: initialize_agent()       │
│  - 返回: 包含在 agent 对象中        │
└────┬────────────────────────────────┘
     │ (delegates tasks + updates state)
     │
     ├──────────────────┬──────────────────┐
     ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│EnhancedAgent │  │  Session     │  │InputManager  │
│(执行任务)    │  │(数据容器)    │  │(命令历史管理)│
└──────────────┘  └──────────────┘  └──────────────┘
     │
     └──────────────┬──────────────────────┐
                    ▼                      ▼
         ┌────────────────────┐  ┌───────────────────┐
         │ExecutionHistory    │  │PersistenceManager │
         │(执行步骤跟踪)      │  │(物理存储)         │
         └────────────────────┘  └───────────────────┘
```

### 数据结构

#### 1. Session 数据模型

```python
# src/sessions/types.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from ..checkpoint.types import ExecutionHistory

@dataclass
class Session:
    """代表一个完整的用户交互会话"""

    session_id: str                                          # 唯一标识
    project_name: str                                        # 项目名称
    start_time: datetime                                     # 会话开始时间

    # 会话状态
    status: str = "active"                                   # active/paused/completed
    end_time: Optional[datetime] = None                      # 会话结束时间

    # 聚合的历史记录
    conversation_history: List[Dict] = field(default_factory=list)  # 对话消息
    command_history: List[str] = field(default_factory=list)        # 执行的命令
    execution_histories: List[ExecutionHistory] = field(default_factory=list)  # 长流程任务

    # 其他元数据
    metadata: Dict = field(default_factory=dict)             # 扩展信息

    # ========== 便捷方法 ==========

    def to_dict(self) -> Dict:
        """序列化为字典"""
        return {
            "session_id": self.session_id,
            "project_name": self.project_name,
            "start_time": self.start_time.isoformat(),
            "status": self.status,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "conversation_history": self.conversation_history,
            "command_history": self.command_history,
            "execution_histories": [eh.to_dict() for eh in self.execution_histories],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Session":
        """从字典反序列化"""
        return cls(
            session_id=data["session_id"],
            project_name=data["project_name"],
            start_time=datetime.fromisoformat(data["start_time"]),
            status=data.get("status", "active"),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            conversation_history=data.get("conversation_history", []),
            command_history=data.get("command_history", []),
            execution_histories=[
                ExecutionHistory.from_dict(eh) for eh in data.get("execution_histories", [])
            ],
            metadata=data.get("metadata", {}),
        )

    def is_active(self) -> bool:
        """判断会话是否活跃"""
        return self.status == "active"

    def is_completed(self) -> bool:
        """判断会话是否已完成"""
        return self.status == "completed"
```

#### 2. SessionManager 核心实现

```python
# src/sessions/manager.py
from datetime import datetime
from typing import Optional
from .types import Session
from ..persistence.manager import PersistenceManager
from ..utils import OutputFormatter

class SessionManager:
    """管理会话的创建、加载、保存和状态变更"""

    def __init__(self, persistence_manager: PersistenceManager):
        self.persistence = persistence_manager
        self.current_session: Optional[Session] = None
        self._feature_toggle_enabled = True  # 新系统功能开关

    # ========== 会话生命周期 ==========

    def start_session(self, project_name: str, session_id: Optional[str] = None) -> Session:
        """开始一个新会话或加载一个现有会话"""
        if session_id:
            # 尝试加载现有会话
            session_data = self._load_session_sync(session_id)
            if session_data:
                self.current_session = Session.from_dict(session_data)
                self.current_session.status = "active"
                OutputFormatter.success(f"Session loaded: {session_id}")
                return self.current_session
            else:
                OutputFormatter.warning(f"Session not found: {session_id}, creating new one")

        # 创建新会话
        self.current_session = Session(
            session_id=f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            project_name=project_name,
            start_time=datetime.now()
        )
        OutputFormatter.success(f"New session started: {self.current_session.session_id}")
        return self.current_session

    def end_session(self) -> None:
        """结束当前会话"""
        if self.current_session:
            self.current_session.end_time = datetime.now()
            self.current_session.status = "completed"
            self._save_session_sync()
            OutputFormatter.success(f"Session ended: {self.current_session.session_id}")
            self.current_session = None

    def pause_session(self) -> None:
        """暂停当前会话（保留所有状态）"""
        if self.current_session:
            self.current_session.status = "paused"
            self._save_session_sync()
            OutputFormatter.info(f"Session paused: {self.current_session.session_id}")

    def resume_session(self, session_id: str) -> Session:
        """恢复一个暂停的会话"""
        session_data = self._load_session_sync(session_id)
        if session_data:
            self.current_session = Session.from_dict(session_data)
            self.current_session.status = "active"
            OutputFormatter.success(f"Session resumed: {session_id}")
            return self.current_session
        else:
            raise ValueError(f"Session not found: {session_id}")

    # ========== 记录数据 ==========

    def record_message(self, message: Dict) -> None:
        """记录一条对话消息"""
        if self.current_session:
            self.current_session.conversation_history.append(message)

    def record_command(self, command: str) -> None:
        """记录一条命令"""
        if self.current_session:
            self.current_session.command_history.append(command)

    def add_execution_history(self, execution_history) -> None:
        """添加一个执行历史"""
        if self.current_session:
            self.current_session.execution_histories.append(execution_history)

    # ========== 命令历史同步 ==========

    def sync_command_history_to_input_manager(self, input_manager) -> None:
        """
        从 Session 加载命令历史到 prompt_toolkit 的 InputManager
        在会话加载时调用
        """
        if self.current_session and hasattr(input_manager, 'history'):
            # 清空 InputManager 的历史
            if hasattr(input_manager.history, '_strings'):
                input_manager.history._strings.clear()

            # 逐条添加命令历史
            for cmd in self.current_session.command_history:
                if hasattr(input_manager.history, 'append_string'):
                    input_manager.history.append_string(cmd)

            OutputFormatter.info(f"Loaded {len(self.current_session.command_history)} commands")

    def sync_command_history_from_input_manager(self, input_manager) -> None:
        """
        从 prompt_toolkit 的 InputManager 提取命令历史到 Session
        在会话保存时调用
        """
        if self.current_session and hasattr(input_manager, 'history'):
            # 提取所有命令历史
            if hasattr(input_manager.history, 'get_strings'):
                commands = list(input_manager.history.get_strings())
                # 只保留会话开始后的命令
                # （可选：实现增量更新，避免重复）
                self.current_session.command_history = commands

    # ========== 持久化操作 ==========

    def _save_session_sync(self) -> None:
        """同步保存会话（暂时使用同步方式）"""
        if self.current_session:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 在异步上下文中，使用 asyncio.create_task
                    asyncio.create_task(
                        self.persistence.save_session(
                            self.current_session.session_id,
                            self.current_session.to_dict()
                        )
                    )
                else:
                    loop.run_until_complete(
                        self.persistence.save_session(
                            self.current_session.session_id,
                            self.current_session.to_dict()
                        )
                    )
            except RuntimeError:
                # 如果没有事件循环，创建新的
                asyncio.run(
                    self.persistence.save_session(
                        self.current_session.session_id,
                        self.current_session.to_dict()
                    )
                )

    def _load_session_sync(self, session_id: str) -> Optional[Dict]:
        """同步加载会话"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 在异步上下文中，创建新的事件循环（使用线程）
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.persistence.load_session(session_id)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self.persistence.load_session(session_id)
                )
        except RuntimeError:
            return asyncio.run(self.persistence.load_session(session_id))

    async def save_session_async(self) -> None:
        """异步保存会话"""
        if self.current_session:
            await self.persistence.save_session(
                self.current_session.session_id,
                self.current_session.to_dict()
            )

    # ========== 会话查询 ==========

    def list_all_sessions(self) -> List[str]:
        """列出所有会话 ID"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.persistence.list_sessions()
                    )
                    return future.result()
            else:
                return loop.run_until_complete(self.persistence.list_sessions())
        except RuntimeError:
            return asyncio.run(self.persistence.list_sessions())

    def get_current_session(self) -> Optional[Session]:
        """获取当前会话"""
        return self.current_session
```

### 会话存储结构

根据 `P6 - Checkpoint Persistence` 中定义的集中式缓存策略：

```
~/.cache/tiny-claude-code/project-name/persistence/
├── session/
│  ├── session-20251114103000.json
│  └── session-20251114110000.json
├── checkpoint/
│  ├── ckpt-execution-001-0.json
│  └── ckpt-execution-001-1.json
├── conversation/
│  └── conv-auto-save-123.json
└── history/
   └── execution-001.json
```

---

## 实现细节

### 第 1 阶段：基础准备（P8 前提工作）

#### ✅ 已完成
- `src/checkpoint/types.py`: 添加 `StepRecord.to_dict()` / `from_dict()`
- `src/checkpoint/types.py`: 添加 `ExecutionHistory.to_dict()` / `from_dict()`
- `src/persistence/manager.py`: 添加 `save_session()`, `load_session()`, `list_sessions()` 方法

#### 待实现
- 创建 `src/sessions/` 目录
- 实现 `src/sessions/types.py` (Session 数据模型)
- 实现 `src/sessions/manager.py` (SessionManager)
- 编写单元测试和集成测试

### 第 2 阶段：系统集成与迁移（Feature Toggle）

#### 步骤 2.1: 修改初始化系统

```python
# src/initialization/setup.py - 修改 initialize_agent()

async def initialize_agent(config, args):
    # ... 现有初始化代码 ...

    # 新增：初始化 SessionManager
    from ..sessions.manager import SessionManager
    session_manager = SessionManager(persistence_manager)

    # 开始或加载会话
    project_name = Path.cwd().name
    session = session_manager.start_session(project_name)

    # 将 SessionManager 附加到 agent（便于访问）
    agent.session_manager = session_manager

    return agent
```

#### 步骤 2.2: 修改 main.py（使用 Feature Toggle）

```python
# src/cli/main.py - 改造主循环

# 在配置中添加功能开关
USE_SESSION_MANAGER = config.get("features", {}).get("session_manager", False)

async def main():
    # ... 初始化代码保持不变 ...
    agent = await initialize_agent(config, args)

    if USE_SESSION_MANAGER:
        # 新系统：使用 SessionManager
        session_manager = agent.session_manager

        while True:
            user_input = await input_manager.async_get_input()

            if command_registry.is_command(user_input):
                result = await command_registry.execute(user_input, cli_context)
                if result:
                    OutputFormatter.print_assistant_response(result)
                continue

            # 记录命令（可选）
            session_manager.record_command(user_input)

            # 执行任务
            result = await agent.run(user_input, verbose=True)

            if isinstance(result, dict):
                # 记录对话
                session_manager.record_message({
                    "role": "user",
                    "content": user_input,
                    "timestamp": datetime.now().isoformat()
                })
                session_manager.record_message({
                    "role": "assistant",
                    "content": result.get("final_response", ""),
                    "timestamp": datetime.now().isoformat()
                })

                # 显示响应
                OutputFormatter.print_assistant_response(
                    result.get("final_response", "")
                )

            # 自动保存会话
            await session_manager.save_session_async()

    else:
        # 旧系统：保持现有行为
        # ... 现有循环代码 ...
```

#### 步骤 2.3: 扩展 CLI 命令

**关键设计决定**: `/session` 命令采用**与 `/checkpoint` 完全相同的交互模式**

- **单一命令**: `/session` (而非子命令)
- **交互式选择器**: 使用 `InteractiveListSelector` 让用户选择操作
- **简洁的 API**: 命令无参数，所有操作通过交互完成
- **别名支持**: 支持 `/sess`, `/resume`, `/restore` 等

```python
# src/commands/session_commands.py (新建)

from typing import Optional
from .base import Command, CLIContext
from ..cli.interactive import InteractiveListSelector


class SessionCommand(Command):
    """交互式会话管理器 - 列表、加载、恢复会话"""

    @property
    def name(self) -> str:
        return "session"

    @property
    def description(self) -> str:
        return "Interactively manage sessions: load, resume, or view session details."

    @property
    def aliases(self):
        return ["sess", "resume"]  # /sess, /resume 作为别名

    async def execute(self, args: str, context: CLIContext) -> Optional[str]:
        """
        交互式会话管理器

        流程：
        1. 显示所有可用会话（带当前会话标记）
        2. 使用交互式选择器让用户选择
        3. 根据选择执行对应操作
        """
        if not hasattr(context.agent, 'session_manager'):
            return "Session manager not enabled. Set 'features.session_manager=true' in config."

        session_manager = context.agent.session_manager
        current_session = session_manager.get_current_session()

        # 获取所有会话
        all_sessions = session_manager.list_all_sessions()

        if not all_sessions:
            return "No sessions found."

        # 格式化会话列表
        session_items = []

        # 添加 "(current)" 选项
        if current_session:
            current_display = f"(current) Session {current_session.session_id}\n  Status: {current_session.status}\n  Messages: {len(current_session.conversation_history)}\n  Commands: {len(current_session.command_history)}"
            session_items.append(("__current__", current_display))

        # 添加可用的会话列表
        for session_id in all_sessions:
            session_data = session_manager._load_session_sync(session_id)
            if session_data:
                from ..sessions.types import Session
                session = Session.from_dict(session_data)
                display = f"Session {session.session_id}\n  Status: {session.status}\n  Started: {session.start_time}\n  Messages: {len(session.conversation_history)}\n  Commands: {len(session.command_history)}"
                session_items.append((session_id, display))

        # 创建交互式选择器
        selector = InteractiveListSelector(
            title="Sessions",
            items=session_items
        )

        selected_session_id = await selector.run()

        if selected_session_id and selected_session_id != "__current__":
            try:
                # 恢复选中的会话
                session = session_manager.resume_session(selected_session_id)

                # 同步命令历史到 InputManager
                from ..utils import get_input_manager
                input_manager = get_input_manager()
                session_manager.sync_command_history_to_input_manager(input_manager)

                return f"✓ Restored session {session.session_id}\n  Messages: {len(session.conversation_history)}\n  Commands: {len(session.command_history)}"
            except ValueError as e:
                return f"✗ Failed to load session: {str(e)}"

        return "Exited session selection."
```

#### 步骤 2.4: 注册命令

```python
# src/commands/__init__.py - 修改

from .session_commands import SessionCommand  # 新增

def register_builtin_commands():
    """注册所有内置命令"""
    # ... 现有命令 ...

    # Session commands (新增)
    command_registry.register(SessionCommand())
```

### 第 3 阶段：完整迁移（Future）

当功能稳定后，进行如下调整：
- 移除功能开关，默认启用 SessionManager
- 从 EnhancedAgent 中移除对话历史管理代码
- 完全采用 SessionManager 协调的架构

---

## 应用场景

### 场景 1: 完整会话恢复

用户昨天工作到一半，关闭了终端。今天回来后，输入 `/session` 命令：

```
$ /session

╔════════════════════════════════════════════════════════════════╗
║                         Sessions                              ║
╠════════════════════════════════════════════════════════════════╣
║  ➤ (current) Session session-20251115100000                    ║
║      Status: active                                            ║
║      Messages: 12                                              ║
║      Commands: 8                                               ║
║                                                                ║
║    Session session-20251114103000                              ║
║      Status: completed                                         ║
║      Started: 2025-11-14 10:30:00                              ║
║      Messages: 45                                              ║
║      Commands: 23                                              ║
║                                                                ║
║    Session session-20251114150000                              ║
║      Status: paused                                            ║
║      Started: 2025-11-14 15:00:00                              ║
║      Messages: 28                                              ║
║      Commands: 15                                              ║
╚════════════════════════════════════════════════════════════════╝

选择一个会话 (↑/↓ 导航, Enter 确认, Esc 取消):
```

用户通过方向键选择之前的会话，按 Enter：

```
✓ Restored session session-20251114150000
  Messages: 28
  Commands: 15

所有对话历史、命令历史和执行记录已恢复
```

系统将恢复：
- ✅ 完整的对话历史（28 条消息）
- ✅ 所有执行过的命令历史（15 条命令）
- ✅ 所有长流程任务的状态和检查点

### 场景 2: 快速会话切换

用户在处理多个项目时，可以快速切换：

```bash
# 输入命令切换会话
$ /sess

╔════════════════════════════════════════════════════════════════╗
║                         Sessions                              ║
╠════════════════════════════════════════════════════════════════╣
║  ➤ (current) Session session-projectA-20251115100000          ║
║    Session session-projectB-20251115095000                    ║
║    Session session-projectC-20251115090000                    ║
╚════════════════════════════════════════════════════════════════╝

# 选择 session-projectB 后，立即切换完成
✓ Restored session session-projectB-20251115095000
```

所有别名生效：`/session`、`/sess`、`/resume` 都能触发同一个交互器

### 场景 3: 任务审计和回顾

在当前会话中，用户可以查看 session 的完整数据：

```bash
# Session 数据文件位置
~/.cache/tiny-claude-code/project-name/persistence/session/session-20251114150000.json

# 内容示例
{
  "session_id": "session-20251114150000",
  "project_name": "my-project",
  "start_time": "2025-11-14T15:00:00",
  "status": "paused",
  "conversation_history": [
    {"role": "user", "content": "...", "timestamp": "2025-11-14T15:00:30"},
    {"role": "assistant", "content": "...", "timestamp": "2025-11-14T15:00:35"},
    ...
  ],
  "command_history": [
    "git status",
    "git add .",
    "git commit -m '...'",
    ...
  ],
  "execution_histories": [
    {
      "execution_id": "exec-001",
      "status": "completed",
      "steps": [...],
      "checkpoints": [...]
    }
  ]
}
```

完整的审计记录可用于：
- 精确回顾整个工作流程
- 分析 AI 助手的决策过程
- 调试复杂的多步任务
- 团队协作中的知识转移

### 场景 4: 会话管理（未来增强）

未来可扩展的功能：

```bash
# 在 /session 选择界面中可添加快捷键
[D] - 删除会话
[E] - 导出会话为 JSON/HTML
[S] - 显示会话统计信息
[A] - 存档会话（标记为只读）

# 导出功能示例
✓ Session exported: session-20251114150000.html
# 生成美化的 HTML 报告，包含对话、命令和执行历史
```

---

## `/session` 命令设计 - 与 `/checkpoint` 对齐

### 命令设计理念一致性

| 维度 | `/checkpoint` | `/session` | 说明 |
|------|--------------|-----------|------|
| **命令形式** | 单一命令 `/checkpoint` | 单一命令 `/session` | 无参数，交互式选择 |
| **交互方式** | `InteractiveListSelector` | `InteractiveListSelector` | 统一的交互体验 |
| **别名** | `/rewind`, `/restore` | `/sess`, `/resume` | 多种快捷方式 |
| **当前标记** | `(current) - 不恢复，继续当前` | `(current) - 保持当前会话` | 相同的用户体验 |
| **选择器菜单** | 执行历史列表 + (current) | 会话列表 + (current) | 相同的列表结构 |
| **返回消息** | 恢复成功/失败反馈 | 恢复成功/失败反馈 | 一致的反馈格式 |
| **命令注册** | `CommandRegistry.register()` | `CommandRegistry.register()` | 同一套命令系统 |

### 实现对齐

```python
# 两个命令都遵循 Command 基类约定
class Command(ABC):
    @property
    def name(self) -> str: ...
    @property
    def description(self) -> str: ...
    @property
    def aliases(self) -> List[str]: ...
    async def execute(self, args: str, context: CLIContext) -> Optional[str]: ...

# /checkpoint 实现
class CheckpointCommand(Command):
    name = "checkpoint"
    aliases = ["rewind", "restore"]
    # 使用 InteractiveListSelector 选择检查点

# /session 实现（镜像结构）
class SessionCommand(Command):
    name = "session"
    aliases = ["sess", "resume"]
    # 使用 InteractiveListSelector 选择会话
```

### 用户体验一致性

**执行流程相同**:

```
用户输入命令 → 获取所有项目列表 → 显示交互式选择器
→ 用户选择 → 执行恢复 → 返回反馈消息

/checkpoint:    /checkpoint → 检查点列表 → 选择 → 恢复检查点
/session:       /session    → 会话列表    → 选择 → 恢复会话
```

**文本格式相同**:

```
(current) <标记>
  <项目描述>

<Project/Session Name>
  <详细信息>
```

### 命令帮助文本

在 `/help` 中的显示：

```
Available commands:
  ...
  /checkpoint (alias: /rewind, /restore)
    Interactively restore the agent and workspace to a previous checkpoint.

  /session (alias: /sess, /resume)
    Interactively manage sessions: load, resume, or view session details.
  ...
```

---

## 测试验证

### 单元测试

#### 1. Session 数据模型测试 (`tests/test_sessions/test_types.py`)

```python
def test_session_creation():
    """测试 Session 创建"""
    session = Session(
        session_id="test-1",
        project_name="test-project",
        start_time=datetime.now()
    )
    assert session.session_id == "test-1"
    assert session.is_active()
    assert not session.is_completed()

def test_session_serialization():
    """测试 Session 序列化和反序列化"""
    session = Session(
        session_id="test-1",
        project_name="test-project",
        start_time=datetime.now(),
        conversation_history=[
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"}
        ]
    )

    # 序列化
    data = session.to_dict()
    assert data["session_id"] == "test-1"
    assert len(data["conversation_history"]) == 2

    # 反序列化
    restored = Session.from_dict(data)
    assert restored.session_id == session.session_id
    assert len(restored.conversation_history) == 2
```

#### 2. SessionManager 生命周期测试 (`tests/test_sessions/test_manager.py`)

```python
async def test_session_manager_create():
    """测试创建新会话"""
    persistence = MagicMock()
    manager = SessionManager(persistence)

    session = manager.start_session("test-project")
    assert session is not None
    assert session.status == "active"
    assert manager.current_session == session

async def test_session_manager_end():
    """测试结束会话"""
    persistence = AsyncMagicMock()
    manager = SessionManager(persistence)

    manager.start_session("test-project")
    manager.end_session()

    assert manager.current_session is None
    persistence.save_session.assert_called_once()

async def test_session_manager_record_message():
    """测试记录消息"""
    persistence = MagicMock()
    manager = SessionManager(persistence)

    manager.start_session("test-project")
    manager.record_message({"role": "user", "content": "test"})

    assert len(manager.current_session.conversation_history) == 1

async def test_session_manager_pause_resume():
    """测试暂停和恢复会话"""
    persistence = AsyncMagicMock()
    manager = SessionManager(persistence)

    manager.start_session("test-project")
    manager.pause_session()
    assert manager.current_session.status == "paused"
```

### 集成测试

#### 1. 会话生命周期完整流程 (`tests/test_sessions/test_integration.py`)

```python
async def test_complete_session_flow():
    \"\"\"\n    测试完整的会话流程：\n    创建 → 记录数据 → 保存 → 加载 → 恢复\n    \"\"\"\n    # 初始化持久化存储（使用文件）\n    from ..persistence.storage.json_storage import JSONStorage\n    storage = JSONStorage(temp_dir)\n    persistence = PersistenceManager(storage)\n    \n    # 第一步：创建会话并记录数据\n    manager1 = SessionManager(persistence)\n    session1 = manager1.start_session(\"test-project\")\n    session1_id = session1.session_id\n    \n    manager1.record_message({\"role\": \"user\", \"content\": \"question\"})\n    manager1.record_message({\"role\": \"assistant\", \"content\": \"answer\"})\n    manager1.record_command(\"git status\")\n    \n    await manager1.save_session_async()\n    \n    # 第二步：创建新的 SessionManager 加载会话\n    manager2 = SessionManager(persistence)\n    session2 = manager2.resume_session(session1_id)\n    \n    # 验证数据完整性\n    assert session2.session_id == session1_id\n    assert len(session2.conversation_history) == 2\n    assert len(session2.command_history) == 1\n```

#### 2. 命令历史同步测试

```python
async def test_command_history_sync():
    \"\"\"测试命令历史在 Session 和 InputManager 之间的同步\"\"\"\n    from unittest.mock import MagicMock\n    \n    # 模拟 InputManager\n    mock_input_manager = MagicMock()\n    mock_input_manager.history = MagicMock()\n    mock_input_manager.history.get_strings = MagicMock(\n        return_value=[\"cmd1\", \"cmd2\", \"cmd3\"]\n    )\n    \n    persistence = MagicMock()\n    manager = SessionManager(persistence)\n    manager.start_session(\"test-project\")\n    \n    # 从 InputManager 同步到 Session\n    manager.sync_command_history_from_input_manager(mock_input_manager)\n    \n    assert len(manager.current_session.command_history) == 3\n    assert \"cmd1\" in manager.current_session.command_history\n```

---

## 实现建议与注意事项

### 1. Feature Toggle 配置

在 `~/.tiny-claude-code/settings.json` 中添加：

```json
{
  "features": {
    "session_manager": false  // 默认关闭，逐步开启
  }
}
```

用户可在任何时候启用新功能进行测试。

### 2. 异步/同步处理

`SessionManager` 提供了同步和异步两套方法：
- 同步方法 (`_save_session_sync`, `_load_session_sync`): 用于 main 循环
- 异步方法 (`save_session_async`): 用于需要异步处理的场景

这样既不破坏现有的同步代码，也支持未来的异步优化。

### 3. 命令历史完全接管

与 v1 的主要区别是第 2 阶段的 `sync_command_history_*` 方法：
- `sync_command_history_to_input_manager()`: 在会话加载时调用，将 Session 的命令历史恢复到 InputManager
- `sync_command_history_from_input_manager()`: 在会话保存时调用，从 InputManager 提取最新的命令历史

这样保证命令历史的完整性和可恢复性。

### 4. 向后兼容性

- P8 v2 **不支持**加载 P8 前的 conversation 格式
- 用户应该在迁移前导出或备份重要的对话
- 这是一个架构升级，兼容性成本较高，不建议支持

### 5. 逐步迁移策略

```
当前 (v2.0)          3个月后            6个月后
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 功能开关默认 │  │ 生产环境开启 │  │ 完全统一     │
│ 关闭         │  │ SessionMgr   │  │ 移除旧系统   │
│              │  │ 广泛测试     │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 实现路线图

| 阶段 | 任务 | 周期 | 优先级 |
|------|------|------|--------|
| P8.0 | 实现 Session 数据模型 + SessionManager | 1周 | P0 |
| P8.0 | 编写单元测试和集成测试 | 1周 | P0 |
| P8.1 | 集成 initialize_agent，添加 Feature Toggle | 3-4天 | P1 |
| P8.1 | 实现 CLI 会话命令 | 3-4天 | P1 |
| P8.1 | 生产验证和 bug 修复 | 1周 | P1 |
| P8.2 | 完整迁移（移除功能开关） | 1周 | P2 |

**总周期**: 2-3 周（取决于测试覆盖和 bug 修复）

---

## 依赖关系

```
P8 (Session Manager v2)
├── ✅ P6 (Checkpoint Persistence) - 已完成
├── ✅ ExecutionHistory 序列化 - 本 PR 已补充
├── ✅ PersistenceManager Session API - 本 PR 已补充
└── P7 (Multi-Agent Orchestration) - 后续增强
```

---

## 配置示例

### 启用 Session Manager

```json
// ~/.tiny-claude-code/settings.json
{
  \"model\": {
    \"provider\": \"anthropic\",
    \"temperature\": 0.7
  },
  \"features\": {
    \"session_manager\": true  // 启用会话管理器
  },
  \"persistence\": {
    \"storage_type\": \"json\",  // 或 \"sqlite\"
    \"cache_dir\": \"~/.cache/tiny-claude-code\"
  }
}
```

---

**实现者**: 待安排
**状态**: 📋 设计中
**相关 Phase**: P7 (Multi-Agent Orchestration)
**优化目标**: P9 (Distributed Execution Tracing)

