# Phase 1: 全局 Hooks 系统

> 📌 **优先级**: P0 🔴 | **难度**: ⭐⭐ | **预计周期**: 1 周
>
> **目标**: 实现事件驱动的 Hooks 系统，为后续功能（日志、监控等）提供基础设施
>
> **状态**: 📋 设计阶段

---

## 🎯 设计思路

### 核心概念

Hooks 是一个**事件驱动系统**，贯穿整个应用生命周期。通过在关键节点触发事件，允许第三方代码（或系统功能）以非侵入方式参与应用流程。

### 事件流图

```
应用运行过程中的关键节点：

┌────────────────────────────────────────────────────────────┐
│ User Input                                                 │
│    ↓                                                        │
│ [Hook: on_user_input] → ✨ 日志记录、输入验证、审计       │
│    ↓                                                        │
│ Agent Processing                                           │
│    ├─ [Hook: on_agent_start] → ✨ 初始化、资源分配       │
│    ├─ [Hook: on_thinking] → ✨ 思考过程记录              │
│    ├─ [Hook: on_tool_select] → ✨ 工具审计               │
│    ├─ [Hook: on_permission_check] → ✨ 权限检查          │
│    ├─ [Hook: on_tool_execute] → ✨ 执行跟踪              │
│    ├─ [Hook: on_tool_result] → ✨ 结果验证               │
│    ├─ [Hook: on_tool_error] → ✨ 错误处理                │
│    └─ [Hook: on_agent_end] → ✨ 汇总、性能统计          │
│    ↓                                                        │
│ Output Generation                                          │
│    ├─ [Hook: on_output_format] → ✨ 输出格式化          │
│    ├─ [Hook: on_output_render] → ✨ 渲染前处理          │
│    └─ [Hook: on_output_send] → ✨ 发送前处理            │
│    ↓                                                        │
│ Error Handling                                             │
│    ├─ [Hook: on_error] → ✨ 错误捕获、分类、记录        │
│    └─ [Hook: on_recovery] → ✨ 恢复策略                  │
│    ↓                                                        │
│ Shutdown                                                   │
│    └─ [Hook: on_shutdown] → ✨ 清理、最终日志           │
└────────────────────────────────────────────────────────────┘
```

### 核心特性

- ✅ **事件驱动**：应用中的关键点都能触发 Hook
- ✅ **非侵入式**：核心逻辑无需修改
- ✅ **优先级控制**：多个 Handler 可按优先级执行
- ✅ **异步支持**：完全的 async/await 支持
- ✅ **链式追踪**：通过 request_id 追踪完整流程
- ✅ **错误隔离**：Hook 异常不中断主流程

---

## 📐 模块设计

### 1. Hook 事件定义 (`src/hooks/types.py`)

```python
# 事件类型枚举
class HookEvent(Enum):
    # User Interaction
    ON_USER_INPUT = "user.input"
    ON_COMMAND_PARSE = "command.parse"

    # Agent Lifecycle
    ON_AGENT_START = "agent.start"
    ON_AGENT_END = "agent.end"
    ON_AGENT_ERROR = "agent.error"

    # Thinking Process
    ON_THINKING = "agent.thinking"
    ON_DECISION = "agent.decision"

    # Tool Execution
    ON_TOOL_SELECT = "tool.select"
    ON_TOOL_EXECUTE = "tool.execute"
    ON_TOOL_RESULT = "tool.result"
    ON_TOOL_ERROR = "tool.error"
    ON_PERMISSION_CHECK = "permission.check"

    # Output
    ON_OUTPUT_FORMAT = "output.format"
    ON_OUTPUT_RENDER = "output.render"
    ON_OUTPUT_SEND = "output.send"

    # System
    ON_ERROR = "system.error"
    ON_RECOVERY = "system.recovery"
    ON_SHUTDOWN = "system.shutdown"
    ON_METRICS = "system.metrics"

# Hook 上下文
@dataclass
class HookContext:
    """Hook 执行时的上下文信息"""
    event: HookEvent
    timestamp: float

    # 事件特定数据
    data: Dict[str, Any]

    # 上下文追踪
    request_id: str
    agent_id: str
    user_id: Optional[str]

    # 元数据
    metadata: Dict[str, Any]

# Handler 类型定义
class HookHandler(Protocol):
    """Hook 处理函数的类型定义"""
    async def __call__(self, context: HookContext) -> None:
        ...
```

