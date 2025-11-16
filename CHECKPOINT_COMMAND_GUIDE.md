# Checkpoint 命令实现完整搜索结果

## 目录结构

代码库中 Checkpoint 相关文件位置：

```
/Users/baiyu/workspaces/laboratory/build-your-own-claude-code/
├── src/
│   ├── checkpoint/                          # Checkpoint 核心模块
│   │   ├── __init__.py
│   │   ├── types.py                        # Checkpoint 数据结构
│   │   ├── manager.py                      # CheckpointManager 类
│   │   └── recovery.py                     # 恢复逻辑
│   ├── commands/
│   │   ├── __init__.py                     # 命令注册表
│   │   ├── base.py                         # 命令基类
│   │   └── checkpoint_commands.py           # CheckpointCommand 实现
│   ├── persistence/
│   │   ├── manager.py                      # PersistenceManager
│   │   └── storage.py                      # 存储后端 (JSON/SQLite)
│   └── agents/
│       └── enhanced_agent.py               # Agent 集成
├── docs/
│   └── features/v0.0.1/
│       └── p6-checkpoint-persistence.md    # 完整设计文档
└── tests/
    └── unit/
        └── test_persistence_system.py      # 单元测试
```

---

## 1. 命令定义和注册

### 位置：`/src/commands/checkpoint_commands.py`

**命令类**：`CheckpointCommand`

#### 命令属性

- **命令名**: `checkpoint`
- **命令别名**: `rewind`, `restore`
- **描述**: "Interactively restore the agent and workspace to a previous checkpoint."

```python
class CheckpointCommand(Command):
    """Interactively restore the agent and workspace to a previous checkpoint."""

    @property
    def name(self) -> str:
        return "checkpoint"

    @property
    def description(self) -> str:
        return "Interactively restore the agent and workspace to a previous checkpoint."

    @property
    def aliases(self):
        return ["rewind", "restore"]
```

#### 命令执行接口

```python
async def execute(self, args: str, context: CLIContext) -> Optional[str]:
    """
    Fetches checkpoint history and uses an interactive selector to let the user
    choose a checkpoint to resume from.
    """
    checkpoint_manager = context.agent.checkpoint_manager
    
    # 获取格式化的检查点历史
    history_items = await checkpoint_manager.get_formatted_checkpoint_history()

    if not history_items:
        return "No checkpoints found."

    # 添加"(current)"选项
    current_display = "(current)\n  Do not restore, continue with the current session."
    history_items.insert(0, ("__current__", current_display))

    # 交互式选择器
    selector = InteractiveListSelector(
        title="Checkpoints",
        items=history_items
    )

    selected_execution_id = await selector.run()

    if selected_execution_id and selected_execution_id != "__current__":
        # TODO: 恢复逻辑未完全实现
        return f"Selected execution to restore: {selected_execution_id}."
    
    return "Exited checkpoint selection."
```

### 命令注册位置：`/src/commands/__init__.py`

```python
def register_builtin_commands():
    """注册所有内置命令"""
    command_registry.register(HelpCommand())
    command_registry.register(ClearCommand())
    command_registry.register(ExitCommand())
    command_registry.register(StatusCommand())
    command_registry.register(TodosCommand())
    command_registry.register(SaveCommand())
    command_registry.register(LoadCommand())
    command_registry.register(ListConversationsCommand())
    command_registry.register(DeleteConversationCommand())
    # Checkpoint commands
    command_registry.register(CheckpointCommand())
    # Workspace commands
    command_registry.register(InitCommand())
    command_registry.register(ShowContextCommand())
    command_registry.register(LoadContextCommand())
    # Output commands
    command_registry.register(VerboseCommand())
    command_registry.register(QuietCommand())
```

---

## 2. 命令执行方式

### 命令行调用语法

```bash
# 使用主命令名
/checkpoint

# 使用别名
/rewind
/restore
```

### 参数格式

当前实现**不支持参数**，所有操作都通过交互式选择器完成。

### 返回结果格式

- **成功**: 返回字符串消息
- **交互式**: 显示检查点列表，用户选择恢复点

#### 返回示例

```
# 无检查点时
"No checkpoints found."

# 用户选择恢复
"Selected execution to restore: exec-123. (Resume logic not yet fully implemented)."

# 用户退出
"Exited checkpoint selection."
```

---

## 3. 命令底层实现

### 3.1 CheckpointManager（检查点管理）

**位置**: `/src/checkpoint/manager.py`

#### 核心方法

