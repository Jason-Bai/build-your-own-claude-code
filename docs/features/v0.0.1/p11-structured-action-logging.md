P11 - 结构化行动日志系统（Structured Action Logging）

一、功能概述

1.1 问题陈述

真实场景问题：

- ❌ Ctrl+C 强制退出丢失数据 - 用户按下两次 Ctrl+C 后，Session 系统尚未持久化，所有进行中的对话、工具调用、执行历史全部丢失
- ❌ 崩溃无法追溯 - 程序异常退出后，无法知道崩溃前发生了什么
- ❌ 调试困难 - 终端错误一旦滚动过去或窗口关闭就无法查看
- ❌ 无审计追踪 - 生产环境无法追溯"谁在什么时候执行了什么操作"
- ❌ 性能分析受限 - 缺乏历史数据支持趋势分析

解决方案：
实时结构化日志系统，将所有用户交互、LLM 调用、工具执行等行为立即持久化到磁盘，使用 JSON Lines 格式按日分割，提供专用查询工具。

关键收益：

- ✅ 实时持久化 - 每个行动立即写入磁盘，Ctrl+C 也不丢数据
- ✅ 崩溃恢复 - 可追溯崩溃前的完整上下文
- ✅ 审计追踪 - 完整的操作历史记录
- ✅ 调试支持 - 可随时查看历史错误和警告
- ✅ 性能分析 - 历史数据支持趋势分析
- ✅ 合规性 - 满足安全审计要求

---

二、架构设计

2.1 日志文件结构

~/.tiny-claude-code/logs/
├── 2025-11-21.jsonl # 当天日志（热数据，实时写入）
├── 2025-11-20.jsonl # 昨天日志
├── 2025-11-19.jsonl.gz # 压缩的旧日志（7 天后自动压缩）
└── metadata.json # 日志元数据（文件索引、统计信息）

2.2 系统集成架构

                      ┌─────────────────┐
                      │  SessionManager │
                      └────────┬────────┘
                               │
                      ┌────────▼────────┐
                      │ ActionLogger    │◄──────┐
                      │ (async queue)   │       │
                      └────────┬────────┘       │
                               │                │
                      ┌────────▼────────┐       │
                      │  LogWriter      │       │
                      │  (background)   │       │
                      └────────┬────────┘       │
                               │                │
                      实时写入 JSONL Files      │
                      (每批100条或1秒)          │
                                                │
      ┌──────────────────────────────────────────┤
      │                                          │

┌───▼──────┐ ┌──────────┐ ┌──────────┐ ┌──▼───┐
│Enhanced │ │Tool │ │Event │ │CLI │
│Agent │ │Executor │ │Bus │ │Main │
└──────────┘ └──────────┘ └──────────┘ └──────┘

集成点：

1. SessionManager - 记录会话生命周期（start/end/pause/resume）
2. EnhancedAgent - 记录状态变化（IDLE→THINKING→USING_TOOL）
3. ToolExecutor - 记录工具调用（参数、结果、错误）
4. LLM Clients - 记录请求/响应（带数据脱敏）
5. EventBus - 记录系统事件
6. CLI Main - 记录用户输入/命令

2.3 异步日志管道（解决 Ctrl+C 问题）

# 架构组件

QueueHandler (sync) → Queue → Background Thread (async) → File Writer
↑ ↓
调用方 实时批量写入 JSONL
(无阻塞) (100 条/批或 1 秒/批)

Ctrl+C 安全设计：

# 注册信号处理器

def signal_handler(sig, frame):
logger.info("接收到中断信号，正在刷新日志...")
action_logger.flush() # 强制写入队列中的所有日志
sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

性能优化：

- 调用方使用 logger.info()立即返回（无 I/O 阻塞）
- 日志记录进入内存队列（默认队列大小：1000 条）
- 后台线程批量写入磁盘（默认 100 条/批或 1 秒/批，取先到者）
- Ctrl+C 时强制刷新队列，确保数据不丢失
- 预期性能影响：< 1ms per action