### 2. Hook 管理器 (`src/hooks/manager.py`)

```python
class HookManager:
    """全局 Hook 管理器"""

    def __init__(self):
        self._handlers: Dict[HookEvent, List[tuple]] = {}
        self._error_handlers: List[Callable] = []

    def register(
        self,
        event: HookEvent,
        handler: HookHandler,
        priority: int = 0
    ) -> None:
        """
        注册 Hook 处理器

        Args:
            event: Hook 事件
            handler: 处理函数
            priority: 优先级（越大越先执行）
        """
        ...

    def unregister(self, event: HookEvent, handler: HookHandler) -> None:
        """取消注册 Handler"""
        ...

    async def trigger(self, event: HookEvent, context: HookContext) -> None:
        """
        触发一个 Hook 事件

        Args:
            event: Hook 事件
            context: Hook 上下文
        """
        ...

    def register_error_handler(self, handler: Callable) -> None:
        """注册 Hook 异常处理器"""
        ...
```

### 3. Hook 上下文构建器 (`src/hooks/builder.py`)

```python
class HookContextBuilder:
    """Helper 类：简化 HookContext 的构建"""

    def __init__(self, request_id: str, agent_id: str):
        self.request_id = request_id
        self.agent_id = agent_id
        self.base_data = {
            "request_id": request_id,
            "agent_id": agent_id,
            "timestamp": time.time(),
        }

    def build(
        self,
        event: HookEvent,
        **data
    ) -> HookContext:
        """构建 Hook 上下文"""
        return HookContext(
            event=event,
            timestamp=time.time(),
            data=data,
            request_id=self.request_id,
            agent_id=self.agent_id,
            user_id=None,
            metadata={},
        )
```

---

## 🔌 集成点

### 集成到 EnhancedAgent

```python
# src/agents/enhanced_agent.py

class EnhancedAgent:
    def __init__(self, ..., hook_manager: HookManager = None):
        self.hooks = hook_manager or HookManager()

    async def run(self, user_input: str):
        context_id = generate_id()
        builder = HookContextBuilder(context_id, self.id)

        # 1. 用户输入
        await self.hooks.trigger(
            HookEvent.ON_USER_INPUT,
            builder.build(HookEvent.ON_USER_INPUT, input=user_input)
        )

        # 2. Agent 启动
        await self.hooks.trigger(
            HookEvent.ON_AGENT_START,
            builder.build(HookEvent.ON_AGENT_START)
        )

        try:
            # 3. 思考过程
            await self.hooks.trigger(
                HookEvent.ON_THINKING,
                builder.build(HookEvent.ON_THINKING, prompt=prompt)
            )

            # 4. Tool 选择
            await self.hooks.trigger(
                HookEvent.ON_TOOL_SELECT,
                builder.build(
                    HookEvent.ON_TOOL_SELECT,
                    tool_name=tool_name,
                    reason=reason
                )
            )

            # 5. 权限检查
            await self.hooks.trigger(
                HookEvent.ON_PERMISSION_CHECK,
                builder.build(
                    HookEvent.ON_PERMISSION_CHECK,
                    tool_name=tool_name,
                    permission_level=level
                )
            )

            # 6. Tool 执行
            start_time = time.time()
            await self.hooks.trigger(
                HookEvent.ON_TOOL_EXECUTE,
                builder.build(
                    HookEvent.ON_TOOL_EXECUTE,
                    tool_name=tool_name,
                    params=params
                )
            )

            result = await self._execute_tool(tool_name, params)
            duration = time.time() - start_time

            # 7. Tool 结果
            await self.hooks.trigger(
                HookEvent.ON_TOOL_RESULT,
                builder.build(
                    HookEvent.ON_TOOL_RESULT,
                    tool_name=tool_name,
                    success=result.success,
                    duration=duration
                )
            )

        except Exception as e:
            # 错误处理
            await self.hooks.trigger(
                HookEvent.ON_AGENT_ERROR,
                builder.build(
                    HookEvent.ON_AGENT_ERROR,
                    error=str(e),
                    error_type=type(e).__name__
                )
            )
            raise

        finally:
            # Agent 结束
            await self.hooks.trigger(
                HookEvent.ON_AGENT_END,
                builder.build(
                    HookEvent.ON_AGENT_END,
                    stats=self.state_manager.get_stats()
                )
            )
```