```python
class CheckpointManager:
    def __init__(self, persistence_manager: PersistenceManager):
        self.persistence = persistence_manager

    # ===== 检查点创建 =====
    async def create_checkpoint(
        self,
        execution_id: str,
        step_name: str,
        step_index: int,
        state: dict,
        context: dict,
        variables: dict,
        status: str = "success",
        error: Optional[str] = None
    ) -> Checkpoint:
        """创建新检查点"""
        checkpoint = Checkpoint(
            id=f"ckpt-{execution_id}-{step_index}",
            execution_id=execution_id,
            step_name=step_name,
            step_index=step_index,
            timestamp=datetime.now(),
            state=state,
            context=context,
            variables=variables,
            status=status,
            error=error
        )
        await self.persistence.save_checkpoint(checkpoint.to_dict())
        return checkpoint

    # ===== 检查点加载 =====
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """加载指定检查点"""
        data = await self.persistence.load_checkpoint(checkpoint_id)
        return Checkpoint.from_dict(data) if data else None

    # ===== 检查点列表 =====
    async def list_checkpoints(self, execution_id: str) -> List[Checkpoint]:
        """列出指定执行的所有检查点"""
        checkpoint_ids = await self.persistence.list_checkpoints(execution_id)
        checkpoints = []
        for cp_id in checkpoint_ids:
            cp = await self.load_checkpoint(cp_id)
            if cp: checkpoints.append(cp)
        return sorted(checkpoints, key=lambda x: x.step_index)

    # ===== 检查点删除 =====
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """删除指定检查点"""
        return await self.persistence.delete_checkpoint(checkpoint_id)

    # ===== 获取最后的成功检查点 =====
    async def get_last_successful_checkpoint(
        self,
        execution_id: str,
        before_step: Optional[int] = None
    ) -> Optional[Checkpoint]:
        """获取最后一个成功的检查点"""
        checkpoints = await self.list_checkpoints(execution_id)
        for cp in reversed(checkpoints):
            if cp.status == "success":
                if before_step is None or cp.step_index < before_step:
                    return cp
        return None

    # ===== 格式化历史记录（用于UI）=====
    async def get_formatted_checkpoint_history(self) -> List[Tuple[str, str]]:
        """
        获取格式化为交互式选择器的检查点历史记录。
        返回格式: [(execution_id, display_text), ...]
        """
        try:
            checkpoint_ids = await self.persistence.storage.list("checkpoint")
            if not checkpoint_ids:
                return []

            # 按 execution_id 分组
            checkpoints_by_exec = {}
            for cp_id in checkpoint_ids:
                data = await self.persistence.load_checkpoint(cp_id)
                if data:
                    cp = Checkpoint.from_dict(data)
                    exec_id = cp.execution_id
                    if exec_id not in checkpoints_by_exec:
                        checkpoints_by_exec[exec_id] = []
                    checkpoints_by_exec[exec_id].append(cp)

            # 为每个 execution 创建显示项
            formatted_items = []
            for exec_id in sorted(checkpoints_by_exec.keys(), reverse=True):
                checkpoints = checkpoints_by_exec[exec_id]
                last_cp = checkpoints[-1] if checkpoints else None
                if last_cp:
                    display_text = f"Restore {exec_id}\n  Step: {last_cp.step_name}"
                    formatted_items.append((exec_id, display_text))

            return formatted_items
        except:
            return []
```

### 3.2 Checkpoint 数据结构

**位置**: `/src/checkpoint/types.py`

```python
@dataclass
class Checkpoint:
    id: str                      # 检查点ID: "ckpt-{execution_id}-{step_index}"
    execution_id: str            # 执行ID
    step_name: str               # 步骤名称
    step_index: int              # 步骤序号
    timestamp: datetime          # 创建时间
    
    # 状态数据
    state: Dict                  # 当前Agent状态
    context: Dict                # 执行上下文
    variables: Dict              # 局部变量
    
    # 元数据
    status: str = "success"      # success/failed/pending
    error: Optional[str] = None  # 错误信息
    metadata: Dict = field(default_factory=dict)  # 其他元数据

    def to_dict(self) -> Dict:
        """序列化为字典"""
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "step_name": self.step_name,
            "step_index": self.step_index,
            "timestamp": self.timestamp.isoformat(),
            "state": self.state,
            "context": self.context,
            "variables": self.variables,
            "status": self.status,
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Checkpoint":
        """从字典反序列化"""
        return cls(
            id=data["id"],
            execution_id=data["execution_id"],
            step_name=data["step_name"],
            step_index=data["step_index"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            state=data["state"],
            context=data["context"],
            variables=data["variables"],
            status=data.get("status", "success"),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )
```

### 3.3 执行恢复管理

**位置**: `/src/checkpoint/recovery.py`

