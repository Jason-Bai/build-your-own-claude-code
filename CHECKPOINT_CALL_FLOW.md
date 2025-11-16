# Checkpoint 命令执行流程详解

## 1. 命令注册流程

```
应用启动
  └─ main.py
     └─ register_builtin_commands()  (/src/commands/__init__.py)
        ├─ HelpCommand()
        ├─ ClearCommand()
        ├─ ...
        └─ CheckpointCommand()  <-- 注册到 command_registry
           └─ 存储为 command_registry.commands["checkpoint"]
              └─ 添加别名
                 ├─ command_registry.aliases["rewind"] -> "checkpoint"
                 └─ command_registry.aliases["restore"] -> "checkpoint"
```

## 2. 命令执行流程 (调用 `/checkpoint`)

```
用户输入: /checkpoint
        │
        ▼
CommandRegistry.execute(text="/checkpoint", context)
        │
        ├─ 验证是否为命令 (text.startswith("/"))
        │
        ├─ 解析命令名和参数
        │  ├─ command_name = "checkpoint"
        │  └─ args = ""
        │
        ├─ 查找命令
        │  ├─ 先查 commands["checkpoint"]  ✓ 找到
        │  └─ 返回 CheckpointCommand 实例
        │
        ▼
CheckpointCommand.execute(args="", context)
        │
        ├─ 获取 CheckpointManager
        │  └─ context.agent.checkpoint_manager
        │
        ├─ 调用 get_formatted_checkpoint_history()
        │  │
        │  ├─ 获取所有检查点 ID
        │  │  └─ checkpoint_manager.persistence.storage.list("checkpoint")
        │  │     └─ 返回: ["ckpt-exec-001-0", "ckpt-exec-001-1", ...]
        │  │
        │  ├─ 按 execution_id 分组
        │  │  └─ {"exec-001": [cp1, cp2], "exec-002": [cp3]}
        │  │
        │  ├─ 加载每个检查点的详细信息
        │  │  └─ await checkpoint_manager.load_checkpoint(cp_id)
        │  │     ├─ PersistenceManager.load_checkpoint(cp_id)
        │  │     │  └─ storage.load("checkpoint", cp_id)
        │  │     │     └─ 读取 JSON 文件
        │  │     │        └─ ~/cache/tiny-claude-code/projects/.../checkpoint/
        │  │     │
        │  │     └─ Checkpoint.from_dict(data)
        │  │        └─ 反序列化为 Checkpoint 对象
        │  │
        │  ├─ 创建显示格式
        │  │  └─ "Restore exec-001\n  Step: data_processing"
        │  │
        │  └─ 返回: List[Tuple[execution_id, display_text]]
        │
        ├─ 检查是否有检查点
        │  ├─ 如果为空 -> return "No checkpoints found."
        │  └─ 如果非空 -> 继续
        │
        ├─ 添加 "(current)" 选项
        │  └─ history_items.insert(0, ("__current__", display_text))
        │
        ├─ 创建交互式选择器
        │  └─ selector = InteractiveListSelector(
        │       title="Checkpoints",
        │       items=history_items
        │     )
        │
        ├─ 显示 UI 并等待用户选择
        │  └─ selected_execution_id = await selector.run()
        │     │
        │     └─ 用户交互 (上下箭头选择, Enter 确认)
        │
        ├─ 根据用户选择处理
        │  ├─ 如果选择 "__current__"
        │  │  └─ return "Exited checkpoint selection."
        │  │
        │  └─ 如果选择其他 (e.g., "exec-001")
        │     ├─ (TODO: 实际恢复逻辑未实现)
        │     │  # last_checkpoint = await checkpoint_manager.get_last_successful_checkpoint(
        │     │  #   selected_execution_id
        │     │  # )
        │     │  # if last_checkpoint:
        │     │  #   await context.agent.recovery.resume_from_checkpoint(last_checkpoint.id)
        │     │  #   return "Restored..."
        │     │
        │     └─ return f"Selected execution to restore: {selected_execution_id}. ..."
        │
        ▼
返回结果字符串
        │
        └─ 显示给用户
```

## 3. 检查点加载详细流程