---

三、JSON Schema 定义

3.1 通用字段（所有日志共享）

{
"timestamp": "2025-11-21T14:32:15.123456",
"action_number": 1234,
"action_type": "tool_call",
"session_id": "session-20251121143210-123456",
"execution_id": "exec-abc123",
"status": "success"
}

3.2 用户交互类

USER_INPUT

{
"action_type": "user_input",
"content": "帮我实现一个登录功能",
"input_mode": "interactive"
}

USER_COMMAND

{
"action_type": "user_command",
"command": "/status",
"args": []
}

3.3 Agent 状态类

AGENT_STATE_CHANGE

{
"action_type": "agent_state_change",
"from_state": "IDLE",
"to_state": "THINKING",
"reason": "user_request"
}

AGENT_THINKING

{
"action_type": "agent_thinking",
"thinking_content": "[MASKED]",
"duration_ms": 1234
}

3.4 LLM 交互类

LLM_REQUEST

{
"action_type": "llm_request",
"provider": "anthropic",
"model": "claude-sonnet-4-5-20250929",
"messages_count": 5,
"tools_count": 8,
"temperature": 0.7,
"max_tokens": 4000,
"request_id": "req-xyz789"
}

LLM_RESPONSE

{
"action_type": "llm_response",
"request_id": "req-xyz789",
"response_type": "tool_use",
"tool_calls": [
{"tool": "read_file", "tool_use_id": "toolu_abc123"}
],
"input_tokens": 1234,
"output_tokens": 567,
"duration_ms": 2345,
"status": "success"
}

LLM_ERROR

{
"action_type": "llm_error",
"request_id": "req-xyz789",
"error_type": "rate_limit_error",
"error_message": "Rate limit exceeded",
"retry_after": 60
}

3.5 工具执行类

TOOL_CALL

{
"action_type": "tool_call",
"tool_name": "bash",
"tool_use_id": "toolu_abc123",
"args": {
"command": "ls -la",
"description": "List files"
},
"permission_level": "NORMAL"
}

TOOL_RESULT

{
"action_type": "tool_result",
"tool_use_id": "toolu_abc123",
"success": true,
"output": "[TRUNCATED 1000 chars]",
"duration_ms": 123,
"status": "success"
}

TOOL_ERROR

{
"action_type": "tool_error",
"tool_use_id": "toolu_abc123",
"error_type": "execution_error",
"error_message": "Command not found: xyz",
"status": "error"
}

TOOL_PERMISSION

{
"action_type": "tool_permission",
"tool_use_id": "toolu_abc123",
"permission_level": "DANGEROUS",
"user_decision": "approved",
"decision_time_ms": 5678
}

3.6 会话生命周期类

SESSION_START/END/PAUSE/RESUME

{
"action_type": "session_start",
"project_name": "my-project",
"session_id": "session-20251121143210-123456",
"metadata": {
"python_version": "3.10.12",
"platform": "darwin"
}
}

3.7 Hook 执行类

HOOK_EXECUTE

{
"action_type": "hook_execute",
"hook_name": "on_tool_execute",
"hook_type": "command",
"duration_ms": 45,
"status": "success"
}

3.8 系统事件类

SYSTEM_ERROR/SYSTEM_WARNING

{
"action_type": "system_error",
"component": "mcp_server",
"error_message": "Failed to connect to filesystem server",
"traceback": "[MASKED]",
"status": "error"
}

---

四、隐私与安全设计

4.1 数据脱敏规则

自动脱敏的敏感数据：

1. API 密钥 - 匹配模式：sk-[a-zA-Z0-9]{48}, Bearer xxx
2. 密码 - 字段名：password, passwd, secret, token
3. 个人信息 - 邮箱、手机号（可选，通过正则匹配）
4. 文件路径 - 用户目录路径（如/Users/baiyu/ → /Users/[USER]/）