---

## 🗂️ 目录结构

```
src/
├── hooks/                          # ✨ 新增
│   ├── __init__.py
│   ├── types.py                    # Hook 事件和类型定义
│   ├── manager.py                  # Hook 管理器
│   ├── builder.py                  # Hook 上下文构建器
│   └── utils.py                    # 工具函数
│
└── agents/
    └── enhanced_agent.py           # 集成 Hook 触发点
```

---

## ✅ 实现清单

- [ ] 创建 `src/hooks/` 目录结构
- [ ] 实现 `HookEvent` 枚举（所有事件类型）
- [ ] 实现 `HookContext` 数据类
- [ ] 实现 `HookManager` 核心类
- [ ] 实现 `HookContextBuilder` 辅助类
- [ ] 在 `EnhancedAgent` 中集成 Hook 触发点
- [ ] 编写 Hook 系统单元测试
- [ ] 编写集成测试（验证 Hook 是否正确触发）
- [ ] 编写 Hook 使用示例
- [ ] 更新文档和注释

---

## 🧪 测试计划

### 单元测试

```python
# tests/hooks/test_manager.py

def test_hook_registration():
    """测试 Hook 注册"""
    ...

def test_hook_trigger():
    """测试 Hook 触发"""
    ...

def test_hook_priority():
    """测试 Hook 优先级"""
    ...

def test_hook_error_isolation():
    """测试 Hook 异常隔离"""
    ...

def test_hook_context_builder():
    """测试 Hook 上下文构建"""
    ...
```

### 集成测试

```python
# tests/integration/test_agent_hooks.py

async def test_agent_hooks_flow():
    """测试 Agent 运行时的 Hook 触发流程"""
    hook_manager = HookManager()
    events_captured = []

    async def capture_event(context):
        events_captured.append(context.event)

    # 注册所有事件
    for event in HookEvent:
        hook_manager.register(event, capture_event)

    agent = EnhancedAgent(..., hook_manager=hook_manager)
    await agent.run("测试输入")

    # 验证关键事件被触发
    assert HookEvent.ON_USER_INPUT in events_captured
    assert HookEvent.ON_AGENT_START in events_captured
    assert HookEvent.ON_AGENT_END in events_captured
    ...
```

---

## 📝 使用示例

### 基础用法

```python
from src.hooks import HookManager, HookEvent, HookContext

# 1. 创建 Hook 管理器
hook_manager = HookManager()

# 2. 定义 Hook 处理器
async def my_hook_handler(context: HookContext):
    print(f"事件: {context.event.value}")
    print(f"数据: {context.data}")

# 3. 注册 Hook
hook_manager.register(HookEvent.ON_TOOL_EXECUTE, my_hook_handler)

# 4. 在应用中使用
agent = EnhancedAgent(..., hook_manager=hook_manager)
```

### 高级用法（优先级）

```python
# 高优先级处理器（先执行）
async def audit_hook(context: HookContext):
    # 审计日志
    pass

# 低优先级处理器（后执行）
async def metrics_hook(context: HookContext):
    # 收集指标
    pass

hook_manager.register(HookEvent.ON_TOOL_EXECUTE, audit_hook, priority=100)
hook_manager.register(HookEvent.ON_TOOL_EXECUTE, metrics_hook, priority=1)
```