```python
class ExecutionRecovery:
    def __init__(self, checkpoint_manager: CheckpointManager, 
                 persistence_manager: PersistenceManager):
        self.checkpoint_manager = checkpoint_manager
        self.persistence = persistence_manager

    # ===== 从检查点恢复 =====
    async def resume_from_checkpoint(
        self,
        checkpoint_id: str,
        agent_instance: Any
    ) -> ExecutionResult:
        """从检查点恢复执行"""
        try:
            checkpoint = await self.checkpoint_manager.load_checkpoint(checkpoint_id)
            if not checkpoint:
                return ExecutionResult(
                    success=False, 
                    error=f"Checkpoint {checkpoint_id} not found"
                )

            agent_instance.restore_state_from_checkpoint(checkpoint)
            return ExecutionResult(
                success=True, 
                output="Agent state restored from checkpoint."
            )
        except Exception as e:
            return ExecutionResult(
                success=False, 
                error=f"Recovery failed: {e}"
            )

    # ===== 从步骤重试 =====
    async def retry_from_step(
        self,
        execution_id: str,
        step_index: int,
        agent_instance: Any,
        max_retries: int = 3
    ) -> ExecutionResult:
        """从指定步骤之前的检查点重试"""
        last_successful_cp = await self.checkpoint_manager.get_last_successful_checkpoint(
            execution_id, before_step=step_index
        )
        if last_successful_cp:
            return await self.resume_from_checkpoint(
                last_successful_cp.id, 
                agent_instance
            )
        else:
            return ExecutionResult(
                success=False, 
                error=f"No successful checkpoint found before step {step_index}"
            )

    # ===== 回滚到检查点 =====
    async def rollback_to_checkpoint(self, checkpoint_id: str) -> bool:
        """回滚到指定检查点（占位符）"""
        return True
```

### 3.4 持久化管理

**位置**: `/src/persistence/manager.py`

```python
class PersistenceManager:
    def __init__(self, storage: BaseStorage):
        self.storage = storage

    # ===== 检查点持久化 =====
    async def save_checkpoint(self, checkpoint_data: Dict) -> str:
        """保存检查点"""
        return await self.storage.save(
            category="checkpoint", 
            key=checkpoint_data["id"], 
            data=checkpoint_data
        )

    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict]:
        """加载检查点"""
        return await self.storage.load("checkpoint", checkpoint_id)

    async def list_checkpoints(self, execution_id: str) -> List[str]:
        """列出指定执行的所有检查点"""
        all_checkpoints = await self.storage.list("checkpoint")
        return [cp for cp in all_checkpoints 
                if cp.startswith(f"ckpt-{execution_id}")]

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """删除检查点"""
        return await self.storage.delete("checkpoint", checkpoint_id)
```

---

## 4. 存储层实现

### 4.1 JSON 存储

**位置**: `/src/persistence/storage.py`

```python
class JSONStorage(BaseStorage):
    def __init__(self, project_name: str, 
                 base_dir: str = "~/.cache/tiny-claude-code"):
        base_path = Path(base_dir).expanduser()
        self.storage_dir = base_path / "projects" / project_name / "persistence"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, category: str, key: str, data: Dict) -> str:
        """保存数据到JSON文件（含文件锁）"""
        category_dir = self.storage_dir / category
        category_dir.mkdir(exist_ok=True)
        file_path = category_dir / f"{key}.json"
        lock_path = category_dir / f"{key}.json.lock"

        if FILELOCK_AVAILABLE:
            lock = FileLock(lock_path, timeout=5)
            try:
                with lock:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, 
                                 indent=2, default=json_serializer)
            except Timeout:
                raise RuntimeError(f"Could not acquire lock for {file_path}")
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, 
                         indent=2, default=json_serializer)
        return str(file_path)

    async def load(self, category: str, key: str) -> Optional[Dict]:
        """从JSON文件加载"""
        file_path = self.storage_dir / category / f"{key}.json"
        if not file_path.exists():
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def delete(self, category: str, key: str) -> bool:
        """删除JSON文件"""
        file_path = self.storage_dir / category / f"{key}.json"
        lock_path = self.storage_dir / category / f"{key}.json.lock"
        if file_path.exists():
            file_path.unlink()
            if Path(lock_path).exists():
                Path(lock_path).unlink()
            return True
        return False

    async def list(self, category: str) -> List[str]:
        """列出指定类别的所有数据"""
        category_dir = self.storage_dir / category
        if not category_dir.exists():
            return []
        return [f.stem for f in category_dir.glob("*.json")]
```

#### 存储文件结构