脱敏方式：

# 示例

"api_key": "sk-ant-api03-abc...xyz" → "api_key": "sk-**_[MASKED 44 chars]_**"
"password": "secret123" → "password": "[MASKED]"

4.2 可配置敏感字段

# settings.json

{
"logging": {
"mask_sensitive_data": true,
"custom_sensitive_fields": ["internal_token", "ssh_key"],
"mask_thinking": true,
"truncate_large_output": true,
"max_output_chars": 1000
}
}

4.3 隐私模式

# 完全禁用日志

{
"logging": {
"enabled": false
}
}

---

五、磁盘管理设计

5.1 保留策略

默认策略：

- 时间保留：30 天（可配置）
- 空间限制：1GB 总大小（可配置）
- 触发条件：任一条件达到即触发清理

# settings.json

{
"logging": {
"retention_days": 30,
"max_total_size_mb": 1024,
"cleanup_on_startup": true
}
}

5.2 自动清理机制

# 清理逻辑

1. 扫描 logs/目录
2. 按时间排序所有.jsonl 和.jsonl.gz 文件
3. 删除超过 retention_days 的文件
4. 如果总大小仍超过 max_total_size_mb，删除最旧的文件直到满足限制

5.3 日志压缩（可选）

# 7 天前的日志自动压缩

2025-11-14.jsonl → 2025-11-14.jsonl.gz

# 压缩比：通常 5:1 到 10:1

---

六、查询工具设计

6.1 命令行工具：/log

命令格式：

# 基本查询（查看今天的日志）

/log

# 指定日期

/log --date 2025-11-21
/log --date-range 2025-11-15:2025-11-21

# 按类型过滤

/log --action-type tool_call
/log --action-type llm_request,llm_response

# 按会话过滤

/log --session-id session-20251121143210-123456

# 按状态过滤

/log --status error
/log --status success --tool-name bash

# 关键词搜索

/log --keyword "authentication"
/log --content-match "Failed to connect"

# 输出格式

/log --format json # JSON 数组
/log --format table # 表格（默认）
/log --format summary # 统计摘要

# 限制结果数量

/log --limit 50
/log --tail 20 # 最后 20 条

# 组合示例

/log --date 2025-11-21 --action-type tool_error --tool-name bash --format table

6.2 查询工具输出示例

表格格式（默认）：
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Timestamp ┃ Action Type ┃ Tool ┃ Status ┃ Message ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ 14:32:15.123 │ tool_error │ bash │ error │ Command not found │
│ 14:35:22.456 │ tool_call │ read_file │ success │ Read config.json │
└──────────────┴───────────────┴────────────┴─────────┴────────────────────┘

Showing 2 of 1,234 total actions

统计摘要格式：
=== 日志统计摘要 (2025-11-21) ===

总行动数: 1,234
会话数: 3
错误数: 12

按类型分布: - tool_call: 456 (37%) - llm_request: 234 (19%) - user_input: 123 (10%) - agent_state_change: 421 (34%)

按状态分布: - success: 1,222 (99%) - error: 12 (1%)

错误类型: - tool_error: 8 - llm_error: 3 - system_error: 1

磁盘使用: - 今日日志大小: 2.3 MB - 总日志大小: 45.6 MB (30 天)

6.3 程序化 API（供内部使用）

from src.logging import LogQueryEngine

# Python API

query = LogQueryEngine()
results = query.filter(
date_range=("2025-11-20", "2025-11-21"),
action_types=["tool_call", "tool_error"],
session_id="session-20251121143210-123456",
status="error"
).limit(100).execute()

# 返回: List[Dict[str, Any]]

for record in results:
print(record['timestamp'], record['action_type'], record['status'])

---

七、配置设计

7.1 新用户默认配置（templates/settings.json）

文件路径: templates/settings.json

