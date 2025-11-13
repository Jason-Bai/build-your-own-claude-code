# Phase 3: 事件驱动实时反馈系统

## 概述

实现完整的事件驱动架构，支持实时反馈和 Hook 扩展。

**状态**: ✅ 完成

---

## 核心组件

### 1. 事件总线 (EventBus)

**位置**: `src/events/bus.py`

#### 功能
- 发布-订阅消息传递
- 异步事件处理
- 事件优先级管理
- 事件去重

#### 接口

```python
class EventBus:
    """事件总线 - 中央事件分发器"""

    async def emit(self, event: Event) -> None:
        """发出事件"""

    def subscribe(self, event_type: str, callback) -> None:
        """订阅事件"""

    def unsubscribe(self, event_type: str, callback) -> None:
        """取消订阅"""
```

### 2. 事件类型 (EventType)

**位置**: `src/events/types.py`

#### 支持的事件

| 事件类型 | 说明 | 数据 |
|---------|------|------|
| `agent_started` | Agent 启动 | `{"timestamp": ...}` |
| `thinking` | 思考过程 | `{"message": "..."}` |
| `tool_call` | 工具调用 | `{"tool_name": "...", "params": {...}}` |
| `tool_result` | 工具结果 | `{"tool_name": "...", "success": bool, "output": "..."}` |
| `message_sent` | 消息发送 | `{"role": "...", "content": "..."}` |
| `response_ready` | 响应就绪 | `{"text": "..."}` |
| `context_compressed` | 上下文压缩 | `{"tokens_removed": 123}` |
| `error_occurred` | 错误发生 | `{"error": "...", "context": {...}}` |

### 3. Hook 系统

**位置**: `src/hooks/`

#### 组件结构

```
src/hooks/
├── manager.py          # Hook 管理器
├── types.py            # Hook 类型定义
├── config_loader.py    # Hook 配置加载
├── validator.py        # Hook 验证
└── secure_loader.py    # 安全代码加载
```

#### Hook 类型

```python
class Hook:
    """Hook 定义"""
    event: str              # 触发事件
    type: str               # "command" 或 "python"
    command: str            # 执行的命令（如果 type="command"）
    code: str               # Python 代码（如果 type="python"）
    priority: int           # 优先级（高优先级先执行）
    enabled: bool           # 是否启用
```

#### 配置示例

```json
{
  "hooks": [
    {
      "event": "on_tool_call",
      "type": "command",
      "command": "echo 'Tool called: {tool_name}'",
      "priority": 10
    },
    {
      "event": "on_thinking",
      "type": "python",
      "code": "print(f'Thinking about: {message}')",
      "priority": 5
    }
  ]
}
```

### 4. Hook 管理器

**位置**: `src/hooks/manager.py`

#### 功能
- 注册/注销 Hook
- 执行 Hook
- 错误处理和恢复

#### 接口

```python
class HookManager:
    """Hook 管理器"""

    def register_hook(self, hook: Hook) -> None:
        """注册 Hook"""

    async def execute_hooks(self, event: str, context: dict) -> None:
        """执行指定事件的所有 Hook"""

    def unregister_hook(self, event: str, hook_id: str) -> None:
        """注销 Hook"""
```

---

## 集成架构

### 事件流

```
应用事件
  ↓
EventBus.emit(event)
  ├─ 记录事件
  ├─ 触发订阅的回调
  └─ 执行相关的 Hook
  ↓
Hook 执行
  ├─ 加载 Hook 代码
  ├─ 验证安全性
  ├─ 执行代码
  └─ 处理错误
```

### Agent 集成

```python
# 在 enhanced_agent.py 中
event_bus = get_event_bus()

# 发出事件
await event_bus.emit(Event(
    type="tool_call",
    data={"tool_name": "read", "params": {...}}
))

# Hook 自动触发
# → 执行 on_tool_call 的所有 Hook
```

---

## 完整事件流示例

### 场景: 用户请求 → Agent 处理 → 工具调用

```
1. 用户输入
   👤 You: 读取 README.md

2. Agent 开始思考
   Event: agent_started
   Hook: on_agent_started (如果有)

3. Agent 决定使用工具
   Event: thinking
   Hook: on_thinking
   → 日志: "Thinking about file operations"

4. 调用 Read 工具
   Event: tool_call
   Hook: on_tool_call
   → 日志: "Tool called: Read"
   → 可能: 执行权限检查

5. 工具执行成功
   Event: tool_result
   Hook: on_tool_result
   → 日志: "Tool completed: Read"
   → 可能: 保存操作日志

6. Agent 生成响应
   Event: response_ready
   Hook: on_response_ready
   → 可能: 格式化输出

7. 消息发送完成
   Event: message_sent
   Hook: on_message_sent
   → 可能: 更新统计信息
```