```
get_formatted_checkpoint_history()
  │
  ▼
await persistence.storage.list("checkpoint")
  │
  ├─ JSONStorage.list("checkpoint")
  │  │
  │  ├─ category_dir = ~/.cache/tiny-claude-code/projects/{project_name}/persistence/checkpoint/
  │  │
  │  ├─ 列出所有 *.json 文件
  │  │  └─ 返回: ["ckpt-exec-001-0", "ckpt-exec-001-1", ...]
  │  │
  │  └─ 返回文件列表
  │
  ▼
for cp_id in checkpoint_ids:
  │
  ├─ await checkpoint_manager.load_checkpoint(cp_id)
  │  │
  │  ├─ await persistence.load_checkpoint(cp_id)
  │  │  │
  │  │  ├─ await storage.load("checkpoint", cp_id)
  │  │  │  │
  │  │  │  ├─ file_path = {category_dir}/{cp_id}.json
  │  │  │  │
  │  │  │  ├─ if not file_path.exists():
  │  │  │  │    return None
  │  │  │  │
  │  │  │  └─ with open(file_path) as f:
  │  │  │      return json.load(f)
  │  │  │
  │  │  └─ 返回: {"id": "ckpt-...", "execution_id": "...", ...}
  │  │
  │  └─ Checkpoint.from_dict(data)
  │     │
  │     ├─ timestamp = datetime.fromisoformat(data["timestamp"])
  │     │
  │     └─ return Checkpoint(
  │          id=..., execution_id=..., step_name=...,
  │          timestamp=..., state=..., context=..., ...
  │        )
  │
  └─ 存储 Checkpoint 对象到 checkpoints_by_exec[execution_id]

▼
for exec_id in sorted(checkpoints_by_exec.keys(), reverse=True):
  │
  ├─ checkpoints = checkpoints_by_exec[exec_id]
  │
  ├─ last_cp = checkpoints[-1]  # 最后一个 checkpoint
  │
  ├─ display_text = f"Restore {exec_id}\n  Step: {last_cp.step_name}"
  │
  └─ formatted_items.append((exec_id, display_text))

▼
return formatted_items  # [(execution_id, display_text), ...]
```

## 4. 完整的状态恢复流程 (未实现部分)

```
用户选择检查点: exec-001
        │
        ▼
await context.agent.recovery.resume_from_checkpoint(checkpoint_id)
        │
        ├─ await checkpoint_manager.load_checkpoint(checkpoint_id)
        │  └─ 返回: Checkpoint 对象
        │
        ├─ agent_instance.restore_state_from_checkpoint(checkpoint)
        │  │
        │  ├─ state_manager.restore_state(checkpoint.state)
        │  │  └─ 恢复 Agent 内部状态
        │  │
        │  └─ 恢复其他信息 (context, variables)
        │
        └─ return ExecutionResult(success=True, ...)
```

## 5. 数据持久化流程

### 创建检查点时

```
await checkpoint_manager.create_checkpoint(
    execution_id="exec-001",
    step_name="data_fetch",
    step_index=0,
    state={...},
    context={...},
    variables={...}
)
        │
        ▼
Checkpoint(
    id="ckpt-exec-001-0",
    execution_id="exec-001",
    ...
)
        │
        ▼
checkpoint.to_dict()
        │
        ├─ timestamp -> timestamp.isoformat()
        │
        └─ return {
            "id": "ckpt-exec-001-0",
            "execution_id": "exec-001",
            "step_name": "data_fetch",
            "step_index": 0,
            "timestamp": "2024-11-16T10:30:45.123456",
            "state": {...},
            "context": {...},
            "variables": {...},
            "status": "success",
            "error": null,
            "metadata": {}
           }
        │
        ▼
await persistence.save_checkpoint(checkpoint_dict)
        │
        ├─ category = "checkpoint"
        ├─ key = "ckpt-exec-001-0"
        │
        ▼
await storage.save(category, key, data)
        │
        ├─ JSONStorage.save()
        │  │
        │  ├─ category_dir = ~/.cache/tiny-claude-code/projects/.../persistence/checkpoint/
        │  │
        │  ├─ file_path = {category_dir}/ckpt-exec-001-0.json
        │  │
        │  ├─ lock_path = {file_path}.lock
        │  │
        │  ├─ if FILELOCK_AVAILABLE:
        │  │    lock = FileLock(lock_path, timeout=5)
        │  │    with lock:
        │  │      with open(file_path, 'w') as f:
        │  │        json.dump(data, f, ...)
        │  │
        │  └─ return str(file_path)
        │
        ▼
检查点已保存到磁盘
```

## 6. 命令注册表查询流程