---

## 🔧 扩展设计：用户 Hook 配置

> 📝 **说明**: 当前 Phase 1 设计为系统级 Hook。未来支持用户端 Hook 配置需要额外的加载机制。
>
> ⚠️ **范围**: 本 Phase 不包含，建议在 Phase 2 或单独作为 Phase 1.5 实现

### 设计目标

支持用户通过配置文件定义和加载自定义 Hook：

```
~/.claude/settings.json              # 用户级设置
.claude/settings.json                # 项目级设置
.claude/settings.local.json          # 本地设置（不提交）
Enterprise managed policy settings    # 企业策略
```

### 配置文件格式

```json
{
  "hooks": {
    "custom_handlers": [
      {
        "event": "tool.execute",
        "handler": "my_module:my_hook_handler",
        "priority": 50,
        "enabled": true
      },
      {
        "event": "agent.error",
        "handler": "monitoring:error_reporter",
        "priority": 100,
        "enabled": true
      }
    ]
  }
}
```

### 配置优先级

```
企业策略 (最高)
    ↓
~/.claude/settings.json
    ↓
.claude/settings.json
    ↓
.claude/settings.local.json (最低)
```

### 核心实现方案

#### 1. Hook 配置加载器 (`src/hooks/config_loader.py`)

```python
class HookConfigLoader:
    """从配置文件加载用户 Hook"""

    async def load_hooks(self, hook_manager: HookManager):
        """
        按优先级加载所有 Hook 配置

        加载顺序：
        1. 企业策略配置
        2. ~/.claude/settings.json (用户全局)
        3. .claude/settings.json (项目级)
        4. .claude/settings.local.json (本地)
        """
        configs = self._collect_configs()

        for config in configs:
            await self._load_config_file(config, hook_manager)

    async def _load_config_file(self, config_path: str, hook_manager: HookManager):
        """从单个配置文件加载 Hook"""
        with open(config_path, 'r') as f:
            config = json.load(f)

        for handler_config in config.get('hooks', {}).get('custom_handlers', []):
            if not handler_config.get('enabled', True):
                continue

            # 动态加载 Handler
            handler = await self._load_handler(
                handler_config['handler']
            )

            # 注册到管理器
            hook_manager.register(
                HookEvent[handler_config['event']],
                handler,
                priority=handler_config.get('priority', 0)
            )

    async def _load_handler(self, handler_path: str):
        """
        动态加载 Hook Handler

        格式: "module_name:function_name"
        例如: "monitoring:error_reporter"
              → from monitoring import error_reporter
        """
        module_name, func_name = handler_path.split(':')
        module = __import__(module_name)
        return getattr(module, func_name)
```

#### 2. Hook 验证器 (`src/hooks/validator.py`)

```python
class HookConfigValidator:
    """验证 Hook 配置的安全性"""

    def validate_handler_path(self, handler_path: str) -> bool:
        """
        检查 Handler 路径是否安全

        防止：
        - 加载恶意模块
        - 访问私有函数
        - 引入不允许的包
        """
        module_name, func_name = handler_path.split(':')

        # 黑名单检查
        forbidden_modules = [
            'os', 'sys', 'subprocess', 'socket',
            '__builtin__', 'importlib'
        ]

        if module_name in forbidden_modules:
            raise SecurityError(f"Forbidden module: {module_name}")

        # 私有函数检查
        if func_name.startswith('_'):
            raise SecurityError(f"Cannot load private function: {func_name}")

        return True

    def validate_priority(self, priority: int) -> bool:
        """验证优先级范围"""
        if not -1000 <= priority <= 1000:
            raise ValueError("Priority must be between -1000 and 1000")
        return True
```

#### 3. 安全加载 (`src/hooks/secure_loader.py`)

