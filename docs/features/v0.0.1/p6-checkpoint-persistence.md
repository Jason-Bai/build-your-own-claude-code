# 功能：P6 - Checkpoint 持久化（Checkpoint Persistence）

**日期**: 待实现
**优先级**: P1 🟡
**难度**: ⭐⭐⭐
**预计周期**: 1 周
**状态**: 📋 未开始
**架构设计**: ✅ 已完成（基于架构分析）

---

## 核心改进（v1.0）

相比原始设计，本版本增加了：

✅ **PersistenceManager** - 统一的持久化管理器
- 支持多种存储后端（JSON、SQLite、云存储）
- 类别化数据管理（Checkpoint、Conversation、History、Config）
- 解耦检查点逻辑与存储实现

✅ **架构演进路径** - 平滑的迁移方案
- 第1步：引入 PersistenceManager 核心
- 第2步：集成 Checkpoint 系统
- 第3步：支持多后端

✅ **最佳实践** - 基于项目现状
- 保留现有 ConversationPersistence API
- 新功能直接使用 PersistenceManager
- 无需改动现有代码

---

## 概述

实现一个**检查点（Checkpoint）系统**，能够在长流程执行中保存中间状态，支持暂停、恢复、重试和故障恢复，提供流程调试和故障恢复能力。

---

## 问题描述

### 当前状况

当前系统的任务执行是一次性的，无法中断或恢复：

```python
# ❌ 无状态保存，无法恢复
result = agent.run(long_query)  # 如果失败，无法从中间点恢复
```

**限制**：
- 长流程执行失败需要从头开始
- 无法暂停和恢复执行
- 无法调试中间步骤
- 无法处理部分成功的情况

### 期望改进

需要一个**检查点系统**，能够：
- 保存执行中间状态
- 支持从检查点恢复
- 支持状态回滚
- 记录完整的执行历史
- 支持条件式重试

---

## 设计方案

### 核心架构

```
长流程执行
  ├─ Step 1: 数据获取
  │  └─ [Checkpoint] 保存数据
  ├─ Step 2: 数据处理
  │  └─ [Checkpoint] 保存处理结果
  ├─ Step 3: 调用 API
  │  └─ [Checkpoint] 保存 API 响应
  ├─ Step 4: 结果验证
  │  └─ [Checkpoint] 保存验证结果
  └─ Step 5: 返回结果
     └─ [Checkpoint] 标记完成

执行失败时：
  从最近的成功检查点恢复
  ├─ 跳过已完成的步骤
  ├─ 恢复上下文和状态
  └─ 重新执行失败的步骤
```

### 检查点数据结构

```python
@dataclass
class Checkpoint:
    """检查点"""

    id: str                          # 检查点 ID
    execution_id: str                # 执行 ID
    step_name: str                   # 步骤名称
    step_index: int                  # 步骤序号
    timestamp: datetime              # 创建时间

    # 状态数据
    state: dict                      # 当前状态
    context: dict                    # 执行上下文
    variables: dict                  # 局部变量

    # 元数据
    status: str                      # success/failed/pending
    error: Optional[str]             # 错误信息
    metadata: dict                   # 其他元数据
```

### 执行历史

```python
@dataclass
class ExecutionHistory:
    """执行历史"""

    execution_id: str                # 执行 ID
    start_time: datetime
    end_time: Optional[datetime]

    steps: List[StepRecord]          # 各步骤记录
    checkpoints: List[Checkpoint]    # 检查点列表

    total_duration: float            # 总耗时
    status: str                      # success/failed/paused

    # 恢复信息
    recovery_attempts: int           # 恢复次数
    last_checkpoint: Optional[Checkpoint]  # 最后的检查点
```

### 状态存储

```
execution-{id}/
├── metadata.json          # 执行元数据
├── checkpoints/
│  ├── step-1.json        # Step 1 检查点
│  ├── step-2.json        # Step 2 检查点
│  └── step-3.json        # Step 3 检查点
├── history.json          # 执行历史
└── logs/
   └── execution.log      # 执行日志
```

---

## 实现细节

### 核心组件

#### 0. PersistenceManager（统一持久化管理器）🎯 **架构核心**