```
~/.cache/tiny-claude-code/
└── projects/
    └── {project_name}/
        └── persistence/
            ├── checkpoint/
            │   ├── ckpt-exec-001-0.json
            │   ├── ckpt-exec-001-1.json
            │   └── ckpt-exec-002-0.json
            ├── conversation/
            │   └── conv-auto-save-123.json
            ├── history/
            │   └── execution-001.json
            ├── session/
            │   └── session-456.json
            └── config/
                └── settings.json
```

### 4.2 SQLite 存储

**位置**: `/src/persistence/storage.py` （部分展示）

```python
class SQLiteStorage(BaseStorage):
    def __init__(self, project_name: str, 
                 base_dir: str = "~/.cache/tiny-claude-code"):
        base_path = Path(base_dir).expanduser()
        self.db_path = base_path / "projects" / project_name / "persistence.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS persistence (
            category TEXT NOT NULL,
            key TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (category, key)
        )
        """)
        conn.commit()
        conn.close()
    
    # ... 其他方法实现
```

---

## 5. Agent 集成

**位置**: `/src/agents/enhanced_agent.py`

### 初始化

```python
class EnhancedAgent:
    def __init__(self, ...):
        # ... 其他初始化代码
        
        # 创建持久化管理器
        project_name = Path.cwd().name
        storage = JSONStorage(project_name)
        self.persistence = PersistenceManager(storage)
        
        # 创建检查点管理器
        self.checkpoint_manager = CheckpointManager(self.persistence)
        
        # 创建恢复管理器
        self.execution_recovery = ExecutionRecovery(
            self.checkpoint_manager, 
            self.persistence
        )
```

### 创建检查点

```python
async def run_with_checkpoints(self, query: str):
    """运行并在各步骤保存检查点"""
    
    # ... 执行步骤 ...
    
    # 在关键步骤后创建检查点
    await self.checkpoint_manager.create_checkpoint(
        execution_id=execution_id,
        step_name="step_name",
        step_index=1,
        state=self.state_manager.get_state(),
        context=self.get_context(),
        variables=self.variables,
        status="success"
    )
```

### 恢复状态

```python
def restore_state_from_checkpoint(self, checkpoint: Checkpoint):
    """从检查点恢复状态"""
    try:
        self.state_manager.restore_state(checkpoint.state)
        # ... 恢复其他状态 ...
    except Exception as e:
        logger.error(f"Failed to restore state: {e}")
```

### 处理错误恢复

```python
# 当发生错误时
except Exception as e:
    # 尝试从检查点恢复
    recovery_result = await self.execution_recovery.retry_from_step(
        execution_id=execution_id,
        step_index=current_step_index,
        agent_instance=self,
        max_retries=3
    )
    if recovery_result.success:
        feedback.add_info("Attempting recovery from last checkpoint...")
```

---

## 6. 使用示例

### 6.1 创建检查点

```python
# 创建检查点
checkpoint = await checkpoint_manager.create_checkpoint(
    execution_id="exec-123",
    step_name="data_processing",
    step_index=2,
    state={"phase": "processing", "processed_items": 100},
    context={"messages": [...], "user_id": "user-456"},
    variables={"total": 1000, "batch_size": 50},
    status="success"
)
# 返回: Checkpoint(id="ckpt-exec-123-2", ...)
```

### 6.2 加载检查点

```python
# 加载指定检查点
checkpoint = await checkpoint_manager.load_checkpoint("ckpt-exec-123-2")
if checkpoint:
    print(f"Loaded: {checkpoint.step_name} at {checkpoint.timestamp}")
    # 恢复Agent状态
    await agent.restore_state_from_checkpoint(checkpoint)
```

### 6.3 列出检查点

```python
# 列出执行的所有检查点
checkpoints = await checkpoint_manager.list_checkpoints("exec-123")
for cp in checkpoints:
    print(f"Step {cp.step_index}: {cp.step_name} [{cp.status}]")
    
# 输出:
# Step 0: data_fetch [success]
# Step 1: data_validation [success]
# Step 2: data_processing [success]
# Step 3: api_call [failed]
```

### 6.4 获取最后的成功检查点

```python
# 获取最后一个成功检查点
last_success = await checkpoint_manager.get_last_successful_checkpoint("exec-123")
if last_success:
    print(f"Last success: Step {last_success.step_index}")
    # 从此处恢复
```

### 6.5 重试从检查点

```python
# 从检查点重试
result = await agent.execution_recovery.retry_from_step(
    execution_id="exec-123",
    step_index=3,  # 重试第3步
    agent_instance=agent,
    max_retries=3
)

if result.success:
    print("Recovery successful!")
else:
    print(f"Recovery failed: {result.error}")
```