{
"model": {
"provider": "anthropic",
"temperature": 0.7,
"max_tokens": 4000
},
"providers": {
"anthropic": {
"api_key": "",
"model_name": "claude-sonnet-4-5-20250929"
},
"openai": {
"api_key": "",
"model_name": "gpt-4o"
},
"kimi": {
"api_key": "",
"model_name": "moonshot-v1-auto"
}
},
"mcp_servers": [],
"hooks": [],
"logging": {
"enabled": true,
"log_dir": "~/.tiny-claude-code/logs",

      "async_logging": true,
      "queue_size": 1000,
      "batch_size": 100,
      "batch_timeout_sec": 1,

      "mask_sensitive_data": true,
      "custom_sensitive_fields": [],
      "mask_thinking": false,
      "truncate_large_output": true,
      "max_output_chars": 1000,

      "retention_days": 30,
      "max_total_size_mb": 1024,
      "cleanup_on_startup": true,
      "compress_after_days": 7,

      "action_types": {
        "user_input": true,
        "user_command": true,
        "agent_state_change": true,
        "agent_thinking": false,
        "llm_request": true,
        "llm_response": true,
        "llm_error": true,
        "tool_call": true,
        "tool_result": true,
        "tool_error": true,
        "tool_permission": true,
        "session_start": true,
        "session_end": true,
        "session_pause": true,
        "session_resume": true,
        "hook_execute": false,
        "hook_error": true,
        "system_error": true,
        "system_warning": true
      }
    }

}

关键默认值说明：

- enabled: true - 默认启用日志（用户可通过配置禁用）
- async_logging: true - 使用异步日志避免性能影响
- mask_sensitive_data: true - 默认启用数据脱敏保护隐私
- mask_thinking: false - 默认不脱敏 agent 思考内容（便于调试）
- agent_thinking: false - 默认不记录思考内容（减少日志量）
- hook_execute: false - 默认不记录 hook 执行（减少噪音）
- retention_days: 30 - 保留 30 天日志
- max_total_size_mb: 1024 - 最大 1GB 磁盘占用

  7.2 用户配置示例（~/.tiny-claude-code/settings.json）

完整配置（文档示例）：
{
"model": {
"provider": "kimi",
"temperature": 0.7,
"max_tokens": 4000
},
"providers": {
"anthropic": {
"api_key": "your-anthropic-key",
"model_name": "claude-sonnet-4.5"
},
"openai": {
"api_key": "your-openai-key",
"model_name": "gpt-4o"
},
"kimi": {
"api_key": "your-kimi-key",
"model_name": "moonshot-v1-auto"
}
},
"mcp_servers": [
{
"name": "filesystem",
"command": "npx",
"args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
"enabled": true
}
],
"logging": {
"enabled": true,
"log_dir": "~/.tiny-claude-code/logs",

      "async_logging": true,
      "queue_size": 1000,
      "batch_size": 100,
      "batch_timeout_sec": 1,

      "mask_sensitive_data": true,
      "custom_sensitive_fields": ["internal_token", "ssh_key"],
      "mask_thinking": true,
      "truncate_large_output": true,
      "max_output_chars": 1000,

      "retention_days": 30,
      "max_total_size_mb": 1024,
      "cleanup_on_startup": true,
      "compress_after_days": 7,

      "action_types": {
        "user_input": true,
        "user_command": true,
        "agent_state_change": true,
        "agent_thinking": false,
        "llm_request": true,
        "llm_response": true,
        "llm_error": true,
        "tool_call": true,
        "tool_result": true,
        "tool_error": true,
        "tool_permission": true,
        "session_start": true,
        "session_end": true,
        "session_pause": true,
        "session_resume": true,
        "hook_execute": false,
        "hook_error": true,
        "system_error": true,
        "system_warning": true
      }
    }

}

最小化配置（只需启用）：
{
"logging": {
"enabled": true
}
}

