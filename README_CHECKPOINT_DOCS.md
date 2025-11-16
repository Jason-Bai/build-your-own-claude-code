# Checkpoint 命令文档导航

## 文档概览

本目录包含关于 `/checkpoint` 命令的完整搜索和分析文档（共4份，2023行）。

### 文档文件

| 文件名 | 大小 | 行数 | 用途 |
|--------|------|------|------|
| **CHECKPOINT_SEARCH_SUMMARY.md** | 13K | 532 | 总体总结和导航 (START HERE) |
| **CHECKPOINT_QUICK_REF.md** | 5.3K | 268 | 快速参考卡片 |
| **CHECKPOINT_COMMAND_GUIDE.md** | 25K | 827 | 完整实现指南 |
| **CHECKPOINT_CALL_FLOW.md** | 14K | 396 | 执行流程和时序图 |

---

## 快速开始

### 我是第一次了解这个命令

1. 先读: **CHECKPOINT_QUICK_REF.md** (5-10分钟)
   - 了解命令名、别名、核心概念

2. 再读: **CHECKPOINT_SEARCH_SUMMARY.md** 第一部分 (10-15分钟)
   - 理解命令结构和功能

### 我需要完整的实现细节

1. 读: **CHECKPOINT_COMMAND_GUIDE.md** (20-30分钟)
   - 代码实现、类、方法、使用例子

2. 读: **CHECKPOINT_CALL_FLOW.md** (15-20分钟)
   - 理解执行流程和数据流

### 我需要快速查找某个功能

查看 **CHECKPOINT_SEARCH_SUMMARY.md** 的"快速导航"部分 (第12节)

---

## 命令速查

```bash
# 调用方式
/checkpoint    # 主命令
/rewind       # 别名
/restore      # 别名

# 特点
- 无参数，通过交互式UI操作
- 显示检查点历史列表
- 用户选择要恢复的检查点
```

---

## 核心文件位置

```
src/
├── checkpoint/                      # Checkpoint 模块
│   ├── types.py                    # 数据结构
│   ├── manager.py                  # 检查点管理器
│   └── recovery.py                 # 恢复逻辑
├── commands/
│   ├── checkpoint_commands.py       # 命令实现 ⭐
│   └── __init__.py                 # 命令注册
├── persistence/
│   ├── manager.py                  # 持久化管理
│   └── storage.py                  # 存储后端
└── agents/
    └── enhanced_agent.py           # Agent 集成
```

---

## 关键概念

### 检查点 ID 格式

```
ckpt-{execution_id}-{step_index}

例如: ckpt-exec-123-2
```

### 存储位置

```
~/.cache/tiny-claude-code/projects/{project_name}/persistence/checkpoint/
```

### 支持的状态

- `success` - 成功完成
- `failed` - 执行失败
- `pending` - 进行中

---

## 核心方法

### CheckpointManager

| 方法 | 功能 |
|------|------|
| `create_checkpoint()` | 创建检查点 |
| `load_checkpoint()` | 加载检查点 |
| `list_checkpoints()` | 列出检查点 |
| `get_last_successful_checkpoint()` | 获取最后成功的 |
| `delete_checkpoint()` | 删除检查点 |
| `get_formatted_checkpoint_history()` | 获取UI格式数据 |

详见: **CHECKPOINT_COMMAND_GUIDE.md** 第3.1节

### ExecutionRecovery

| 方法 | 功能 |
|------|------|
| `resume_from_checkpoint()` | 从检查点恢复 |
| `retry_from_step()` | 从步骤重试 |
| `rollback_to_checkpoint()` | 回滚 |

详见: **CHECKPOINT_COMMAND_GUIDE.md** 第3.3节

---

## 代码示例

### 创建检查点

```python
checkpoint = await checkpoint_manager.create_checkpoint(
    execution_id="exec-123",
    step_name="data_processing",
    step_index=2,
    state={"phase": "processing"},
    context={...},
    variables={...},
    status="success"
)
```

详见: **CHECKPOINT_COMMAND_GUIDE.md** 第6.1节

### 列出检查点

```python
checkpoints = await checkpoint_manager.list_checkpoints("exec-123")
for cp in checkpoints:
    print(f"Step {cp.step_index}: {cp.step_name}")
```

详见: **CHECKPOINT_COMMAND_GUIDE.md** 第6.3节

### 从检查点恢复

```python
result = await recovery.resume_from_checkpoint(checkpoint_id, agent)
if result.success:
    print("Recovery successful!")
```

详见: **CHECKPOINT_COMMAND_GUIDE.md** 第6.5节

---

## 执行流程

```
用户输入: /checkpoint
    ↓
命令注册表查找
    ↓
CheckpointCommand.execute()
    ↓
获取检查点历史
    ↓
显示交互式 UI
    ↓
用户选择
    ↓
返回结果
```

详见: **CHECKPOINT_CALL_FLOW.md** 第2节

---

## 当前状态

- **完成度**: 50%
- **已实现**: 
  - 命令框架
  - 交互式 UI
  - 检查点管理底层
- **缺失**: 
  - 实际状态恢复逻辑 (标记为 TODO)

详见: **CHECKPOINT_SEARCH_SUMMARY.md** 第十三节

---

## 测试

运行测试:
```bash
pytest tests/unit/test_persistence_system.py -v
```

测试覆盖:
- 创建和加载检查点
- 列出检查点
- 获取最后成功的检查点
- JSON/SQLite 存储后端

详见: **CHECKPOINT_COMMAND_GUIDE.md** 第7节

---

## 关键限制

| 限制 | 说明 |
|------|------|
| 恢复逻辑 | 标记为 TODO，未完全实现 |
| 自动清理 | 不支持，需手动删除 |
| 加密 | 不支持 |
| 跨项目 | 每个项目独立存储 |

详见: **CHECKPOINT_SEARCH_SUMMARY.md** 第十三节

---

## 常见问题

**Q: 检查点会占用多少空间?**
A: 每个约 1-10KB，取决于状态大小

**Q: 如何创建检查点?**
A: 通过 `CheckpointManager.create_checkpoint()` 方法

**Q: 检查点存储在哪里?**
A: `~/.cache/tiny-claude-code/projects/{project_name}/persistence/checkpoint/`

**Q: 支持哪些存储后端?**
A: JSON (当前) 和 SQLite (可选)

详见: **CHECKPOINT_QUICK_REF.md** 常见问题部分

---

## 下一步

推荐按此顺序阅读完整文档:

1. **CHECKPOINT_SEARCH_SUMMARY.md** - 总体了解
2. **CHECKPOINT_QUICK_REF.md** - 快速查找
3. **CHECKPOINT_COMMAND_GUIDE.md** - 深入理解代码
4. **CHECKPOINT_CALL_FLOW.md** - 理解执行细节

---

## 文档统计

- 总行数: 2,023 行
- 总大小: 57KB
- 代码示例: 30+ 个
- 流程图: 10+ 个
- 数据结构: 5+ 个

---

## 版本信息

- 搜索日期: 2024-11-16
- 代码库: build-your-own-claude-code
- 分支: main
- 命令状态: 50% 完成

---

**提示**: 所有文档都是自动生成的。如果发现错误或需要更新，请参考源代码中的注释。