### 6.6 命令行交互

```bash
# 启动应用并使用checkpoint命令
python -m src.main

# 在提示符下输入：
> /checkpoint

# 输出（交互式选择器）：
# Checkpoints
# 1) (current)
#    Do not restore, continue with the current session.
# 2) Restore exec-123
#    Step: data_processing
# 3) Restore exec-124
#    Step: api_call

# 用户选择选项 2，返回：
# Selected execution to restore: exec-123. (Resume logic not yet fully implemented).

# 或使用别名
> /rewind
> /restore
```

---

## 7. 单元测试示例

**位置**: `/tests/unit/test_persistence_system.py`

```python
@pytest.mark.asyncio
async def test_create_and_load_checkpoint():
    """测试检查点创建和加载"""
    storage = JSONStorage(project_name="test_project")
    persistence = PersistenceManager(storage)
    checkpoint_manager = CheckpointManager(persistence)
    
    # 创建检查点
    cp = await checkpoint_manager.create_checkpoint(
        execution_id="exec-123",
        step_name="test_step",
        step_index=1,
        state={"agent_state": "thinking"},
        context={"messages": []},
        variables={"var1": "value1"}
    )
    
    # 加载检查点
    loaded_cp = await checkpoint_manager.load_checkpoint(cp.id)
    assert loaded_cp is not None
    assert loaded_cp.execution_id == "exec-123"
    assert loaded_cp.step_index == 1
    assert loaded_cp.state == {"agent_state": "thinking"}

@pytest.mark.asyncio
async def test_list_checkpoints():
    """测试检查点列表"""
    storage = JSONStorage(project_name="test_project")
    persistence = PersistenceManager(storage)
    checkpoint_manager = CheckpointManager(persistence)
    
    # 创建多个检查点
    await checkpoint_manager.create_checkpoint("exec-1", "step1", 1, {}, {}, {})
    await checkpoint_manager.create_checkpoint("exec-1", "step2", 2, {}, {}, {})
    
    # 列出检查点
    checkpoints = await checkpoint_manager.list_checkpoints("exec-1")
    assert len(checkpoints) == 2
    assert checkpoints[0].step_index == 1
    assert checkpoints[1].step_index == 2

@pytest.mark.asyncio
async def test_get_last_successful_checkpoint():
    """测试获取最后的成功检查点"""
    storage = JSONStorage(project_name="test_project")
    persistence = PersistenceManager(storage)
    checkpoint_manager = CheckpointManager(persistence)
    
    # 创建多个不同状态的检查点
    await checkpoint_manager.create_checkpoint(
        "exec-1", "step1", 1, {}, {}, {}, status="success"
    )
    await checkpoint_manager.create_checkpoint(
        "exec-1", "step2", 2, {}, {}, {}, status="success"
    )
    await checkpoint_manager.create_checkpoint(
        "exec-1", "step3", 3, {}, {}, {}, status="failed"
    )
    
    # 获取最后成功的
    last_success = await checkpoint_manager.get_last_successful_checkpoint("exec-1")
    assert last_success.step_index == 2
```

---

## 8. 关键特性总结

| 特性 | 说明 |
|------|------|
| **命令名** | `checkpoint` (别名: `rewind`, `restore`) |
| **命令参数** | 无参数，通过交互式选择器选择 |
| **返回类型** | 字符串消息或交互式选择 |
| **ID格式** | `ckpt-{execution_id}-{step_index}` |
| **存储位置** | `~/.cache/tiny-claude-code/projects/{project_name}/persistence/` |
| **支持的状态** | `success`, `failed`, `pending` |
| **存储后端** | JSON (文件锁) + SQLite (可选) |
| **并发安全** | 文件锁支持 (filelock) |
| **序列化** | JSON + ISO8601 datetime |
| **恢复策略** | 从最后成功检查点恢复 |

---

## 9. 文件路径速查表

| 文件 | 位置 |
|------|------|
| CheckpointCommand | `/src/commands/checkpoint_commands.py` |
| CheckpointManager | `/src/checkpoint/manager.py` |
| Checkpoint 类型 | `/src/checkpoint/types.py` |
| ExecutionRecovery | `/src/checkpoint/recovery.py` |
| PersistenceManager | `/src/persistence/manager.py` |
| 存储后端 | `/src/persistence/storage.py` |
| 命令注册 | `/src/commands/__init__.py` |
| Agent 集成 | `/src/agents/enhanced_agent.py` |
| 单元测试 | `/tests/unit/test_persistence_system.py` |
| 设计文档 | `/docs/features/v0.0.1/p6-checkpoint-persistence.md` |

