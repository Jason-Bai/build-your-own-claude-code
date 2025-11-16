# Checkpoint 命令 - 快速参考卡片

## 命令调用

```bash
/checkpoint    # 主命令
/rewind       # 别名
/restore      # 别名
```

## 当前状态

- **实现状态**: 50% 完成
- **可用功能**: 交互式检查点选择UI
- **缺失功能**: 实际恢复逻辑（标记为TODO）

---

## 核心文件

| 文件 | 功能 |
|------|------|
| `src/commands/checkpoint_commands.py` | 命令实现 |
| `src/checkpoint/manager.py` | 检查点管理 |
| `src/checkpoint/types.py` | 数据结构 |
| `src/checkpoint/recovery.py` | 恢复逻辑 |
| `src/persistence/manager.py` | 持久化 |
| `src/persistence/storage.py` | 存储后端 |

---

## 检查点ID格式

```
ckpt-{execution_id}-{step_index}

例如: ckpt-exec-123-2
```

---

## 主要类和方法

### CheckpointManager
- `create_checkpoint()` - 创建检查点
- `load_checkpoint()` - 加载检查点
- `list_checkpoints()` - 列出所有检查点
- `get_last_successful_checkpoint()` - 获取最后成功的
- `get_formatted_checkpoint_history()` - 获取UI格式的历史

### ExecutionRecovery
- `resume_from_checkpoint()` - 从检查点恢复
- `retry_from_step()` - 从步骤重试
- `rollback_to_checkpoint()` - 回滚（占位符）

---

## 数据流

```
┌─ Agent State
│
├─ create_checkpoint()
│  └─ Checkpoint Object
│     └─ to_dict()
│        └─ PersistenceManager.save_checkpoint()
│           └─ JSONStorage/SQLiteStorage
│              └─ ~/.cache/tiny-claude-code/.../checkpoint/
│
├─ get_formatted_checkpoint_history()
│  └─ Load all checkpoints from storage
│     └─ Group by execution_id
│        └─ Format for UI
│           └─ InteractiveListSelector
│
└─ load_checkpoint()
   └─ PersistenceManager.load_checkpoint()
      └─ Storage layer
         └─ Checkpoint.from_dict()
            └─ restore_state_from_checkpoint()
```

---

## 存储结构

```
~/.cache/tiny-claude-code/projects/{project_name}/persistence/
├── checkpoint/
│   ├── ckpt-exec-001-0.json
│   └── ckpt-exec-001-1.json
├── conversation/
├── history/
└── session/
```

---

## 检查点JSON示例

```json
{
  "id": "ckpt-exec-123-2",
  "execution_id": "exec-123",
  "step_name": "data_processing",
  "step_index": 2,
  "timestamp": "2024-11-16T10:30:45.123456",
  "state": {
    "phase": "processing",
    "processed_items": 100
  },
  "context": {
    "messages": [...],
    "user_id": "user-456"
  },
  "variables": {
    "total": 1000,
    "batch_size": 50
  },
  "status": "success",
  "error": null,
  "metadata": {}
}
```

---

## 支持的状态

- `success` - 成功完成
- `failed` - 执行失败
- `pending` - 进行中

---

## 代码示例

### 创建检查点
```python
cp = await checkpoint_manager.create_checkpoint(
    execution_id="exec-123",
    step_name="process",
    step_index=1,
    state={...},
    context={...},
    variables={...}
)
```

### 加载检查点
```python
cp = await checkpoint_manager.load_checkpoint("ckpt-exec-123-1")
if cp:
    await agent.restore_state_from_checkpoint(cp)
```

### 列出检查点
```python
checkpoints = await checkpoint_manager.list_checkpoints("exec-123")
for cp in checkpoints:
    print(f"Step {cp.step_index}: {cp.step_name}")
```

### 获取最后成功的
```python
last = await checkpoint_manager.get_last_successful_checkpoint("exec-123")
if last:
    result = await recovery.resume_from_checkpoint(last.id, agent)
```

---

## 存储后端

### JSON (当前)
- 默认实现
- 文件锁支持 (filelock)
- 原子性操作

### SQLite (可选)
- 数据库存储
- ACID事务
- 更好的并发支持

---

## 测试

运行测试:
```bash
pytest tests/unit/test_persistence_system.py -v
```

主要测试覆盖:
- 创建和加载检查点
- 列出检查点
- 获取最后成功的检查点
- JSON/SQLite存储
- 并发安全性

---

## 配置示例

```json
{
  "model": {
    "provider": "anthropic"
  },
  "persistence": {
    "storage_type": "json",
    "base_dir": "~/.cache/tiny-claude-code"
  }
}
```

---

## 状态转换图

```
┌─────────────┐
│   IDLE      │
└──────┬──────┘
       │ /checkpoint
       ▼
┌─────────────────────────────┐
│ Load checkpoint history     │
│ from storage                │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Show interactive selector   │
│ with checkpoint list        │
└──────┬──────────────────────┘
       │
       ├─ user selects item
       │
       ├─ return formatted output
       │
       └─ TODO: actual recovery not impl
```

---

## 常见问题

Q: 检查点会占用多少空间?
A: 每个约 1-10KB，取决于状态大小

Q: 支持自动清理吗?
A: 暂未实现，需手动删除

Q: 如何跨项目使用检查点?
A: 每个项目独立存储

Q: 支持加密吗?
A: 暂未实现

---

## 相关文档

- 完整设计: `docs/features/v0.0.1/p6-checkpoint-persistence.md`
- 完整指南: `CHECKPOINT_COMMAND_GUIDE.md`
- 架构文档: `docs/architecture_guide.md`