禁用日志配置：
{
"logging": {
"enabled": false
}
}

7.3 配置字段详解

| 配置项                  | 类型   | 默认值                   | 说明                           |
| ----------------------- | ------ | ------------------------ | ------------------------------ |
| enabled                 | bool   | true                     | 是否启用日志系统               |
| log_dir                 | string | ~/.tiny-claude-code/logs | 日志文件存储目录               |
| async_logging           | bool   | true                     | 是否使用异步日志（推荐开启）   |
| queue_size              | int    | 1000                     | 异步队列大小                   |
| batch_size              | int    | 100                      | 批量写入大小（100 条/批）      |
| batch_timeout_sec       | float  | 1.0                      | 批量写入超时（1 秒/批）        |
| mask_sensitive_data     | bool   | true                     | 是否脱敏敏感数据               |
| custom_sensitive_fields | list   | []                       | 自定义敏感字段名列表           |
| mask_thinking           | bool   | false                    | 是否脱敏 agent 思考内容        |
| truncate_large_output   | bool   | true                     | 是否截断超长输出               |
| max_output_chars        | int    | 1000                     | 输出最大字符数                 |
| retention_days          | int    | 30                       | 日志保留天数                   |
| max_total_size_mb       | int    | 1024                     | 日志总大小限制（MB）           |
| cleanup_on_startup      | bool   | true                     | 启动时自动清理过期日志         |
| compress_after_days     | int    | 7                        | N 天后自动压缩日志             |
| action_types.\*         | bool   | varies                   | 各类行动类型的开关（详见上表） |

---

八、实现阶段

Phase 1: MVP (核心功能)

工期: 3 天

功能：

- ✅ 基础 ActionLogger 类（async 版本，QueueHandler + 后台线程）
- ✅ JSON Lines 写入器（带 Ctrl+C 信号处理）
- ✅ 按日分割逻辑
- ✅ 核心 action types（10 个）：
  - USER_INPUT, USER_COMMAND
  - AGENT_STATE_CHANGE
  - LLM_REQUEST, LLM_RESPONSE
  - TOOL_CALL, TOOL_RESULT, TOOL_ERROR
  - SESSION_START, SESSION_END
- ✅ 集成到 SessionManager、EnhancedAgent、ToolExecutor
- ✅ 基础数据脱敏（API 密钥、密码字段）
- ✅ 更新配置模板（templates/settings.json）

测试：

- 单元测试：日志写入、日期分割、数据脱敏、Ctrl+C 处理
- 集成测试：完整流程日志记录、强制退出数据完整性

Phase 2: 增强功能

工期: 2 天

功能：

- ✅ 完整 action types（19 个）
- ✅ 高级数据脱敏（正则匹配、自定义字段）
- ✅ 磁盘管理（保留策略、自动清理）
- ✅ 基础查询工具（/log 命令，支持基本过滤）

测试：

- 性能测试：异步日志吞吐量
- 压力测试：大量日志写入

Phase 3: 生产就绪

工期: 2 天

功能：

- ✅ 日志压缩（旧日志自动压缩）
- ✅ 完整查询工具（所有过滤条件、输出格式）
- ✅ 程序化 API（LogQueryEngine）
- ✅ 配置验证和默认值处理
- ✅ 监控和告警（日志写入失败告警）

测试：

- E2E 测试：完整用户场景
- 边界测试：磁盘满、权限错误、配置错误

---

九、与 Session 系统的关系

9.1 互补架构（非替代）

| 方面        | Session 系统                     | Logging 系统                              |
| ----------- | -------------------------------- | ----------------------------------------- |
| 目的        | 状态恢复、会话管理               | 审计追踪、调试分析、崩溃保护              |
| 写入时机    | 会话结束时批量保存               | 每个行动实时写入                          |
| Ctrl+C 行为 | ❌ 数据丢失                      | ✅ 数据安全（信号处理器强制刷新）         |
| 存储格式    | Python 对象序列化（pickle/json） | JSON Lines（行式）                        |
| 查询方式    | 加载整个会话对象                 | 按行过滤、聚合统计                        |
| 典型用例    | 恢复中断的会话、切换会话         | Ctrl+C 后查看丢失内容、崩溃排查、性能分析 |

