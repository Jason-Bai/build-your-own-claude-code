# 功能：P6 - Checkpoint 持久化（Checkpoint Persistence）v2

**日期**: 待实现
**优先级**: P1 🟡
**难度**: ⭐⭐⭐
**预计周期**: 1 周
**状态**: 📋 未开始
**架构设计**: ✅ 已完成（v2）

---

## 核心改进（v2.0）

相比 v1.0 版本，本版本增加了：

✅ **增强的存储后端**

- **原子性操作**：为 `JSONStorage` 增加了文件锁，确保并发安全。
- **可配置性**：通过 `config.json` 动态选择存储后端。

✅ **明确的序列化策略**

- 强调了所有持久化对象必须是可序列化的，并提出了具体的实现建议。

✅ **健壮的错误处理**

- 为 `ExecutionRecovery` 定义了更详细的错误处理和重试逻辑。

✅ **安全和维护**

- 增加了数据加密和检查点清理策略。

✅ **用户交互**

- 提出了用于管理检查点的 CLI 命令。

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

    def to_dict(self) -> dict:
        # ... implementation for serialization ...
        pass

    @classmethod
    def from_dict(cls, data: dict) -> "Checkpoint":
        # ... implementation for deserialization ...
        pass
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
~/.cache/tiny-claude-code/project-name/persistence/
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

### 核心组件

#### 0. PersistenceManager（统一持久化管理器）🎯 **架构核心**

```python
# src/persistence/manager.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

class BaseStorage(ABC):
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

    def __init__(self, storage: BaseStorage):
        self.storage = storage

    # ... (rest of the methods are the same as in v1)
```

#### 1. 存储后端 (`BaseStorage` 实现)

##### JSONStorage

```python
class JSONStorage(BaseStorage):
    """JSON 文件存储后端（当前实现）"""

    def __init__(self, project_name: str, base_dir: str = "~/.cache/tiny-claude-code"):
        base_path = Path(base_dir).expanduser()
        self.storage_dir = base_path / project_name / "persistence"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, category: str, key: str, data: Dict) -> str:
        """保存数据到 JSON 文件，并使用文件锁确保原子性"""
        import fcntl  # Or a cross-platform library like filelock
        category_dir = self.storage_dir / category
        category_dir.mkdir(exist_ok=True)

        file_path = category_dir / f"{key}.json"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                fcntl.flock(f, fcntl.LOCK_EX)  # Exclusive lock
                json.dump(data, f, ensure_ascii=False, indent=2)
                fcntl.flock(f, fcntl.LOCK_UN)  # Unlock
        except IOError as e:
            # Handle locking errors
            raise RuntimeError(f"Could not lock file {file_path}: {e}") from e

        return str(file_path)

    # ... (load, delete, list methods)
```

##### SQLiteStorage

```python
class SQLiteStorage(BaseStorage):
    """SQLite 存储后端（未来可选实现）"""

    def __init__(self, project_name: str, base_dir: str = "~/.cache/tiny-claude-code"):
        base_path = Path(base_dir).expanduser()
        self.db_path = base_path / project_name / "persistence.db"
        self._init_db()
```

#### 2. CheckpointManager（检查点管理器）

```python
class CheckpointManager:
    """管理检查点的保存和加载"""
    # ... (implementation is the same as in v1)
```

#### 3. ExecutionRecovery（执行恢复）

```python
class ExecutionRecovery:
    """处理执行恢复"""

    async def resume_from_checkpoint(
        self,
        checkpoint_id: str,
        remaining_steps: List[Step]
    ) -> ExecutionResult:
        """从检查点恢复执行"""
        try:
            checkpoint = await self.checkpoint_manager.load_checkpoint(checkpoint_id)
            if not checkpoint:
                raise ValueError(f"Checkpoint {checkpoint_id} not found")

            context = Context.from_checkpoint(checkpoint)

            return await self._execute_steps(
                steps=remaining_steps,
                context=context,
                start_from_index=checkpoint.step_index + 1
            )
        except Exception as e:
            # Log the recovery failure and return a failed result
            return ExecutionResult(success=False, error=f"Recovery failed: {e}")

    # ... (retry_from_step, rollback_to_checkpoint methods)
```

#### 4. ExecutionTracker（执行跟踪）

