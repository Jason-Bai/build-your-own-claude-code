# 修复：asyncio 事件循环冲突

**日期**: 2025-01-13
**相关 Commit**: 0370ab7
**影响范围**: Phase 1 输入增强
**严重程度**: 高（致命错误）

---

## 问题描述

### 症状
在异步环境中使用 PromptInputManager 时出现致命错误：
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

这导致应用启动后无法获取用户输入，无法正常运行。

### 原因分析

Prompt-Toolkit 的 `PromptSession.prompt()` 方法是同步的，它内部使用 `asyncio.run()` 来处理用户输入。

当应用的主程序已经有一个运行中的事件循环时，调用 `asyncio.run()` 会尝试创建第二个事件循环，这在 Python 的 asyncio 中是不允许的，导致 RuntimeError。

**调用栈**：
1. 应用主程序启动事件循环
2. 调用 `PromptInputManager.get_input()` (同步方法)
3. `PromptSession.prompt()` 内部调用 `asyncio.run()`
4. ❌ RuntimeError: asyncio.run() 不能在运行中的事件循环中调用

---

## 解决方案

### 实现细节

使用 Prompt-Toolkit 的异步 API `session.prompt_async()` 替代同步的 `prompt()`：

**修改前**（有问题）：
```python
class PromptInputManager:
    def get_input(self, prompt: str) -> str:
        """同步获取输入（有问题）"""
        result = self.session.prompt(prompt)  # ❌ 创建新事件循环
        return result
```

**修改后**（解决）：
```python
class PromptInputManager:
    async def async_get_input(self, prompt: str) -> str:
        """异步获取输入（正确）"""
        result = await self.session.prompt_async(prompt)  # ✅ 在现有事件循环中运行
        return result
```

### 文件修改

- **文件**: `src/utils/input.py`
- **类**: `PromptInputManager`
- **新增方法**: `async_get_input(prompt: str) -> str`
- **保留方法**: `get_input()` 仍然存在（用于同步上下文）

### 代码示例

```python
from src.utils.input import PromptInputManager

async def main():
    manager = PromptInputManager()

    # ✅ 在异步上下文中使用异步方法
    user_input = await manager.async_get_input("Your input: ")
    print(f"You entered: {user_input}")

# 在应用主循环中运行
import asyncio
asyncio.run(main())  # ✅ 成功
```

---

## 测试验证

### 手动测试

```python
import asyncio
from src.utils.input import PromptInputManager

async def test_async_input():
    """测试异步输入"""
    manager = PromptInputManager()

    # 这应该在没有事件循环错误的情况下运行
    result = await manager.async_get_input("Test prompt: ")
    print(f"Result: {result}")
    return result is not None

# 运行测试
result = asyncio.run(test_async_input())
print(f"✅ Test passed: {result}")
```

### 预期结果

- ✅ 应用启动后正常显示提示符
- ✅ 用户可以输入内容
- ✅ 没有 RuntimeError 异常
- ✅ 应用可以继续运行主事件循环

---

## 影响范围

### Phase 1 输入增强功能
- ✅ PromptInputManager 现在与 asyncio 兼容
- ✅ CommandCompleter 可以在异步上下文中使用
- ✅ 历史记录管理正常工作
- ✅ 所有快捷键功能可用

### 向后兼容性
- ✅ 同步 `get_input()` 方法仍然保留（虽然不推荐在异步上下文中使用）
- ✅ 现有代码不需要修改
- ✅ 可以逐步迁移到异步方法

### 应用主流程
- ✅ 应用主循环可以继续使用 asyncio.run()
- ✅ 不需要修改应用的事件循环管理
- ✅ 其他异步操作不受影响

---

## 相关技术资源

- **Prompt-Toolkit 文档**: https://python-prompt-toolkit.readthedocs.io/
- **Prompt-Toolkit 异步支持**: https://python-prompt-toolkit.readthedocs.io/en/master/pages/advanced_topics/asyncio_integration.html
- **Python asyncio 文档**: https://docs.python.org/3/library/asyncio.html

---

## 结论

这个修复确保了 Phase 1 输入增强功能在现代异步 Python 应用中的可靠性。通过使用 Prompt-Toolkit 的异步 API，我们避免了事件循环冲突，同时保持了代码的简洁性和可维护性。

---

**修复者**: Build Your Own Claude Code 项目维护者
**修复日期**: 2025-01-13
**相关 Commit**: `0370ab7 Fix: Add async support to PromptInputManager`
