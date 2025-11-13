# 功能：P5 - 条件路由（Conditional Routing）

**日期**: 待实现
**优先级**: P1 🟡
**难度**: ⭐⭐
**预计周期**: 1 周
**状态**: 📋 未开始

---

## 概述

实现一个**智能条件路由系统**，根据用户输入、上下文信息和预定义规则，自动将任务路由到最合适的 Agent、工具或处理器，支持复杂的流程控制和任务分类。

---

## 问题描述

### 当前状况

当前系统采用单一的 Agent 线性处理：

```python
# ❌ 单一流程，无法适应不同场景
agent.run(query)
```

**限制**：
- 所有请求采用相同的处理流程
- 无法针对不同类型的任务优化
- 复杂任务需要手动分解
- 无法根据上下文做出动态决策

### 期望改进

需要一个**智能路由系统**，能够：
- 自动分类任务类型
- 根据条件选择处理器
- 支持多条件组合
- 支持流程跳转和条件分支
- 记录路由决策

---

## 设计方案

### 核心架构

```
用户输入
  ↓
分析请求 (Request Analyzer)
  ├─ 提取意图
  ├─ 识别实体
  ├─ 分析上下文
  └─ 计算优先级
  ↓
条件评估 (Condition Evaluator)
  ├─ 关键字匹配
  ├─ 模式匹配
  ├─ ML 分类（可选）
  └─ 上下文判断
  ↓
规则匹配 (Rule Matcher)
  ├─ 顺序匹配规则
  ├─ 优先级排序
  └─ 选择最优规则
  ↓
选择处理器 (Handler Selection)
  ├─ Agent
  ├─ 工具集
  ├─ 自定义处理器
  └─ 外部服务
  ↓
执行处理器
  ├─ 传递参数
  ├─ 监控执行
  └─ 处理结果
  ↓
返回结果
```

### 条件类型

#### 1. 文本条件
```python
# 关键字匹配
TextCondition(
    contains=["error", "bug"],
    case_sensitive=False
)

# 正则表达式
RegexCondition(
    pattern=r"^(show|list)\s+(files|directories)"
)

# 相似度匹配
SimilarityCondition(
    text="show all files",
    threshold=0.8
)
```

#### 2. 上下文条件
```python
# 消息数量
ContextCondition(
    message_count__gt=5,
    message_count__lt=100
)

# 上次错误
ErrorCondition(
    last_error_type="PermissionError",
    occurrence_count__gt=1
)

# 用户权限
PermissionCondition(
    user_role="admin",
    required_permissions=["write", "execute"]
)
```

#### 3. 组合条件
```python
# AND 条件
AndCondition(
    TextCondition(contains=["file"]),
    ContextCondition(message_count__gt=3)
)

# OR 条件
OrCondition(
    TextCondition(contains=["show"]),
    TextCondition(contains=["list"])
)

# NOT 条件
NotCondition(
    TextCondition(contains=["delete"])
)
```

### 规则定义

```python
class Route:
    """路由规则"""

    name: str              # 路由名称
    priority: int          # 优先级（越高越先匹配）
    condition: Condition   # 条件
    handler: Callable      # 处理器
    metadata: dict         # 元数据

# 示例规则
routes = [
    Route(
        name="show_files",
        priority=100,
        condition=TextCondition(
            contains=["show", "list"],
            keywords=["files", "directory"]
        ),
        handler=file_list_handler,
        metadata={"type": "file_operation"}
    ),

    Route(
        name="execute_code",
        priority=90,
        condition=TextCondition(
            contains=["run", "execute"],
            keywords=["code", "script", "python"]
        ),
        handler=code_execution_handler,
        metadata={"type": "code_execution", "requires_permission": "execute"}
    ),

    Route(
        name="error_recovery",
        priority=50,
        condition=ErrorCondition(
            last_error_type="PermissionError",
            occurrence_count__gt=1
        ),
        handler=error_recovery_handler,
        metadata={"type": "error_handling"}
    ),
]
```

### 路由决策树

```
输入: "show all files in /home"
  ├─ 文本条件 (优先级 100)
  │  ├─ 包含 "show" ✓
  │  ├─ 包含 "files" ✓
  │  └─ 匹配成功
  │
  ├─ 处理器选择
  │  └─ file_list_handler
  │
  └─ 执行路由

输入: "I got a permission error again"
  ├─ 文本条件 (优先级 100)
  │  ├─ 包含 "show" ✗
  │  └─ 匹配失败
  │
  ├─ 错误条件 (优先级 50)
  │  ├─ 最后错误: PermissionError ✓
  │  ├─ 出现次数 > 1 ✓
  │  └─ 匹配成功
  │
  ├─ 处理器选择
  │  └─ error_recovery_handler
  │
  └─ 执行路由
```

---

## 实现细节

### 核心组件

#### 1. RequestAnalyzer（请求分析器）
```python
class RequestAnalyzer:
    """分析用户请求"""

    async def analyze(self, text: str, context: Context) -> RequestInfo:
        """分析请求"""
        return RequestInfo(
            original_text=text,
            intent=self._extract_intent(text),
            entities=self._extract_entities(text),
            keywords=self._extract_keywords(text),
            urgency=self._calculate_urgency(text),
            context_score=self._analyze_context(context)
        )

    def _extract_intent(self, text: str) -> str:
        """提取意图"""
        pass

    def _extract_entities(self, text: str) -> List[Entity]:
        """提取实体"""
        pass

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键字"""
        pass
```