```python
# src/persistence/manager.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

class StorageBackend(ABC):
    """存储后端抽象接口（支持不同存储实现）"""

    @abstractmethod
    async def save(self, category: str, key: str, data: Dict) -> str:
        """保存数据到存储"""
        pass

    @abstractmethod
    async def load(self, category: str, key: str) -> Optional[Dict]:
        """从存储加载数据"""
        pass

    @abstractmethod
    async def delete(self, category: str, key: str) -> bool:
        """删除数据"""
        pass

    @abstractmethod
    async def list(self, category: str) -> List[str]:
        """列出指定类别的所有数据"""
        pass


class PersistenceManager:
    """统一的持久化管理器

    职责：
    - 统一管理所有需要持久化的数据（对话、检查点、配置、状态）
    - 支持多种存储后端（JSON、SQLite、云存储等）
    - 提供类别化的数据保存和加载接口
    """

    def __init__(self, backend: StorageBackend):
        self.backend = backend

    # ======== Checkpoint 相关 ========
    async def save_checkpoint(self, checkpoint: Checkpoint) -> str:
        """保存检查点"""
        return await self.backend.save(
            category="checkpoint",
            key=checkpoint.id,
            data=checkpoint.to_dict()
        )

    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """加载检查点"""
        data = await self.backend.load("checkpoint", checkpoint_id)
        return Checkpoint.from_dict(data) if data else None

    async def list_checkpoints(self, execution_id: str) -> List[str]:
        """列出某个执行的所有检查点"""
        all_checkpoints = await self.backend.list("checkpoint")
        return [
            cp for cp in all_checkpoints
            if cp.startswith(f"ckpt-{execution_id}")
        ]

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """删除检查点"""
        return await self.backend.delete("checkpoint", checkpoint_id)

    # ======== Conversation 相关 ========
    async def save_conversation(self, conv_id: str, conversation: Dict) -> str:
        """保存对话（兼容现有 API）"""
        return await self.backend.save(
            category="conversation",
            key=conv_id,
            data=conversation
        )

    async def load_conversation(self, conv_id: str) -> Optional[Dict]:
        """加载对话"""
        return await self.backend.load("conversation", conv_id)

    async def list_conversations(self) -> List[str]:
        """列出所有对话"""
        return await self.backend.list("conversation")

    async def delete_conversation(self, conv_id: str) -> bool:
        """删除对话"""
        return await self.backend.delete("conversation", conv_id)

    # ======== Execution History 相关 ========
    async def save_history(self, execution_id: str, history: Dict) -> str:
        """保存执行历史"""
        return await self.backend.save(
            category="history",
            key=execution_id,
            data=history
        )

    async def load_history(self, execution_id: str) -> Optional[Dict]:
        """加载执行历史"""
        return await self.backend.load("history", execution_id)

    # ======== 配置相关（可扩展） ========
    async def save_config(self, config_name: str, config: Dict) -> str:
        """保存配置"""
        return await self.backend.save(
            category="config",
            key=config_name,
            data=config
        )

    async def load_config(self, config_name: str) -> Optional[Dict]:
        """加载配置"""
        return await self.backend.load("config", config_name)

    # ======== Agent 状态相关（P6+ 功能） ========
    async def save_agent_state(self, agent_id: str, state: Dict) -> str:
        """保存 Agent 状态快照"""
        return await self.backend.save(
            category="agent_state",
            key=agent_id,
            data=state
        )

    async def load_agent_state(self, agent_id: str) -> Optional[Dict]:
        """加载 Agent 状态"""
        return await self.backend.load("agent_state", agent_id)


class JSONBackend(StorageBackend):
    """JSON 文件存储后端（当前实现）"""

    def __init__(self, storage_dir: str = ".cache/claude-code/persistence"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, category: str, key: str, data: Dict) -> str:
        """保存数据到 JSON 文件"""
        category_dir = self.storage_dir / category
        category_dir.mkdir(exist_ok=True)

        file_path = category_dir / f"{key}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(file_path)

    async def load(self, category: str, key: str) -> Optional[Dict]:
        """从 JSON 文件加载数据"""
        file_path = self.storage_dir / category / f"{key}.json"
        if not file_path.exists():
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def delete(self, category: str, key: str) -> bool:
        """删除 JSON 文件"""
        file_path = self.storage_dir / category / f"{key}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    async def list(self, category: str) -> List[str]:
        """列出指定类别的所有文件"""
        category_dir = self.storage_dir / category
        if not category_dir.exists():
            return []

        return [f.stem for f in category_dir.glob("*.json")]


class SQLiteBackend(StorageBackend):
    """SQLite 存储后端（未来可选实现）"""

    def __init__(self, db_path: str = ".cache/claude-code/persistence.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS persistence (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            key TEXT NOT NULL,
            data JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, key)
        )
        """)

        conn.commit()
        conn.close()

    async def save(self, category: str, key: str, data: Dict) -> str:
        """保存数据到 SQLite"""
        import sqlite3
        import json as json_lib

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        unique_id = f"{category}:{key}"
        cursor.execute("""
        INSERT OR REPLACE INTO persistence (id, category, key, data, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (unique_id, category, key, json_lib.dumps(data)))

        conn.commit()
        conn.close()

        return unique_id

    async def load(self, category: str, key: str) -> Optional[Dict]:
        """从 SQLite 加载数据"""
        import sqlite3
        import json as json_lib

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT data FROM persistence WHERE category=? AND key=?",
            (category, key)
        )

        row = cursor.fetchone()
        conn.close()

        return json_lib.loads(row[0]) if row else None

    async def delete(self, category: str, key: str) -> bool:
        """从 SQLite 删除数据"""
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM persistence WHERE category=? AND key=?",
            (category, key)
        )

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return deleted

    async def list(self, category: str) -> List[str]:
        """列出指定类别的所有数据"""
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT key FROM persistence WHERE category=?",
            (category,)
        )

        keys = [row[0] for row in cursor.fetchall()]
        conn.close()

        return keys
```