9.2 数据流关系

用户行动
│
├──► ActionLogger.log() ──► Queue ──► Background Thread ──► JSONL 文件 (实时)
│ ↑
│ Ctrl+C 时强制刷新
│
└──► Session.record_xxx() ──► Session 对象 (内存)
│
└──► PersistenceManager (会话结束时)

9.3 不会破坏现有架构

- ✅ 零侵入：通过 event hooks 集成，无需修改核心逻辑
- ✅ 可选功能：通过配置禁用日志不影响 Session 系统
- ✅ 独立存储：日志文件和 Session 文件完全分离

---

十、测试策略

10.1 单元测试

# tests/unit/test_action_logger.py

- test_log_writing()
- test_date_rotation()
- test_data_masking()
- test_json_schema_validation()
- test_ctrl_c_signal_handling() # 新增：测试 Ctrl+C 安全
- test_queue_flush() # 新增：测试队列刷新

# tests/unit/test_log_query.py

- test_date_filter()
- test_action_type_filter()
- test_status_filter()

  10.2 集成测试

# tests/integration/test_logging_integration.py

- test_full_session_logging()
- test_tool_execution_logging()
- test_llm_interaction_logging()
- test_error_logging()
- test_force_exit_data_integrity() # 新增：测试强制退出数据完整性

  10.3 性能测试

# tests/performance/test_logging_performance.py

- test_async_logging_overhead() # < 1ms/action
- test_async_logging_throughput() # > 1000 actions/sec
- test_disk_usage() # 压缩比验证

---

十一、潜在风险与缓解措施

### 11.1 基础风险列表

| 风险                 | 影响 | 缓解措施                                  |
| -------------------- | ---- | ----------------------------------------- |
| Ctrl+C 数据丢失      | 高   | ✅ 信号处理器强制刷新队列                 |
| 日志文件过大         | 高   | ✅ 自动清理、压缩、可配置保留策略         |
| 敏感数据泄露         | 高   | ✅ 默认脱敏、可配置脱敏规则、隐私模式     |
| 性能开销             | 中   | ✅ 异步日志、批量写入、可禁用详细日志     |
| 磁盘写入失败         | 中   | ✅ 降级到 stderr、告警通知                |
| 查询工具性能         | 低   | ✅ JSONL 格式支持流式解析、无需加载全文件 |
| 配置错误导致系统失败 | 中   | ✅ 配置验证、默认值回退、优雅降级         |

### 11.2 深度风险分析与改进建议

#### 11.2.1 队列满时的策略 ⚠️ 中高风险

**风险描述**：
在极端情况下（磁盘I/O慢、大量日志突发），队列可能满载（默认1000条）。当前设计采用丢弃策略（drop），可能丢失关键错误信息。

**改进方案**：
```python
# 分级队列 + 配置化策略
{
  "logging": {
    "queue_full_strategy": {
      "default": "drop_oldest",      # 普通日志：丢弃最旧的
      "critical_levels": ["error", "llm_error", "system_error", "tool_error"],
      "critical_strategy": "block_with_timeout",  # 关键日志：阻塞最多3秒
      "critical_timeout_sec": 3
    }
  }
}
```

**实现优先级**：
- **Phase 1 (MVP)**: 使用简单的 `drop_oldest` 策略（Python Queue 默认行为）
- **Phase 2**: 实现分级策略（高成本/收益比）

**理由**：队列大小1000足够覆盖99%场景，真正需要分级策略的场景极少（除非磁盘故障）。

---

#### 11.2.2 后台线程的异常处理 🔴 高风险

