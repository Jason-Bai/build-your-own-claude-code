# 功能：P6 - Checkpoint 持久化（Checkpoint Persistence）

**日期**: 待实现
**优先级**: P1 🟡
**难度**: ⭐⭐⭐
**预计周期**: 1 周
**状态**: 📋 未开始

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

#### 1. CheckpointManager（检查点管理器）
```python
class CheckpointManager:
    """管理检查点的保存和加载"""

    async def create_checkpoint(
        self,
        execution_id: str,
        step_name: str,
        step_index: int,
        state: dict,
        context: dict,
        variables: dict
    ) -> Checkpoint:
        """创建检查点"""
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
        await self._save_checkpoint(checkpoint)
        return checkpoint

    async def load_checkpoint(
        self,
        checkpoint_id: str
    ) -> Checkpoint:
        """加载检查点"""
        return await self._load_from_storage(checkpoint_id)

    async def list_checkpoints(
        self,
        execution_id: str
    ) -> List[Checkpoint]:
        """列出所有检查点"""
        pass

    async def delete_checkpoint(
        self,
        checkpoint_id: str
    ):
        """删除检查点"""
        pass

    async def _save_checkpoint(
        self,
        checkpoint: Checkpoint
    ):
        """保存检查点到存储"""
        pass
```

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

## 工作原理

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