**设计优势：**

1. ✅ **统一接口**：所有持久化操作通过 `PersistenceManager`
2. ✅ **存储无关**：支持 JSON、SQLite、云存储等（实现 `StorageBackend`）
3. ✅ **易于扩展**：添加新的持久化需求只需调用相应方法
4. ✅ **类别管理**：数据按类别组织，便于维护和迁移
5. ✅ **向后兼容**：现有 `ConversationPersistence` 可平滑过渡

#### 1. CheckpointManager（检查点管理器）

```python
class CheckpointManager:
    """管理检查点的保存和加载

    依赖 PersistenceManager 处理数据持久化
    """

    def __init__(self, persistence_manager: PersistenceManager):
        self.persistence = persistence_manager

    async def create_checkpoint(
        self,
        execution_id: str,
        step_name: str,
        step_index: int,
        state: dict,
        context: dict,
        variables: dict
    ) -> Checkpoint:
        """创建并保存检查点"""
        checkpoint = Checkpoint(
            id=f"ckpt-{execution_id}-{step_index}",
            execution_id=execution_id,
            step_name=step_name,
            step_index=step_index,
            timestamp=datetime.now(),
            state=state,
            context=context,
            variables=variables,
            status="success"
        )

        # 通过 PersistenceManager 保存
        await self.persistence.save_checkpoint(checkpoint)
        return checkpoint

    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """加载检查点"""
        # 通过 PersistenceManager 加载
        return await self.persistence.load_checkpoint(checkpoint_id)

    async def list_checkpoints(self, execution_id: str) -> List[Checkpoint]:
        """列出所有检查点"""
        checkpoint_ids = await self.persistence.list_checkpoints(execution_id)
        checkpoints = []

        for cp_id in checkpoint_ids:
            cp = await self.load_checkpoint(cp_id)
            if cp:
                checkpoints.append(cp)

        return sorted(checkpoints, key=lambda x: x.step_index)

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """删除检查点"""
        return await self.persistence.delete_checkpoint(checkpoint_id)

    async def get_last_successful_checkpoint(
        self,
        execution_id: str,
        before_step: Optional[int] = None
    ) -> Optional[Checkpoint]:
        """获取最后一个成功的检查点"""
        checkpoints = await self.list_checkpoints(execution_id)

        # 按步骤倒序，找最后一个成功的
        for cp in reversed(checkpoints):
            if cp.status == "success":
                if before_step is None or cp.step_index < before_step:
                    return cp

        return None
```