```python
class SecureHookLoader:
    """安全地加载用户定义的 Hook"""

    async def load_hook(self, handler_path: str, sandbox: bool = True):
        """
        安全加载 Hook Handler

        Args:
            handler_path: "module:function" 格式
            sandbox: 是否在沙箱中加载
        """
        if sandbox:
            # 在受限环境中加载
            return await self._load_in_sandbox(handler_path)
        else:
            # 直接加载（需要信任）
            return await self._load_direct(handler_path)

    async def _load_in_sandbox(self, handler_path: str):
        """在沙箱中加载 Hook"""
        # 方案 1: AST 检查（轻量）
        handler = await self._load_direct(handler_path)
        self._audit_handler(handler)
        return handler

    def _audit_handler(self, handler: Callable):
        """审计 Handler 的安全性"""
        import inspect
        source = inspect.getsource(handler)
        # AST 分析，检查是否有危险操作
        ...
```

#### 4. 集成到应用初始化

```python
# src/main.py

async def main():
    """主函数"""
    args = parse_args()

    # 1. 创建 Hook 管理器
    hook_manager = HookManager()

    # 2. 加载系统级 Hook（日志等）
    logging_hook = LoggingHook(...)
    hook_manager.register(HookEvent.ON_USER_INPUT, logging_hook)

    # 3. 💡 加载用户 Hook 配置 (新增)
    config_loader = HookConfigLoader()
    await config_loader.load_hooks(hook_manager)

    # 4. 创建 Agent
    agent = EnhancedAgent(..., hook_manager=hook_manager)

    # ... 后续逻辑
```

### 使用示例

#### 用户创建自定义 Hook

```python
# my_hooks.py
async def custom_logger(context: HookContext):
    """自定义日志处理"""
    print(f"Custom: {context.event} - {context.data}")

async def error_alert(context: HookContext):
    """错误告警"""
    if context.event == HookEvent.ON_ERROR:
        send_alert(context.data['error'])
```

#### 用户配置文件

```json
// .claude/settings.json
{
  "hooks": {
    "custom_handlers": [
      {
        "event": "agent.error",
        "handler": "my_hooks:error_alert",
        "priority": 100,
        "enabled": true
      },
      {
        "event": "tool.execute",
        "handler": "my_hooks:custom_logger",
        "priority": 50,
        "enabled": true
      }
    ]
  }
}
```

### 安全考虑

1. **代码审计**: 加载前进行 AST 分析
2. **沙箱执行**: 关键 Hook 在受限环境中运行
3. **路径检查**: 验证 module:function 格式和白名单
4. **错误隔离**: 用户 Hook 异常不中断系统
5. **权限检查**: 不允许访问敏感系统模块

### 与当前设计的兼容性

✅ **完全兼容**！当前设计已支持：
- [x] 多个 Handler 注册同一事件
- [x] 优先级控制（系统 Hook 高优先级）
- [x] 异常隔离（Hook 异常不中断）
- [x] 异步支持（async/await）

💡 **只需补充**：
- [ ] 配置文件格式定义
- [ ] 配置加载器实现
- [ ] 安全验证机制
- [ ] 动态模块加载

### 实现建议

**时间规划**:
- Phase 1: 基础 Hook 系统 ✅
- Phase 1.5 (可选): 用户 Hook 配置 (1-2 周)
  - 配置加载器
  - 安全验证
  - 集成测试
- Phase 2: 日志系统 (依赖 Phase 1)

---

## 🚀 下一步

Phase 1 完成后，将启动 Phase 2（日志系统），其中 `LoggingHook` 将作为系统默认 Hook 通过 `HookManager` 实现。

如果需要用户 Hook 配置支持，建议在 Phase 1 完成后作为 Phase 1.5 单独实现。

---

## 📊 完成状态

**当前进度**: 25% (设计完成)

- [x] 需求分析
- [x] 设计文档
- [ ] 代码实现
- [ ] 单元测试
- [ ] 集成测试
- [ ] 文档完善
- [ ] 代码审查
- [ ] 提交合并

**预计完成时间**: 2025-11-19

---

**作者**: 架构团队
**最后更新**: 2025-11-12
**下一次更新**: Phase 1 实现开始时