**风险描述**：
如果 `_worker` 线程内部发生未捕获异常导致线程退出，日志系统将静默失效，用户无感知。

**改进方案**：
```python
# 健康检查 + 自动重启 + 降级
class ActionLogger:
    def __init__(self):
        self._worker_thread = None
        self._worker_alive = True
        self._last_heartbeat = time.time()
        self._start_worker()

    def _worker(self):
        try:
            while self._running:
                # ... 日志处理逻辑 ...
                self._last_heartbeat = time.time()  # 心跳
        except Exception as e:
            logger.error(f"Worker thread crashed: {e}")
            self._worker_alive = False

    def log(self, action_data: dict):
        # 健康检查
        if not self._is_worker_healthy():
            logger.warning("Worker unhealthy, attempting restart...")
            if not self._restart_worker():
                # 降级到同步模式
                logger.warning("Fallback to synchronous logging")
                self._sync_write(action_data)
                return

        # 正常异步写入
        self._queue.put_nowait(action_data)

    def _is_worker_healthy(self) -> bool:
        if not self._worker_thread.is_alive():
            return False
        if time.time() - self._last_heartbeat > 10:  # 10秒无心跳
            return False
        return True
```

**实现优先级**：
- **Phase 1 (MVP)**: ✅ **必须实现** - 至少需要异常捕获 + 降级到同步模式

**理由**：线程崩溃的代价太高（丢失所有后续日志），实现成本不高（~50行代码），这是防御性编程的典范。

---

#### 11.2.3 日志轮转的原子性 🟡 低风险（当前），中风险（未来）

**风险描述**：
多进程环境下（虽然当前是单进程CLI），简单的文件打开/关闭可能会有竞争条件。

**改进方案**：
```python
# 文件锁 + 原子重命名
import fcntl

class LogWriter:
    def _rotate_if_needed(self):
        current_date = datetime.now().date()
        if current_date != self._current_date:
            # 使用文件锁保护轮转操作
            lock_file = self.log_dir / ".rotation.lock"
            with open(lock_file, 'w') as f:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self._do_rotate(current_date)
                except BlockingIOError:
                    # 其他进程正在轮转，跳过
                    pass
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

**实现优先级**：
- **Phase 1 (MVP)**: ❌ 不实现（单进程无需）
- **Phase 3 (Production)**: ✅ 实现（为未来扩展做准备）

**理由**：当前单进程CLI架构无此风险，但如果未来支持多实例、服务器模式、分布式部署，则必须实现。

---

#### 11.2.4 性能优化 🟢 低风险，优化机会

**风险描述**：
Python 的标准 `json` 库在处理大量数据时性能一般（~1000 logs/sec）。

**改进方案**：
```python
# 可选依赖 + 自动降级
try:
    import orjson as json_lib
    FAST_JSON = True
except ImportError:
    import json as json_lib
    FAST_JSON = False

class LogWriter:
    def _serialize(self, data: dict) -> bytes:
        if FAST_JSON:
            return orjson.dumps(data)  # 返回bytes，3-5倍速度提升
        else:
            return json_lib.dumps(data).encode('utf-8')