**与 PersistenceManager 的关系：**
- ✅ CheckpointManager 专注于检查点逻辑（创建、查询、恢复）
- ✅ PersistenceManager 负责实际的存储操作（JSON/SQLite）
- ✅ 解耦清晰：更换存储后端只需改 PersistenceManager

#### 2. ExecutionRecovery（执行恢复）
```python
class ExecutionRecovery:
    """处理执行恢复"""

    async def resume_from_checkpoint(
        self,
        checkpoint_id: str,
        remaining_steps: List[Step]
    ) -> ExecutionResult:
        """从检查点恢复执行"""
        # 加载检查点
        checkpoint = await self.checkpoint_manager.load_checkpoint(
            checkpoint_id
        )

        # 恢复上下文
        context = Context.from_checkpoint(checkpoint)

        # 执行剩余步骤
        return await self._execute_steps(
            steps=remaining_steps,
            context=context,
            start_from_index=checkpoint.step_index + 1
        )

    async def retry_from_step(
        self,
        execution_id: str,
        step_index: int,
        max_retries: int = 3
    ) -> ExecutionResult:
        """重试从某个步骤开始"""
        # 获取上一个成功的检查点
        checkpoint = await self._get_last_successful_checkpoint(
            execution_id,
            before_step=step_index
        )

        # 从检查点恢复
        return await self.resume_from_checkpoint(
            checkpoint.id,
            remaining_steps=self._get_remaining_steps(step_index)
        )

    async def rollback_to_checkpoint(
        self,
        checkpoint_id: str
    ):
        """回滚到指定检查点"""
        pass
```

#### 3. ExecutionTracker（执行跟踪）
```python
class ExecutionTracker:
    """跟踪执行过程"""

    async def track_step(
        self,
        execution_id: str,
        step: Step,
        result: Any,
        duration: float
    ):
        """记录步骤执行"""
        record = StepRecord(
            execution_id=execution_id,
            step_name=step.name,
            step_index=step.index,
            status="success",
            result=result,
            duration=duration,
            timestamp=datetime.now()
        )
        await self.history_manager.record_step(record)

    async def track_error(
        self,
        execution_id: str,
        step: Step,
        error: Exception
    ):
        """记录错误"""
        record = StepRecord(
            execution_id=execution_id,
            step_name=step.name,
            step_index=step.index,
            status="failed",
            error=str(error),
            timestamp=datetime.now()
        )
        await self.history_manager.record_step(record)

    async def get_execution_history(
        self,
        execution_id: str
    ) -> ExecutionHistory:
        """获取执行历史"""
        pass
```

### 文件修改

- `src/checkpoint/manager.py` - 检查点管理器
- `src/checkpoint/recovery.py` - 恢复逻辑
- `src/checkpoint/tracker.py` - 执行跟踪
- `src/checkpoint/storage.py` - 存储后端
- `src/agents/enhanced_agent.py` - 集成检查点

---

## 架构演进路径（关键）

### 背景：当前持久化状态

当前项目有 `src/persistence.py` 处理对话保存，但：
- ❌ 持久化逻辑分散
- ❌ 只支持对话，不支持其他需求
- ⚠️ 难以扩展到 Checkpoint 和 Agent 状态

### P6 实施分三步演进

#### **第 1 步：引入 PersistenceManager（P6 起始）**

```python
# 新建文件：src/persistence/manager.py
# 包含：StorageBackend 接口 + JSONBackend 实现

# 修改：src/persistence.py
class ConversationPersistence:
    """旧的 API，保留向后兼容"""
    def __init__(self):
        self.manager = PersistenceManager(JSONBackend())

    def save_conversation(self, conv_id, messages, ...):
        # 委托给 PersistenceManager
        return self.manager.save_conversation(conv_id, {...})

    def load_conversation(self, conv_id):
        # 委托给 PersistenceManager
        return self.manager.load_conversation(conv_id)
```