```python
class ExecutionTracker:
    """跟踪执行过程"""
    # ... (implementation is the same as in v1)
```

### 序列化策略

所有需要持久化的对象（如 `Checkpoint`, `ExecutionHistory`, 以及 `state`, `context`, `variables` 中的内容）都必须是可序列化的。

- **基本类型**: `str`, `int`, `float`, `bool`, `list`, `dict` 等可以直接序列化。
- **复杂对象**: 自定义对象需要提供 `to_dict()` 和 `from_dict()` 方法。
- **Datetime**: `datetime` 对象在序列化时应转换为 ISO 8601 格式的字符串，在反序列化时再转换回来。

### 文件修改

- `src/checkpoint/manager.py` - 检查点管理器
- `src/checkpoint/recovery.py` - 恢复逻辑
- `src/checkpoint/tracker.py` - 执行跟踪
- `src/persistence/storage.py` - 存储后端
- `src/agents/enhanced_agent.py` - 集成检查点

---

## 架构演进路径（关键）

### P6 实施分三步演进

#### **第 1 步：引入 PersistenceManager（P6 起始）**

```python
# 新建文件：src/persistence/manager.py
# 包含：BaseStorage 接口 + JSONStorage 实现

# 修改：src/persistence.py
class ConversationPersistence:
    """旧的 API，保留向后兼容"""
    def __init__(self):
        # The storage backend can be configured here
        storage = self._get_configured_storage()
        self.manager = PersistenceManager(storage)

    def _get_configured_storage(self):
        # Read from config.json to decide which storage to use
        # Get current project name (e.g., from current working directory)
        project_name = Path.cwd().name
        # ...
        return JSONStorage(project_name)

    def save_conversation(self, conv_id, messages, ...):
        return self.manager.save_conversation(conv_id, {...})

    def load_conversation(self, conv_id):
        return self.manager.load_conversation(conv_id)
```

#### **第 2 步：集成 Checkpoint 系统（P6 中期）**

```python
# 新建文件：src/checkpoint/manager.py
# 使用 PersistenceManager 保存检查点

# 修改：src/agents/enhanced_agent.py
class EnhancedAgent:
    def __init__(self, ...):
        # Get current project name (e.g., from current working directory)
        project_name = Path.cwd().name
        storage = self._get_configured_storage(project_name)
        self.persistence = PersistenceManager(storage)
        self.checkpoint_manager = CheckpointManager(self.persistence)

    def _get_configured_storage(self, project_name: str):
        # Read from config.json to decide which storage to use
        # ...
        return JSONStorage(project_name)

    async def run_with_checkpoints(self, query):
        # ... (implementation is the same as in v1)
```

#### **第 3 步：多后端支持（P6 完成）**

```python
# config.json
{
  "persistence": {
    "storage_type": "sqlite",  // "json" or "sqlite"
    "path": ".cache/tiny-claude-code/data.db"
  }
}

# Factory function to create storage backend
import os
from pathlib import Path

def create_storage_from_config(config: dict) -> BaseStorage:
    storage_config = config.get("persistence", {})
    storage_type = storage_config.get("storage_type", "json")
    base_dir = storage_config.get("base_dir", "~/.cache/tiny-claude-code")
    
    # Get current project name (e.g., from current working directory)
    project_name = Path.cwd().name

    if storage_type == "sqlite":
        return SQLiteStorage(project_name, base_dir)
    else:
        return JSONStorage(project_name, base_dir)
```

---

## 安全与维护

### 数据加密

对于包含敏感信息（如 API 密钥）的检查点，应在持久化之前进行加密。

- **实现**: 可以在 `PersistenceManager` 中添加一个加密/解密层，或者创建一个 `EncryptedStorage` 包装器。
- **密钥管理**: 加密密钥应通过安全的方式（如环境变量或专用的密钥管理服务）提供。

### 检查点清理

为防止存储空间无限增长，需要一个清理策略。

- **策略**:
  - **基于时间**: 删除超过 N 天的检查点。
  - **基于数量**: 每个 `execution_id` 只保留最新的 N 个检查点。
  - **基于状态**: 删除已成功完成的执行的所有检查点。
- **实现**: 可以创建一个独立的清理脚本或一个在应用启动时运行的后台任务。

---

## 用户体验 (CLI 命令)