---

## 安全考虑

### Python Hook 执行安全

#### 1. AST 验证
- 解析 Hook 代码的 AST
- 检测危险操作（如 `os.system()` 调用）
- 拒绝执行不安全的代码

#### 2. 导入限制
- 限制可导入的模块
- 白名单: `logging`, `json`, `datetime` 等安全模块
- 拒绝: `os`, `subprocess`, `sys` 等系统模块

#### 3. 执行沙盒
- 隔离执行上下文
- 限制访问的全局变量
- 超时保护

### 配置文件权限

- **全局**: `~/.tiny-claude/settings.json` (644 权限)
- **项目**: `.tiny-claude/settings.json` (644 权限)
- **本地**: `.tiny-claude/settings.local.json` (600 权限)

---

## 使用例子

### 1. 监控工具调用

```json
{
  "event": "on_tool_call",
  "type": "python",
  "code": "print(f'Tool: {tool_name}, Params: {params}')",
  "priority": 10
}
```

### 2. 自动日志记录

```json
{
  "event": "on_tool_result",
  "type": "command",
  "command": "echo '[TOOL] {tool_name}: {status}' >> ~/.tiny-claude/tools.log",
  "priority": 5
}
```

### 3. 错误通知

```json
{
  "event": "on_error",
  "type": "command",
  "command": "notify-send 'Claude Code Error' 'Error: {error}'",
  "priority": 20
}
```

### 4. Token 统计

```json
{
  "event": "on_response_ready",
  "type": "python",
  "code": "logging.info(f'Total tokens: {tokens_used}')",
  "priority": 5
}
```

---

## 事件类型详解

### agent_started
**何时触发**: Agent 开始处理用户输入
```python
{
    "timestamp": datetime,
    "user_input": str
}
```

### thinking
**何时触发**: Agent 分析输入和制定计划
```python
{
    "message": str,
    "step": int
}
```

### tool_call
**何时触发**: 即将调用工具
```python
{
    "tool_name": str,
    "params": dict,
    "timestamp": datetime
}
```

### tool_result
**何时触发**: 工具执行完成
```python
{
    "tool_name": str,
    "success": bool,
    "output": str,
    "execution_time": float
}
```

### message_sent
**何时触发**: 消息发送给 LLM 或返回给用户
```python
{
    "role": str,  # "user" 或 "assistant"
    "content": str,
    "tokens": int
}
```

### response_ready
**何时触发**: Agent 生成最终响应
```python
{
    "text": str,
    "tokens_used": int,
    "execution_time": float
}
```

### context_compressed
**何时触发**: 上下文被自动压缩
```python
{
    "tokens_before": int,
    "tokens_after": int,
    "tokens_removed": int,
    "compression_ratio": float
}
```

### error_occurred
**何时触发**: 发生错误
```python
{
    "error": str,
    "error_type": str,
    "context": dict,
    "timestamp": datetime
}
```

---

## 配置位置

### 全局 Hook 配置
```
~/.tiny-claude/settings.json
```

### 项目 Hook 配置
```
.tiny-claude/settings.json
```

### 本地 Hook 配置（gitignored）
```
.tiny-claude/settings.local.json
```

### 配置合并优先级
1. 本地配置 (最高优先级)
2. 项目配置
3. 全局配置 (最低优先级)

---

## 性能指标

- **事件发出**: < 1ms
- **Hook 执行**: 取决于 Hook 类型，通常 10-100ms
- **事件缓冲**: 异步处理，不阻塞 Agent
- **内存使用**: 每个事件 ~200 字节

---

## 实现提交

| 提交哈希 | 说明 |
|---------|------|
| `1a17886` | P3: 实现事件驱动实时反馈系统 |

---

## 与现有系统的集成

### Agent 集成
- Agent 在关键步骤发出事件
- Hook 可以监控和控制 Agent 行为

### 工具集成
- 工具调用前后发出事件
- Hook 可以记录、验证、修改工具调用

### 输出集成
- 响应生成时发出事件
- Hook 可以格式化、过滤、转发输出

---

## 未来扩展

### 可能的增强
1. **Event 过滤**: 支持正则表达式过滤事件
2. **异步 Hook**: 支持异步 Python Hook
3. **Hook 链**: Hook 之间的依赖和调用链
4. **事件回放**: 录制和回放事件流用于调试
5. **事件聚合**: 将多个事件聚合成高级事件

---

**状态**: ✅ 完成
**开始时间**: 2024-12
**完成时间**: 2025-01
**总耗时**: ~2 周
**代码行数**: ~500 行（事件系统 + Hook 系统）