**优势：**
- ✅ 现有代码无需改动
- ✅ 新功能可直接使用 PersistenceManager
- ✅ 逐步迁移旧代码

#### **第 2 步：集成 Checkpoint 系统（P6 中期）**

```python
# 新建文件：src/checkpoint/manager.py
# 使用 PersistenceManager 保存检查点

# 修改：src/agents/enhanced_agent.py
class EnhancedAgent:
    def __init__(self, ...):
        self.persistence = PersistenceManager(JSONBackend())
        self.checkpoint_manager = CheckpointManager(self.persistence)

    async def run_with_checkpoints(self, query):
        """支持检查点的执行"""
        execution_id = generate_id()

        for step_idx, step in enumerate(self._execution_steps):
            try:
                result = await step.execute()

                # 每步后保存检查点
                await self.checkpoint_manager.create_checkpoint(
                    execution_id=execution_id,
                    step_name=step.name,
                    step_index=step_idx,
                    state=result,
                    context=self.context_manager.get_context_info(),
                    variables=locals()
                )

            except Exception as e:
                # 失败时触发恢复
                recovery = ExecutionRecovery(self.checkpoint_manager)
                result = await recovery.retry_from_step(
                    execution_id=execution_id,
                    step_index=step_idx
                )
```

#### **第 3 步：多后端支持（P6 完成）**

```python
# 新建文件：src/persistence/backends/sqlite.py
# 实现 SQLiteBackend

# 用户可选择存储后端
persistence = PersistenceManager(
    backend=SQLiteBackend(".cache/claude-code/data.db")
)

# 或使用 JSON（默认）
persistence = PersistenceManager(
    backend=JSONBackend(".cache/claude-code")
)

# 或使用云存储（未来）
persistence = PersistenceManager(
    backend=S3Backend("my-bucket")
)
```

### 迁移时间表

| 阶段 | 时间 | 工作 |
|------|------|------|
| **现在** | - | 项目现状：ConversationPersistence + 359 tests |
| **P6 开始** | Week 1 | 实现 PersistenceManager + StorageBackend |
| **P6 中期** | Week 2 | 实现 CheckpointManager + ExecutionRecovery |
| **P6 完成** | Week 3 | 集成到 EnhancedAgent + SQLite 后端 |

---

### 执行流程

```
开始执行
  ↓
[Step 1] 获取数据
  ├─ 执行步骤
  ├─ 保存 Checkpoint-1
  └─ 记录历史
  ↓
[Step 2] 处理数据
  ├─ 执行步骤
  ├─ 保存 Checkpoint-2
  └─ 记录历史
  ↓
[Step 3] 调用 API (失败 ❌)
  ├─ 执行失败
  ├─ 记录错误
  └─ 保存到 Checkpoint-2
  ↓
恢复流程
  ├─ 从 Checkpoint-2 加载状态
  ├─ 跳过 Step 1-2（已完成）
  ├─ 重试 Step 3
  └─ 继续执行
  ↓
执行完成
```

### 检查点保存流程

```python
# 在每个步骤后创建检查点
async def execute_with_checkpoints(steps):
    execution_id = generate_id()
    history = ExecutionHistory(execution_id=execution_id)

    for idx, step in enumerate(steps):
        try:
            # 执行步骤
            result = await step.execute()

            # 保存检查点
            checkpoint = await checkpoint_manager.create_checkpoint(
                execution_id=execution_id,
                step_name=step.name,
                step_index=idx,
                state=result,
                context=current_context,
                variables=local_vars
            )

            # 记录历史
            await tracker.track_step(
                execution_id=execution_id,
                step=step,
                result=result,
                duration=step.duration
            )

        except Exception as e:
            # 记录错误
            await tracker.track_error(
                execution_id=execution_id,
                step=step,
                error=e
            )

            # 可选：自动重试
            if should_retry(e):
                result = await recovery.retry_from_step(
                    execution_id=execution_id,
                    step_index=idx
                )
```

---

## 应用场景

