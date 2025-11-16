# P8 v2.0 - 快速开发参考

## 🎯 一页纸总结

### 你要实现什么？
- 统一的会话管理系统：对话 + 命令 + 执行历史
- 交互式 `/session` 命令（完全镜像 `/checkpoint`）
- 命令历史完全接管（替代 prompt_toolkit）
- Feature Toggle 渐进式迁移

### 三个阶段

```
┌─────────────────┐
│  Phase 1: 核心  │
│  (1 周)         │
├─────────────────┤
│  Session model  │
│  SessionManager │
│  单元测试       │
└─────────────────┘
        ↓
┌─────────────────┐
│ Phase 2: 集成  │
│ (1-1.5 周)      │
├─────────────────┤
│ SessionCommand  │
│ Feature Toggle  │
│ 集成测试        │
└─────────────────┘
        ↓
┌─────────────────┐
│ Phase 3: 迁移  │
│ (1 周)          │
├─────────────────┤
│ 生产验证        │
│ Bug 修复        │
│ 完全迁移        │
└─────────────────┘
```

---

## 📂 文件清单

### 要创建的文件

```
src/sessions/
├── __init__.py
├── types.py          ← Session 数据模型
└── manager.py        ← SessionManager 核心

src/commands/
└── session_commands.py  ← /session 命令实现

tests/test_sessions/
├── test_types.py     ← Session 数据模型测试
└── test_manager.py   ← SessionManager 测试
```

### 要修改的文件

```
src/initialization/setup.py
  └─ initialize_agent() 中创建 SessionManager

src/cli/main.py
  └─ 添加 Feature Toggle 控制执行流

src/commands/__init__.py
  └─ 导入和注册 SessionCommand

src/checkpoint/types.py
  ✅ 已添加：StepRecord.to_dict/from_dict
  ✅ 已添加：ExecutionHistory.to_dict/from_dict

src/persistence/manager.py
  ✅ 已添加：save_session/load_session/list_sessions/delete_session
```

---

## 🔧 核心代码框架

### 1. Session 数据类

```python
# src/sessions/types.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from ..checkpoint.types import ExecutionHistory

@dataclass
class Session:
    session_id: str
    project_name: str
    start_time: datetime
    status: str = "active"
    end_time: Optional[datetime] = None
    conversation_history: List[Dict] = field(default_factory=list)
    command_history: List[str] = field(default_factory=list)
    execution_histories: List[ExecutionHistory] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
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
        return self.status == "active"

    def is_completed(self) -> bool:
        return self.status == "completed"
```

### 2. SessionManager 核心

```python
# src/sessions/manager.py
from datetime import datetime
from typing import Optional, List, Dict
from .types import Session
from ..persistence.manager import PersistenceManager

class SessionManager:
    def __init__(self, persistence_manager: PersistenceManager):
        self.persistence = persistence_manager
        self.current_session: Optional[Session] = None

    # 核心方法
    def start_session(self, project_name: str, session_id: Optional[str] = None) -> Session:
        """开始新会话或加载现有会话"""
        if session_id:
            session_data = self._load_session_sync(session_id)
            if session_data:
                self.current_session = Session.from_dict(session_data)
                self.current_session.status = "active"
                return self.current_session

        self.current_session = Session(
            session_id=f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            project_name=project_name,
            start_time=datetime.now()
        )
        return self.current_session

    def end_session(self) -> None:
        """结束当前会话"""
        if self.current_session:
            self.current_session.end_time = datetime.now()
            self.current_session.status = "completed"
            self._save_session_sync()
            self.current_session = None

    def record_message(self, message: Dict) -> None:
        """记录消息"""
        if self.current_session:
            self.current_session.conversation_history.append(message)

    def record_command(self, command: str) -> None:
        """记录命令"""
        if self.current_session:
            self.current_session.command_history.append(command)

    # 命令历史同步
    def sync_command_history_to_input_manager(self, input_manager) -> None:
        """加载命令历史到 InputManager"""
        if self.current_session and hasattr(input_manager, 'history'):
            if hasattr(input_manager.history, '_strings'):
                input_manager.history._strings.clear()
            for cmd in self.current_session.command_history:
                if hasattr(input_manager.history, 'append_string'):
                    input_manager.history.append_string(cmd)

    def sync_command_history_from_input_manager(self, input_manager) -> None:
        """从 InputManager 提取命令历史"""
        if self.current_session and hasattr(input_manager, 'history'):
            if hasattr(input_manager.history, 'get_strings'):
                commands = list(input_manager.history.get_strings())
                self.current_session.command_history = commands

    # 查询
    def get_current_session(self) -> Optional[Session]:
        return self.current_session

    def list_all_sessions(self) -> List[str]:
        """列出所有会话"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                return loop.run_until_complete(self.persistence.list_sessions())
        except RuntimeError:
            pass
        return []

    # 持久化
    def _save_session_sync(self) -> None:
        """同步保存"""
        if self.current_session:
            import asyncio
            try:
                asyncio.run(
                    self.persistence.save_session(
                        self.current_session.session_id,
                        self.current_session.to_dict()
                    )
                )
            except RuntimeError:
                pass

    def _load_session_sync(self, session_id: str) -> Optional[Dict]:
        """同步加载"""
        import asyncio
        try:
            return asyncio.run(
                self.persistence.load_session(session_id)
            )
        except RuntimeError:
            return None
```

### 3. SessionCommand 实现