为了方便用户管理检查点，可以添加以下 CLI 命令：

- `/checkpoints list <execution_id>`: 列出指定执行的所有检查点。
- `/checkpoints inspect <checkpoint_id>`: 显示检查点的详细信息。
- `/checkpoints resume <checkpoint_id>`: 从指定的检查点恢复执行。
- `/checkpoints rollback <checkpoint_id>`: 回滚到指定的检查点（删除之后的所有检查点）。
- `/checkpoints clean`: 手动触发检查点清理。

---

## 测试验证



### 单元测试



1.  **PersistenceManager 功能测试**：

    *   验证 `save`, `load`, `delete`, `list` 方法在不同类别（`checkpoint`, `conversation`, `history`）下的正确性。

    *   测试加载不存在的数据时返回 `None`。

    *   验证删除不存在的数据时返回 `False`。



2.  **JSONStorage 实现测试**：

    *   验证文件路径的正确构建（`~/.cache/tiny-claude-code/project-name/persistence/category/key.json`）。

    *   **原子性测试**：模拟并发写入，验证文件锁是否能防止数据损坏或不一致。

    *   测试 `save` 方法在成功写入后返回正确的文件路径。

    *   测试 `load` 方法能正确读取 JSON 数据。

    *   测试 `delete` 方法能正确删除文件。

    *   测试 `list` 方法能正确列出指定类别下的所有文件。



3.  **SQLiteStorage 实现测试**：

    *   验证数据库文件路径的正确构建（`~/.cache/tiny-claude-code/project-name/persistence.db`）。

    *   验证数据库表的初始化是否正确（`persistence` 表结构）。

    *   测试 `save` 方法能正确插入或更新数据，并返回唯一 ID。

    *   测试 `load` 方法能正确从数据库加载数据。

    *   测试 `delete` 方法能正确从数据库删除数据。

    *   测试 `list` 方法能正确列出指定类别下的所有键。

    *   **事务性测试**：验证 SQLite 的事务特性在并发操作下的数据一致性。



4.  **CheckpointManager 逻辑测试**：

    *   验证 `create_checkpoint` 能正确生成 ID 并保存数据。

    *   验证 `load_checkpoint` 能正确加载指定检查点。

    *   验证 `list_checkpoints` 能按 `execution_id` 过滤并按 `step_index` 排序。

    *   验证 `get_last_successful_checkpoint` 能正确找到最后一个成功检查点。



5.  **ExecutionRecovery 逻辑测试**：

    *   **恢复成功**：模拟从一个成功的检查点恢复，并验证后续步骤能正确执行。

    *   **恢复失败**：模拟 `resume_from_checkpoint` 内部发生错误，验证其能返回 `ExecutionResult(success=False, error=...)`。

    *   **重试机制**：模拟 `retry_from_step`，验证其能从上一个成功检查点恢复并重试指定步骤，包括指数退避和最大重试次数的逻辑。

    *   **回滚逻辑**：验证 `rollback_to_checkpoint` 能正确删除指定检查点之后的所有检查点和相关历史记录。



6.  **ExecutionTracker 逻辑测试**：

    *   验证 `track_step` 和 `track_error` 能正确记录步骤和错误信息到 `ExecutionHistory`。

    *   验证 `get_execution_history` 能返回完整的执行历史。



### 集成测试



1.  **端到端检查点流程**：

    *   模拟一个多步骤的长流程任务，在每个步骤后保存检查点。

    *   在中间步骤模拟失败，验证系统能从最近的成功检查点自动恢复并完成任务。

    *   验证最终的 `ExecutionHistory` 记录了所有步骤、检查点和恢复尝试。



2.  **配置切换测试**：

    *   通过修改 `config.json` 切换 `JSONStorage` 和 `SQLiteStorage`，验证检查点功能在不同后端下都能正常工作。



3.  **清理策略测试**：

    *   创建大量检查点，然后运行清理任务，验证只有符合策略（如过期、超量）的检查点被删除。



4.  **加密/解密测试**：

    *   如果实现了加密层，验证敏感数据在保存时被加密，加载时被正确解密。



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

**实现者**: 待安排
**状态**: 📋 未开始
**依赖**: Phase 1 (Hooks 系统)
**相关 Phase**: Phase 4 (条件路由)