### 场景 1: 长流程恢复
```
执行一个 5 步的复杂任务：
Step 1: 获取数据 ✓
Step 2: 验证数据 ✓
Step 3: 调用外部 API (超时)
  → 从 Step 2 的检查点恢复
  → 重试 Step 3 (成功)
Step 4: 处理结果 ✓
Step 5: 返回结果 ✓
```

### 场景 2: 调试中间步骤
```
查看执行历史：
[Checkpoint-1] Step 1: 获取数据
  - 输入: {...}
  - 输出: {...}
  - 耗时: 1.2s

[Checkpoint-2] Step 2: 验证数据
  - 输入: {...}
  - 输出: {...}
  - 耗时: 0.3s

使用 Checkpoint-2 的数据调试 Step 3
```

### 场景 3: 故障自动恢复
```
检测到 Step 3 失败
  → 自动从 Checkpoint-2 恢复
  → 使用指数退避重试
  → 最多重试 3 次
  → 如果仍失败，标记为失败并通知
```

---

## 存储策略

### 本地存储
```
~/.cache/claude-code/executions/
├── execution-20250113-001/
│  ├── metadata.json
│  ├── checkpoints/
│  │  ├── 1.json
│  │  ├── 2.json
│  │  └── 3.json
│  └── history.json
└── execution-20250113-002/
```

### 数据库存储
```sql
CREATE TABLE checkpoints (
    id VARCHAR(255) PRIMARY KEY,
    execution_id VARCHAR(255),
    step_name VARCHAR(255),
    step_index INT,
    state LONGBLOB,
    context LONGBLOB,
    variables LONGBLOB,
    created_at TIMESTAMP
);

CREATE TABLE execution_history (
    id VARCHAR(255) PRIMARY KEY,
    execution_id VARCHAR(255),
    step_name VARCHAR(255),
    status VARCHAR(50),
    duration FLOAT,
    result LONGBLOB,
    error TEXT,
    created_at TIMESTAMP
);
```

---

## 测试验证

### 测试用例

#### 1. 检查点保存
```python
# 执行步骤并验证检查点已保存
execution_id = await execute_with_checkpoints(steps)
checkpoints = await manager.list_checkpoints(execution_id)
assert len(checkpoints) == len(steps)
```

#### 2. 检查点恢复
```python
# 从检查点恢复并验证结果
result = await recovery.resume_from_checkpoint(
    checkpoint_id="ckpt-exec-001-2",
    remaining_steps=steps[3:]
)
assert result.success
```

#### 3. 错误恢复
```python
# 模拟错误并测试恢复
execution_id = await execute_with_checkpoints_and_errors(steps)
assert history.recovery_attempts > 0
assert history.status == "success"
```

#### 4. 历史查询
```python
# 查询执行历史
history = await tracker.get_execution_history(execution_id)
assert len(history.steps) == len(steps)
assert history.total_duration > 0
```

---

## 性能影响

### 评估

- **检查点保存**: ~10-50ms（取决于状态大小）
- **检查点加载**: ~5-20ms
- **存储空间**: 每个检查点 ~1-10KB
- **整体开销**: ~5-10% 性能损耗

### 优化策略

- 增量保存（仅保存变化的状态）
- 压缩存储
- 异步保存
- 定期清理过期检查点

---

## 相关资源

- **数据库事务**: https://en.wikipedia.org/wiki/Database_transaction
- **故障恢复**: https://en.wikipedia.org/wiki/Failure_recovery
- **检查点技术**: https://en.wikipedia.org/wiki/Application_checkpointing

---

## 常见问题

### Q: 如何管理检查点存储大小？
**A**: 设置过期时间和最大数量限制，自动清理旧检查点。

### Q: 检查点可以跨会话使用吗？
**A**: 可以，检查点持久化存储，支持跨会话恢复。

### Q: 如何处理无法恢复的状态？
**A**: 标记为失败，通知用户，提供手动干预选项。

### Q: 性能开销有多大？
**A**: 通常 5-10% 性能损耗，可通过异步保存进一步优化。

---

**实现者**: 待安排
**状态**: 📋 未开始
**依赖**: Phase 1 (Hooks 系统)
**相关 Phase**: Phase 4 (条件路由)