```
用户输入: /rewind
        │
        ▼
CommandRegistry.execute("/rewind", context)
        │
        ├─ command_name = "rewind"
        │
        ▼
CommandRegistry.get("rewind")
        │
        ├─ name = "rewind"  (去掉 "/" 前缀)
        │
        ├─ if name in self.commands:
        │    return self.commands[name]  # 不在
        │
        ├─ if name in self.aliases:
        │    actual_name = self.aliases["rewind"]  # "checkpoint"
        │    return self.commands["checkpoint"]  ✓ 找到
        │
        └─ return CheckpointCommand 实例
```

## 7. 错误处理流程

```
CheckpointCommand.execute()
        │
        ├─ try:
        │  │
        │  ├─ get_formatted_checkpoint_history()
        │  │  │
        │  │  ├─ 可能异常: FileNotFoundError, JSONDecodeError, etc.
        │  │  │
        │  │  └─ except: return []  (返回空列表，不崩溃)
        │  │
        │  └─ 其他逻辑
        │
        └─ 如果命令本身异常:
           └─ CommandRegistry.execute() 的 try-except 捕获
              └─ return f"❌ Command execution failed: {str(e)}"
```

## 8. 内存与文件系统交互

```
内存                          文件系统
                              
Checkpoint                   ckpt-exec-001-0.json
Object                        {
├─ id                         ├─ "id": "ckpt-exec-001-0"
├─ execution_id               ├─ "execution_id": "exec-001"
├─ step_name                  ├─ "step_name": "data_fetch"
├─ step_index              ── ├─ "step_index": 0
├─ timestamp               ── ├─ "timestamp": "2024-11-16T..."
├─ state: dict             ── ├─ "state": {...}
├─ context: dict           ── ├─ "context": {...}
├─ variables: dict         ── ├─ "variables": {...}
├─ status                  ── ├─ "status": "success"
├─ error                   ── ├─ "error": null
└─ metadata                ── └─ "metadata": {}
                              }
   to_dict()
   ←─────────────────────────→
   from_dict()
```

## 9. 调用栈深度分析

```
顶层: 用户交互
  │
  ├─ Level 1: CLIContext
  │  │
  │  ├─ Level 2: CommandRegistry.execute()
  │  │  │
  │  │  ├─ Level 3: CheckpointCommand.execute()
  │  │  │  │
  │  │  │  ├─ Level 4: CheckpointManager.get_formatted_checkpoint_history()
  │  │  │  │  │
  │  │  │  │  ├─ Level 5: PersistenceManager.storage.list()
  │  │  │  │  │  │
  │  │  │  │  │  └─ Level 6: JSONStorage.list()
  │  │  │  │  │     │
  │  │  │  │  │     └─ 文件系统操作 (glob, listdir)
  │  │  │  │  │
  │  │  │  │  ├─ Level 5: PersistenceManager.load_checkpoint()
  │  │  │  │  │  │
  │  │  │  │  │  ├─ Level 6: JSONStorage.load()
  │  │  │  │  │  │  └─ 文件I/O
  │  │  │  │  │  │
  │  │  │  │  │  └─ Level 6: Checkpoint.from_dict()
  │  │  │  │  │
  │  │  │  │  └─ Level 5: InteractiveListSelector.run()
  │  │  │  │     └─ UI 交互
  │  │  │  │
  │  │  │  └─ Level 4: 返回结果
  │  │  │
  │  │  └─ Level 3: 返回给用户
  │  │
  │  └─ Level 2: 返回结果
  │
  └─ Level 1: 显示到终端
```

## 10. 时序图

```
时间
│     用户输入      命令注册表    CheckpointCommand  CheckpointManager  存储层
│        │              │              │                    │              │
│        ├─ /checkpoint->│              │                    │              │
│        │              ├─ 查找→        │                    │              │
│        │              │        ├─ 获取历史────→           │              │
│        │              │        │              ├─ list()──────────────────→│
│        │              │        │              │  (遍历文件夹)             │
│        │              │        │              │←返回 ID 列表──────────────┤
│        │              │        │    (逐个加载)             │              │
│        │              │        │              ├─ load()──────────────────→│
│        │              │        │              │ (读 JSON)               │
│        │              │        │              │←返回数据──────────────────┤
│        │              │        │              ├─ from_dict()  │
│        │              │        │              ├─ 分组汇总    │
│        │              │        │←返回格式化列表│              │
│        │              │        │              │              │
│        │              │        ├─ 显示 UI────→
│        │              │        │   (交互式选择)
│        │
│        ├─ 用户选择项->│
│        │              │        ├─ 处理选择────→
│        │              │        │    (恢复逻辑 TODO)
│        │              │        │
│        ├─ 显示结果    │        │
│        │              │        │
▼─────────────────────────────────────────────────────
```

