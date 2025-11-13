# 修复：应用启动错误和 asyncio 兼容性

**日期**: 2025-01-13
**相关 Commit**: 0d3476f
**影响范围**: 应用启动、Hook 系统、状态命令
**严重程度**: 高（应用无法启动）

---

## 问题描述

### 症状
应用无法启动，出现多个错误：
1. `TypeError: load_dotenv() got an unexpected keyword argument 'dotenv_path'`
2. `RuntimeError: asyncio.run() cannot be called from a running event loop`
3. `AttributeError: 'EnhancedAgent' object has no attribute 'context'`

### 原因分析

这个提交修复了三个不相关的启动时问题：

#### 问题 1：load_dotenv() API 变更
python-dotenv 库的 API 发生了变化，从接受位置参数改为使用关键字参数。
```python
# ❌ 旧方式（已过期）
load_dotenv(env_file)  # TypeError

# ✅ 新方式
load_dotenv(dotenv_path=env_file)
```

#### 问题 2：_load_user_hooks 中的 asyncio 冲突
在已有运行的事件循环中调用 `asyncio.run()` 会导致冲突。
```python
# ❌ 问题代码
def _load_user_hooks(...):
    stats = asyncio.run(loader.load_hooks(...))  # 在异步上下文中不能用

# ✅ 解决方案
async def _load_user_hooks(...):
    stats = await loader.load_hooks(...)  # 直接 await
```

#### 问题 3：StatusCommand 中的属性引用错误
代码使用了不存在的属性名，应该使用经理类的正确引用。
```python
# ❌ 错误引用
agent.context.messages      # ❌ context 不存在
agent.tools.tools          # ❌ tools 不存在

# ✅ 正确引用
agent.context_manager.get_messages()   # ✅
agent.tool_manager.tools               # ✅
```

---

## 解决方案

### 实现细节

#### 修改 1：src/main.py - load_dotenv API 修复
```python
# 修改前
if env_file.exists():
    load_dotenv(env_file)  # ❌

# 修改后
if env_file.exists():
    load_dotenv(dotenv_path=env_file)  # ✅
```

#### 修改 2：src/main.py - _load_user_hooks 异步化
```python
# 修改前
def _load_user_hooks(hook_manager: HookManager, verbose: bool = False) -> None:
    """..."""
    import asyncio
    loader = HookConfigLoader()
    try:
        stats = asyncio.run(loader.load_hooks(hook_manager, skip_errors=True))  # ❌

# 修改后
async def _load_user_hooks(hook_manager: HookManager, verbose: bool = False) -> None:
    """..."""
    loader = HookConfigLoader()
    try:
        stats = await loader.load_hooks(hook_manager, skip_errors=True)  # ✅
```

以及在调用处也要改为 await：
```python
# 修改前
_load_user_hooks(hook_manager, verbose=args.verbose if args else False)

# 修改后
await _load_user_hooks(hook_manager, verbose=args.verbose if args else False)
```

#### 修改 3：src/commands/builtin.py - StatusCommand 属性修复
```python
# 修改前
total_messages = len(agent.context.messages)                    # ❌
estimated_tokens = agent.context.estimate_tokens()             # ❌
max_tokens = agent.context.max_tokens                           # ❌
tool_count = len(agent.tools.tools)                            # ❌
summary_length = len(agent.context.summary)                     # ❌

# 修改后
total_messages = len(agent.context_manager.get_messages())      # ✅
estimated_tokens = agent.context_manager.estimate_tokens()     # ✅
max_tokens = agent.context_manager.max_tokens                  # ✅
tool_count = len(agent.tool_manager.tools)                     # ✅
summary_length = len(agent.context_manager.summary)            # ✅
```

### 文件修改

- **文件 1**: `src/main.py`
  - 修复 `load_dotenv()` API 调用
  - 异步化 `_load_user_hooks()` 函数
  - 更新调用处为 `await` 形式

- **文件 2**: `src/commands/builtin.py`
  - 更新 StatusCommand 中所有对 Agent 属性的引用
  - 从 `agent.context` 改为 `agent.context_manager`
  - 从 `agent.tools` 改为 `agent.tool_manager`

---

## 测试验证

### 测试步骤

1. **启动应用**:
   ```bash
   python -m src.main
   ```
   应该正常启动，无启动错误。

2. **检查状态命令**:
   ```
   输入: /status
   预期: 显示完整的系统状态信息 ✅
   ```

3. **检查 Hook 加载**:
   ```
   输入: /status
   预期: 显示加载的 Hook 统计信息（如果有 Hook 配置）✅
   ```

### 预期结果

- ✅ 应用成功启动，无 ImportError
- ✅ load_dotenv 正确读取 .env 文件
- ✅ /status 命令能正确显示所有统计信息
- ✅ Hook 系统正确加载并显示统计

---

## 影响范围

### 应用启动
- ✅ 现在可以正确读取 .env 文件配置
- ✅ 应用启动时正确加载 Hook

### Hook 系统
- ✅ _load_user_hooks 不再引发 asyncio 冲突
- ✅ Hook 加载在异步上下文中正常工作

### 状态命令
- ✅ /status 命令能正确访问 Agent 的管理器
- ✅ 显示准确的统计信息

### 向后兼容性
- ✅ 现有配置文件继续工作
- ✅ Hook 配置文件继续工作
- ✅ 无 API 变更

---

## 相关技术资源

- **python-dotenv 文档**: https://github.com/theskumar/python-dotenv
- **Python asyncio 文档**: https://docs.python.org/3/library/asyncio.html
- **项目 Hook 系统**: [docs/development_guide.md](../development_guide.md#hook-系统开发)

---

## 结论

这个修复解决了三个关键的启动时问题，确保应用能够正常启动。主要改进包括：
1. 适配 python-dotenv 最新 API
2. 消除 asyncio 事件循环冲突
3. 修正 Agent 属性访问

这些修复是互相独立但同时发生的，都影响应用的正常启动。

---

**修复者**: Build Your Own Claude Code 项目维护者
**修复日期**: 2025-01-13
**相关 Commit**: `0d3476f Fix application startup errors and make asyncio compatible`