```python
# src/commands/session_commands.py
from typing import Optional
from .base import Command, CLIContext
from ..cli.interactive import InteractiveListSelector

class SessionCommand(Command):
    @property
    def name(self) -> str:
        return "session"

    @property
    def description(self) -> str:
        return "Interactively manage sessions: load, resume, or view session details."

    @property
    def aliases(self):
        return ["sess", "resume"]

    async def execute(self, args: str, context: CLIContext) -> Optional[str]:
        if not hasattr(context.agent, 'session_manager'):
            return "Session manager not enabled"

        session_manager = context.agent.session_manager
        all_sessions = session_manager.list_all_sessions()

        if not all_sessions:
            return "No sessions found"

        # 构建会话列表
        session_items = []
        current = session_manager.get_current_session()

        if current:
            display = f"(current) {current.session_id}\n  Status: {current.status}\n  Messages: {len(current.conversation_history)}"
            session_items.append(("__current__", display))

        for session_id in all_sessions:
            session_data = session_manager._load_session_sync(session_id)
            if session_data:
                from ..sessions.types import Session
                session = Session.from_dict(session_data)
                display = f"{session.session_id}\n  Status: {session.status}\n  Messages: {len(session.conversation_history)}"
                session_items.append((session_id, display))

        # 显示选择器
        selector = InteractiveListSelector(title="Sessions", items=session_items)
        selected_id = await selector.run()

        if selected_id and selected_id != "__current__":
            try:
                session = session_manager.resume_session(selected_id)
                from ..utils import get_input_manager
                input_manager = get_input_manager()
                session_manager.sync_command_history_to_input_manager(input_manager)
                return f"✓ Session restored: {session.session_id}"
            except ValueError as e:
                return f"✗ Error: {str(e)}"

        return "Exited session selection"
```

---

## 🧪 测试模板

### 单元测试

```python
# tests/test_sessions/test_types.py
import pytest
from datetime import datetime
from src.sessions.types import Session

def test_session_creation():
    session = Session(
        session_id="test-1",
        project_name="test",
        start_time=datetime.now()
    )
    assert session.is_active()
    assert not session.is_completed()

def test_session_serialization():
    session = Session(
        session_id="test-1",
        project_name="test",
        start_time=datetime.now(),
        conversation_history=[{"role": "user", "content": "hi"}]
    )
    data = session.to_dict()
    restored = Session.from_dict(data)
    assert restored.session_id == session.session_id
    assert len(restored.conversation_history) == 1
```

### 集成测试

```python
# tests/test_sessions/test_manager.py
import pytest
from src.sessions.manager import SessionManager
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_session_lifecycle():
    persistence = MagicMock()
    manager = SessionManager(persistence)

    # 创建
    session = manager.start_session("test-project")
    assert session is not None
    assert manager.current_session == session

    # 记录
    manager.record_message({"role": "user", "content": "test"})
    assert len(session.conversation_history) == 1

    # 结束
    manager.end_session()
    assert manager.current_session is None
```

---

## 🔌 集成步骤

### Step 1: 修改 initialize_agent

```python
# src/initialization/setup.py
async def initialize_agent(config, args):
    # ... 现有代码 ...

    # 新增
    from ..sessions.manager import SessionManager
    session_manager = SessionManager(persistence_manager)
    agent.session_manager = session_manager

    return agent
```

### Step 2: 注册命令

```python
# src/commands/__init__.py
from .session_commands import SessionCommand

def register_builtin_commands():
    # ... 现有命令 ...
    command_registry.register(SessionCommand())
```

### Step 3: Feature Toggle

```python
# src/cli/main.py
USE_SESSION_MANAGER = config.get("features", {}).get("session_manager", False)

if USE_SESSION_MANAGER:
    session_manager.record_message({...})
    session_manager.record_command(user_input)
```

---

## 📋 检查清单

### Phase 1 (第 1 周)

- [ ] 创建 `src/sessions/` 目录和 `__init__.py`
- [ ] 实现 `Session` 数据类（70 行代码）
- [ ] 实现 `SessionManager`（80 行代码）
- [ ] 编写单元测试（50 行代码）
- [ ] 验证序列化/反序列化

### Phase 2 (第 2-2.5 周)

- [ ] 实现 `SessionCommand`（80 行代码）
- [ ] 修改 `initialize_agent()`（5 行代码）
- [ ] 修改命令注册（3 行代码）
- [ ] 修改 `main.py` Feature Toggle（20 行代码）
- [ ] 编写集成测试（80 行代码）
- [ ] 验证交互式选择器

### Phase 3 (第 3 周)

- [ ] 启用 Feature Toggle 进行 alpha 测试
- [ ] 收集反馈和修复 bug
- [ ] 完整的回归测试
- [ ] 用户文档
- [ ] 完全迁移

---

## 💡 关键提示

1. **与 /checkpoint 完全对齐** ← 这是关键
   - 同一个 `InteractiveListSelector`
   - 同一套命令注册系统
   - 同一个用户体验

2. **命令历史双向同步** ← 不要忘记
   - `sync_to_input_manager()` - 加载时
   - `sync_from_input_manager()` - 保存时

3. **Feature Toggle 默认关闭** ← 降低风险
   - 新功能不会影响现有用户
   - 可逐步启用

4. **序列化链路必须完整** ← 已验证
   - Session → ExecutionHistory → StepRecord
   - 所有层级都有 to_dict/from_dict

---

## 📞 常见问题

**Q: SessionManager 何时创建？**
A: 在 `initialize_agent()` 中创建，返回给 `main.py`

**Q: 命令历史怎么接管？**
A: 两个方法：`sync_to_input_manager()` 和 `sync_from_input_manager()`

**Q: 如何避免与旧系统冲突？**
A: Feature Toggle，默认关闭，用户可选启用

**Q: 如何测试？**
A: 单元测试 + 集成测试，测试模板已提供

**Q: 什么时候可以删除旧系统？**
A: Phase 3 完成后，用户都迁移到新系统

---

**文档版本**: v2.0
**最后更新**: 2025-11-16
**作者**: Claude Code