#### 2. ConditionEvaluator（条件评估器）
```python
class ConditionEvaluator:
    """评估条件"""

    async def evaluate(
        self,
        condition: Condition,
        request_info: RequestInfo,
        context: Context
    ) -> bool:
        """评估条件是否满足"""
        if isinstance(condition, TextCondition):
            return self._evaluate_text(condition, request_info)
        elif isinstance(condition, ContextCondition):
            return self._evaluate_context(condition, context)
        elif isinstance(condition, AndCondition):
            return all(
                await self.evaluate(c, request_info, context)
                for c in condition.conditions
            )
        elif isinstance(condition, OrCondition):
            return any(
                await self.evaluate(c, request_info, context)
                for c in condition.conditions
            )
        # ... 其他条件类型
        return False

    def _evaluate_text(
        self,
        condition: TextCondition,
        request_info: RequestInfo
    ) -> bool:
        """评估文本条件"""
        pass
```

#### 3. Router（路由器）
```python
class Router:
    """路由管理器"""

    def __init__(self, routes: List[Route]):
        self.routes = sorted(routes, key=lambda r: r.priority, reverse=True)
        self.evaluator = ConditionEvaluator()
        self.analyzer = RequestAnalyzer()

    async def route(
        self,
        text: str,
        context: Context
    ) -> Tuple[Route, Any]:
        """路由请求到合适的处理器"""

        # 分析请求
        request_info = await self.analyzer.analyze(text, context)

        # 按优先级匹配规则
        for route in self.routes:
            if await self.evaluator.evaluate(
                route.condition,
                request_info,
                context
            ):
                # 记录路由决策
                await self._log_routing_decision(
                    route=route,
                    request_info=request_info,
                    matched=True
                )

                # 执行处理器
                result = await route.handler(text, context)
                return route, result

        # 没有匹配的规则，使用默认处理器
        return self._default_route(text, context)

    async def _log_routing_decision(
        self,
        route: Route,
        request_info: RequestInfo,
        matched: bool
    ):
        """记录路由决策"""
        pass
```

### 文件修改

- `src/routing/analyzer.py` - 请求分析器
- `src/routing/condition.py` - 条件定义
- `src/routing/evaluator.py` - 条件评估器
- `src/routing/router.py` - 路由器
- `src/routing/config.py` - 路由配置

---

## 应用场景

### 场景 1: 任务分类
```
输入: "show all files"
路由: file_operations_agent
处理: 列出文件列表

输入: "run my script"
路由: code_execution_agent
处理: 执行脚本
```

### 场景 2: 错误处理
```
输入: "permission denied again"
条件: 最后错误 = PermissionError AND 出现次数 > 1
路由: error_recovery_handler
处理: 建议权限修复
```

### 场景 3: 优先级处理
```
输入: "This is urgent! System is down!"
条件: 包含"urgent"且消息长度 > 5
路由: priority_agent
处理: 高优先级处理
```

---

## 工作原理

### 路由流程

```
1. 请求到达
   ↓
2. RequestAnalyzer 分析
   - 提取意图、实体、关键字
   - 计算上下文相关性
   ↓
3. 按优先级遍历规则
   ↓
4. 条件评估
   ├─ 文本条件：关键字/模式匹配
   ├─ 上下文条件：上下文检查
   ├─ 组合条件：多条件判断
   └─ 自定义条件：业务逻辑
   ↓
5. 规则匹配
   ├─ 匹配成功 → 记录决策 → 执行处理器
   └─ 全部失败 → 使用默认处理器
   ↓
6. 返回结果
```

---

## 测试验证

### 测试用例

#### 1. 文本条件匹配
```python
# 测试关键字匹配
route("show files") → file_operations
route("list files") → file_operations
route("execute script") → code_execution
```

#### 2. 上下文条件匹配
```python
# 测试消息计数
route(text, context_with_10_messages) → special_agent
route(text, context_with_2_messages) → normal_agent
```

#### 3. 组合条件匹配
```python
# 测试 AND 条件
route("show urgent files") → priority_file_handler

# 测试 OR 条件
route("list files") → file_handler  # 第一个 OR 条件匹配
route("show files") → file_handler  # 第二个 OR 条件匹配
```

#### 4. 优先级排序
```python
# 高优先级规则优先匹配
route("show error again") → error_recovery (优先级 100)
              ↓ (不匹配其他条件)
→ default_handler (优先级 0)
```

---

## 性能影响

### 评估

- **条件评估**: ~1-5ms（取决于条件复杂度）
- **规则匹配**: O(n)，n 为规则数量
- **整体开销**: < 10ms（通常）

### 优化策略

- 规则缓存
- 条件短路（AND/OR 优化）
- 倒排索引（关键字快速查询）
- 编译正则表达式

---

## 相关资源

- **路由算法**: https://en.wikipedia.org/wiki/Routing
- **规则引擎**: https://en.wikipedia.org/wiki/Business_rules_engine
- **条件逻辑**: https://en.wikipedia.org/wiki/Boolean_algebra

---

## 常见问题

### Q: 如何添加新的路由规则？
**A**: 创建新的 Route 对象，添加到路由列表中。

### Q: 如何调试路由决策？
**A**: 通过日志记录和可视化界面查看路由决策过程。

### Q: 性能如何？
**A**: 条件评估通常 < 10ms，对应用性能影响最小。

### Q: 支持动态规则吗？
**A**: 支持，可以在运行时添加、删除、修改规则。

---

**实现者**: 待安排
**状态**: 📋 未开始
**依赖**: Phase 1 (Hooks 系统)
**相关 Phase**: Phase 3 (沙箱执行)