```

**性能对比**：
- 标准 `json`: ~1000 logs/sec
- `orjson`: ~3000-5000 logs/sec

**实现优先级**：
- **Phase 1 (MVP)**: 使用标准 `json`
- **Phase 2**: 添加 `orjson` 作为可选依赖
  ```python
  # setup.py
  extras_require = {
      'performance': ['orjson>=3.8.0']
  }
  ```

**理由**：MVP阶段无需过早优化，对于CLI工具标准 `json` 已足够。如果未来日志量达到10k+ logs/sec，再引入 `orjson`。

---

#### 11.2.5 查询工具的复杂性 🟡 中等复杂度

**风险描述**：
`/log` 命令设计了非常丰富的过滤功能（日期、类型、Session ID、关键词等）。在 V1 版本中全部实现可能工作量较大，阻碍核心功能上线。

**改进方案（分阶段实现）**：

**Phase 1 (MVP)** - 基础查询（3天工作量）：
```bash
/log                           # 查看今天所有日志（最后50条）
/log --tail 100                # 最后100条
/log --date 2025-11-21         # 指定日期
/log --keyword "error"         # 关键词搜索（简单字符串匹配）
/log --format table|json       # 输出格式
```

**Phase 2 (Enhanced)** - 结构化过滤（2天工作量）：
```bash
/log --action-type tool_error  # 按类型过滤
/log --status error            # 按状态过滤
/log --session-id xxx          # 按会话过滤
```

**Phase 3 (Production)** - 高级功能（2天工作量）：
```bash
/log --date-range 2025-11-15:2025-11-21  # 日期范围
/log --format summary          # 统计摘要
/log --limit 50                # 结果限制
```

**实现技巧（流式解析）**：
```python
# 避免加载整个文件
def query_logs(date: str, filters: dict):
    log_file = LOG_DIR / f"{date}.jsonl"
    results = []

    with open(log_file, 'r') as f:
        for line in f:
            record = json.loads(line)
            if _match_filters(record, filters):
                results.append(record)
                if len(results) >= filters.get('limit', 1000):
                    break

    return results
```

**理由**：查询工具的复杂度不应阻碍日志系统上线。先实现核心功能（tail + grep），验证用户需求，根据实际使用反馈迭代功能。

---

### 11.3 风险优先级总结

| 风险项               | 风险等级 | MVP是否必须 | 实现成本 | 实现阶段 | 建议                          |
|----------------------|----------|-------------|----------|----------|-------------------------------|
| 队列满策略           | 🟡 中    | ❌ 否       | 中       | Phase 2  | 实现分级策略（高收益）         |
| 后台线程异常处理     | 🔴 高    | ✅ **是**   | 低       | Phase 1  | **MVP必须实现降级机制**        |
| 日志轮转原子性       | 🟢 低    | ❌ 否       | 低       | Phase 3  | 为未来多进程扩展准备           |
| 性能优化（orjson）   | 🟢 低    | ❌ 否       | 低       | Phase 2  | 作为可选依赖                  |
| 查询工具复杂性       | 🟡 中    | ⚠️ 部分     | 中       | Phase 1-3| **MVP实现tail+grep即可**       |

**关键原则**：
- ✅ **"先求有，再求好"** - MVP优先验证核心价值（实时日志 + Ctrl+C安全）
- ✅ **"防御性编程"** - 后台线程异常处理必须有（🔴 高风险）
- ✅ **"按需优化"** - 性能优化等有真实数据后再做（避免过早优化）

---

十二、未来扩展

Phase 4+（可选）

- 📊 日志可视化工具 - Web 界面展示日志统计
- 📡 远程日志上传 - 支持上传到中心化日志服务
- 🔍 全文搜索引擎 - 集成 Elasticsearch/SQLite FTS
- 🔔 实时告警 - 错误率阈值告警
- 📈 性能分析报告 - 自动生成性能优化建议
- 🔄 日志回放 - 基于日志重现用户操作（用于调试）

---

十三、关键改进总结

相比初版方案，本次修订的关键改进：

1. ✅ Ctrl+C 问题解决 - 添加信号处理器，强制退出时刷新队列确保数据不丢失
2. ✅ 命令简化 - /claude-logs → /log（符合项目命名风格）
3. ✅ 配置模板补充 - 新增 templates/settings.json 的完整 logging 配置
4. ✅ 文档配置示例 - 补充 ~/.tiny-claude-code/settings.json 的详细说明
5. ✅ 默认值优化 - 明确各配置项的默认值和推荐设置
6. ✅ 测试用例补充 - 新增 Ctrl+C 相关测试用例
