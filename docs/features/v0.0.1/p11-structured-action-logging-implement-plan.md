P11 结构化行动日志系统 - 设计方案：./p11-structured-action-logging.md

---

P11 结构化行动日志系统 - 实现计划

📋 实施概览

总工期: 7 个工作日（3 天 + 2 天 + 2 天）
实施模式: 三个 Phase 递进式开发
关键里程碑: MVP → Enhanced → Production Ready

---

Phase 1: MVP（核心功能）- 3 个工作日

目标

验证核心价值：实时日志持久化 + Ctrl+C 安全 + 基础查询

任务分解

Day 1: 日志基础架构（6-8 小时）

1.1 创建日志模块结构
src/logging/
├── **init**.py
├── action_logger.py # 核心日志器
├── log_writer.py # 文件写入器
├── types.py # 数据类型定义
└── constants.py # 常量（action types 等）

1.2 实现 ActionLogger 类

- ✅ 异步队列（QueueHandler）
- ✅ 后台线程（background worker）
- ✅ 健康检查机制（❗ 高优先级，11.2.2）
  - 心跳检测
  - 自动重启
  - 降级到同步模式
- ✅ Ctrl+C 信号处理器（SIGINT）
- ✅ flush() 方法（强制刷新队列）

关键代码框架：

# src/logging/action_logger.py

class ActionLogger:
def **init**(self, config: LoggingConfig):
self.\_queue = Queue(maxsize=config.queue_size)
self.\_worker_thread = None
self.\_last_heartbeat = time.time()
self.\_running = True
self.\_start_worker()
self.\_register_signal_handlers()

      def log(self, action_type: str, **data):
          """记录行动（异步）"""
          if not self._is_worker_healthy():
              self._handle_unhealthy_worker()

          action_data = self._build_action_data(action_type, **data)
          try:
              self._queue.put_nowait(action_data)
          except queue.Full:
              # Phase 1: 简单丢弃策略
              logger.warning("Log queue full, dropping log")

      def _worker(self):
          """后台线程：批量写入日志"""
          try:
              while self._running:
                  batch = self._collect_batch()  # 100条或1秒超时
                  if batch:
                      self._writer.write_batch(batch)
                  self._last_heartbeat = time.time()
          except Exception as e:
              logger.error(f"Worker crashed: {e}")
              self._worker_alive = False

      def _is_worker_healthy(self) -> bool:
          """健康检查（11.2.2 高风险项）"""
          if not self._worker_thread.is_alive():
              return False
          if time.time() - self._last_heartbeat > 10:
              return False
          return True

1.3 实现 LogWriter 类

- ✅ JSON Lines 格式写入
- ✅ 按日期分割（YYYY-MM-DD.jsonl）
- ✅ 批量写入优化（减少 I/O）
- ✅ 文件句柄管理（打开/关闭/轮转）

  1.4 定义数据类型

# src/logging/types.py

from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class ActionData:
timestamp: str
action_number: int
action_type: str
session_id: str
execution_id: Optional[str]
status: str
data: Dict[str, Any]

交付物：

- ✅ 基础日志框架可运行
- ✅ 单元测试：队列操作、健康检查、信号处理
- ✅ 集成测试：完整流程（log → queue → worker → file）

---

Day 2: 核心集成 + 数据脱敏（6-8 小时）

2.1 集成到现有系统

集成点 1: SessionManager

# src/sessions/manager.py

from src.logging import get_action_logger

class SessionManager:
def **init**(self):
self.logger = get_action_logger()

      def start_session(self, project_name: str):
          session = Session(...)
          self.logger.log("session_start",
                         project_name=project_name,
                         session_id=session.session_id,
                         metadata={...})
          return session

      def end_session(self):
          self.logger.log("session_end",
                         session_id=self.current_session.session_id,
                         duration=...)

集成点 2: EnhancedAgent

# src/agents/enhanced_agent.py

def \_transition_state(self, new_state: AgentState):
old_state = self.state
self.state = new_state

      self.logger.log("agent_state_change",
                     from_state=old_state.value,
                     to_state=new_state.value,
                     reason="user_request")

集成点 3: ToolExecutor

# src/tools/executor.py

async def execute_tool(self, tool_name: str, args: dict):
tool_use_id = generate_id()

      self.logger.log("tool_call",
                     tool_name=tool_name,
                     tool_use_id=tool_use_id,
                     args=args,
                     permission_level=tool.permission_level)

      try:
          result = await tool.execute(**args)
          self.logger.log("tool_result",
                         tool_use_id=tool_use_id,
                         success=True,
                         output=result.output[:1000])  # 截断
      except Exception as e:
          self.logger.log("tool_error",
                         tool_use_id=tool_use_id,
                         error_type=type(e).__name__,
                         error_message=str(e))

集成点 4: LLM Clients

# src/clients/base.py (在所有 client 基类添加)

async def create_message(self, messages, tools=None, \*\*kwargs):
request_id = generate_id()

      self.logger.log("llm_request",
                     provider=self.provider_name,
                     model=self.model_name,
                     messages_count=len(messages),
                     request_id=request_id)

      try:
          response = await self._do_request(...)
          self.logger.log("llm_response",
                         request_id=request_id,
                         input_tokens=response.usage.input_tokens,
                         output_tokens=response.usage.output_tokens)
      except Exception as e:
          self.logger.log("llm_error",
                         request_id=request_id,
                         error_type=type(e).__name__)

2.2 数据脱敏实现

# src/logging/masking.py

class DataMasker:
def **init**(self, config: MaskingConfig):
self.enabled = config.mask_sensitive_data
self.sensitive_fields = config.custom_sensitive_fields
self.\_compile_patterns()

      def mask(self, data: dict) -> dict:
          """递归脱敏字典数据"""
          if not self.enabled:
              return data

          masked = {}
          for key, value in data.items():
              if self._is_sensitive_field(key):
                  masked[key] = "[MASKED]"
              elif isinstance(value, str):
                  masked[key] = self._mask_patterns(value)
              elif isinstance(value, dict):
                  masked[key] = self.mask(value)  # 递归
              else:
                  masked[key] = value
          return masked

      def _mask_patterns(self, text: str) -> str:
          """基于正则的模式脱敏"""
          # API密钥: sk-ant-api03-xxx...
          text = re.sub(r'sk-[a-zA-Z0-9]{48}', 'sk-***[MASKED]***', text)
          # Bearer token
          text = re.sub(r'Bearer\s+[A-Za-z0-9\-._~+/]+', 'Bearer [MASKED]', text)
          # 文件路径
          text = re.sub(r'/Users/[^/]+/', '/Users/[USER]/', text)
          return text

2.3 实现核心 action types（10 个）

- USER_INPUT
- USER_COMMAND
- AGENT_STATE_CHANGE
- LLM_REQUEST
- LLM_RESPONSE
- TOOL_CALL
- TOOL_RESULT
- TOOL_ERROR
- SESSION_START
- SESSION_END

交付物：

- ✅ 5 个集成点全部完成
- ✅ 数据脱敏正常工作
- ✅ 集成测试：完整用户场景（输入 → LLM → 工具 → 输出）

---

Day 3: 配置系统 + 基础查询工具（6-8 小时）

3.1 更新配置模板

# templates/settings.json

{
"logging": {
"enabled": true,
"log_dir": "~/.tiny-claude-code/logs",
"async_logging": true,
"queue_size": 1000,
"batch_size": 100,
"batch_timeout_sec": 1,
"mask_sensitive_data": true,
"custom_sensitive_fields": [],
"action_types": {
"user_input": true,
"user_command": true,
...
}
}
}

3.2 配置加载和验证

# src/logging/config.py

from pydantic import BaseModel, Field, validator

class LoggingConfig(BaseModel):
enabled: bool = True
log_dir: str = "~/.tiny-claude-code/logs"
async_logging: bool = True
queue_size: int = Field(default=1000, ge=100, le=10000)
batch_size: int = Field(default=100, ge=10, le=1000)

      @validator('log_dir')
      def expand_path(cls, v):
          return Path(v).expanduser()

3.3 实现 /log 命令（MVP 版本）

# src/commands/log_command.py

class LogCommand:
"""基础查询工具（11.2.5 分阶段实现）"""

      def execute(self, args: argparse.Namespace):
          # Phase 1 支持的功能
          date = args.date or datetime.now().strftime("%Y-%m-%d")
          tail = args.tail or 50
          keyword = args.keyword
          format = args.format or "table"

          # 流式读取日志文件
          results = self._query_logs(date, keyword, tail)

          # 格式化输出
          if format == "table":
              self._print_table(results)
          elif format == "json":
              print(json.dumps(results, indent=2))

支持的查询选项（MVP）：
/log # 今天最后 50 条
/log --tail 100 # 最后 100 条
/log --date 2025-11-21 # 指定日期
/log --keyword "error" # 关键词搜索
/log --format table|json # 输出格式

3.4 注册命令

# src/commands/**init**.py

BUILTIN_COMMANDS = {
"status": StatusCommand,
"todos": TodosCommand,
"log": LogCommand, # 新增
...
}

交付物：

- ✅ 配置系统完整（模板 + 加载 + 验证）
- ✅ /log 命令可用（MVP 功能）
- ✅ E2E 测试：用户完整流程测试

---

Phase 1 验收标准

功能验收：

- 启动程序，所有行动实时写入 ~/.tiny-claude-code/logs/YYYY-MM-DD.jsonl
- 按两次 Ctrl+C，检查日志文件包含退出前的所有操作
- 查看日志文件，验证 API key 已脱敏
- 运行 /log 命令，可以看到今天的日志
- 运行 /log --keyword "error"，可以筛选包含 "error" 的日志

性能验收：

- 每个 action 记录延迟 < 1ms（异步队列）
- 程序运行无明显卡顿
- 后台线程 CPU 占用 < 5%

测试覆盖：

- 单元测试覆盖率 > 80%
- 集成测试覆盖 5 个集成点
- Ctrl+C 测试通过

---

Phase 2: 增强功能 - 2 个工作日

目标

完善 action types + 高级脱敏 + 磁盘管理 + 结构化过滤

任务分解

Day 4: 完整 action types + 高级脱敏（6-8 小时）

4.1 补充剩余 action types（9 个）

- AGENT_THINKING
- LLM_ERROR
- TOOL_PERMISSION
- SESSION_PAUSE
- SESSION_RESUME
- HOOK_EXECUTE
- HOOK_ERROR
- SYSTEM_ERROR
- SYSTEM_WARNING

集成点：

- EventBus → SYSTEM_ERROR/WARNING
- HookManager → HOOK_EXECUTE/ERROR
- PermissionManager → TOOL_PERMISSION

  4.2 高级数据脱敏
  class DataMasker:
  def _mask_patterns(self, text: str) -> str: # 新增模式 # 邮箱
  text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
  '[EMAIL_MASKED]', text) # 手机号（中国）
  text = re.sub(r'1[3-9]\d{9}', '[PHONE_MASKED]', text) # 信用卡号
  text = re.sub(r'\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}',
  '[CARD_MASKED]', text)
  return text

  4.3 可配置脱敏规则

# 支持用户自定义敏感字段

config.custom_sensitive_fields = ["internal_token", "ssh_key"]

交付物：

- ✅ 19 个 action types 全部实现
- ✅ 高级脱敏规则生效
- ✅ 单元测试：各类脱敏模式

---

Day 5: 磁盘管理 + 结构化过滤（6-8 小时）

5.1 磁盘管理

# src/logging/cleaner.py

class LogCleaner:
def **init**(self, config: CleanupConfig):
self.retention_days = config.retention_days
self.max_total_size_mb = config.max_total_size_mb

      def cleanup(self):
          """自动清理策略"""
          log_files = self._scan_log_files()

          # 步骤1: 删除超过保留期的文件
          self._delete_old_files(log_files, self.retention_days)

          # 步骤2: 检查总大小，删除最旧文件直到满足限制
          total_size = self._calculate_total_size(log_files)
          if total_size > self.max_total_size_mb * 1024 * 1024:
              self._delete_until_size_limit(log_files)

      def compress_old_logs(self, days_threshold=7):
          """压缩N天前的日志"""
          for log_file in self._get_old_uncompressed_files(days_threshold):
              self._compress_file(log_file)  # gzip

5.2 启动时自动清理

# src/main.py

def main():
config = load_config()

      if config.logging.cleanup_on_startup:
          cleaner = LogCleaner(config.logging)
          cleaner.cleanup()

      # ... 启动应用

5.3 结构化过滤（Phase 2 查询功能）

# src/commands/log_command.py (扩展)

class LogQueryEngine:
def filter(self,
date: str,
action_types: List[str] = None,
status: str = None,
session_id: str = None,
tool_name: str = None,
limit: int = 1000):
"""结构化过滤"""
results = []

          with open(self._get_log_file(date), 'r') as f:
              for line in f:
                  record = json.loads(line)

                  # 多条件过滤
                  if action_types and record['action_type'] not in action_types:
                      continue
                  if status and record.get('status') != status:
                      continue
                  if session_id and record.get('session_id') != session_id:
                      continue
                  if tool_name and record.get('tool_name') != tool_name:
                      continue

                  results.append(record)
                  if len(results) >= limit:
                      break

          return results

新增查询选项：
/log --action-type tool_error # 按类型
/log --status error # 按状态
/log --session-id session-xxx # 按会话
/log --action-type tool_call --status success --tool-name bash

交付物：

- ✅ 磁盘清理机制工作
- ✅ 7 天后日志自动压缩
- ✅ 结构化过滤查询可用
- ✅ 性能测试：大文件查询性能

---

Phase 2 验收标准

功能验收：

- 所有 19 个 action types 都能正确记录
- 邮箱、手机号自动脱敏
- 启动程序，自动清理超过 30 天的日志
- 7 天前的日志自动压缩为 .gz
- /log --action-type tool_error 可以精确过滤

性能验收：

- 100MB 日志文件查询响应时间 < 2 秒
- 异步日志吞吐量 > 1000 actions/sec

---

Phase 3: 生产就绪 - 2 个工作日

目标

日志压缩 + 完整查询工具 + 程序化 API + 监控告警

任务分解

Day 6: 完整查询工具 + 程序化 API（6-8 小时）

6.1 高级查询功能

# 日期范围

/log --date-range 2025-11-15:2025-11-21

# 统计摘要

/log --format summary

# 结果限制

/log --limit 50

6.2 统计摘要实现
def generate_summary(logs: List[dict]) -> dict:
"""生成统计摘要"""
summary = {
"total_actions": len(logs),
"sessions": len(set(log['session_id'] for log in logs)),
"errors": sum(1 for log in logs if 'error' in log['action_type']),
"type_distribution": Counter(log['action_type'] for log in logs),
"status_distribution": Counter(log['status'] for log in logs),
}
return summary

6.3 程序化 API

# src/logging/query.py

class LogQueryEngine:
"""供内部使用的程序化 API"""

      def filter(self,
                 date_range: Tuple[str, str] = None,
                 action_types: List[str] = None,
                 session_id: str = None,
                 status: str = None) -> 'Query':
          self._filters.update(...)
          return self

      def limit(self, n: int) -> 'Query':
          self._limit = n
          return self

      def execute(self) -> List[Dict[str, Any]]:
          """执行查询，返回结果"""
          return self._do_query()

# 使用示例

from src.logging import LogQueryEngine

results = LogQueryEngine().filter(
date_range=("2025-11-20", "2025-11-21"),
action_types=["tool_call", "tool_error"],
status="error"
).limit(100).execute()

交付物：

- ✅ 完整查询功能（所有过滤条件）
- ✅ 统计摘要生成
- ✅ 程序化 API 可用

---

Day 7: 监控告警 + 文档 + 最终测试（6-8 小时）

7.1 监控和告警

# src/logging/monitor.py

class LoggingMonitor:
def **init**(self):
self.\_error_count = 0
self.\_last_alert_time = 0

      def on_log_write_failed(self, error: Exception):
          """日志写入失败告警"""
          self._error_count += 1

          # 降级到 stderr
          sys.stderr.write(f"[LOGGING ERROR] {error}\n")

          # 如果连续失败5次，触发告警
          if self._error_count >= 5:
              self._send_alert("Logging system degraded")

      def on_queue_full(self):
          """队列满告警"""
          current_time = time.time()
          # 避免告警风暴（每分钟最多一次）
          if current_time - self._last_alert_time > 60:
              self._send_alert("Log queue full, dropping logs")
              self._last_alert_time = current_time

      def _send_alert(self, message: str):
          # Phase 3: 简单输出到 stderr
          # Phase 4: 可以集成邮件/Slack/钉钉通知
          sys.stderr.write(f"[ALERT] {message}\n")

7.2 配置验证和默认值处理

# src/logging/config.py

class LoggingConfig(BaseModel):
@validator('queue_size')
def validate_queue_size(cls, v):
if v < 100:
logger.warning(f"queue_size {v} too small, using 100")
return 100
if v > 10000:
logger.warning(f"queue_size {v} too large, using 10000")
return 10000
return v

7.3 更新文档

- README.md - 添加日志系统说明
- 创建 docs/logging_guide.md - 详细使用指南
- 更新 CLAUDE.md - 添加日志系统到架构说明

  7.4 最终 E2E 测试

# tests/e2e/test_full_logging_workflow.py

def test_complete_user_workflow():
"""测试完整用户工作流的日志记录""" # 1. 启动会话 # 2. 用户输入 # 3. LLM 调用 # 4. 工具执行 # 5. 错误处理 # 6. 会话结束 # 7. Ctrl+C 退出 # 8. 验证日志完整性
pass

def test_disk_full_scenario():
"""测试磁盘满场景""" # 模拟磁盘满，验证降级到 stderr
pass

def test_configuration_errors():
"""测试配置错误场景""" # 验证配置验证和默认值回退
pass

交付物：

- ✅ 监控告警机制
- ✅ 配置验证健壮
- ✅ 文档更新完成
- ✅ E2E 测试全部通过

---

Phase 3 验收标准

功能验收：

- /log --format summary 显示完整统计
- 日志写入失败时有告警输出到 stderr
- 配置错误时有友好提示并使用默认值
- 文档完整，用户可以独立使用

性能验收：

- 压力测试：连续 10,000 条日志写入无丢失
- 边界测试：磁盘满、权限错误、配置错误都能优雅处理

代码质量：

- 代码审查通过
- 测试覆盖率 > 85%
- 无 critical 级别 lint 警告

---

📊 总体进度跟踪

| Phase          | 时间 | 关键交付                     | 状态       |
| -------------- | ---- | ---------------------------- | ---------- |
| Phase 1 Day 1  | 1 天 | 日志基础架构 + 健康检查      | ⏳ Pending |
| Phase 1 Day 2  | 1 天 | 核心集成 + 数据脱敏          | ⏳ Pending |
| Phase 1 Day 3  | 1 天 | 配置系统 + 基础查询          | ⏳ Pending |
| Phase 1 里程碑 | 3 天 | MVP 可用                     | ⏳ Pending |
| Phase 2 Day 4  | 1 天 | 完整 action types + 高级脱敏 | ⏳ Pending |
| Phase 2 Day 5  | 1 天 | 磁盘管理 + 结构化过滤        | ⏳ Pending |
| Phase 2 里程碑 | 2 天 | 增强功能完成                 | ⏳ Pending |
| Phase 3 Day 6  | 1 天 | 完整查询 + 程序化 API        | ⏳ Pending |
| Phase 3 Day 7  | 1 天 | 监控告警 + 文档 + 测试       | ⏳ Pending |
| Phase 3 里程碑 | 2 天 | 生产就绪                     | ⏳ Pending |

---

🎯 关键风险缓解措施（内嵌在实施中）

| 风险项            | 缓解方案                                | 实施阶段          |
| ----------------- | --------------------------------------- | ----------------- |
| 🔴 后台线程异常   | 健康检查 + 降级机制                     | Phase 1 Day 1 ✅  |
| 🟡 队列满策略     | 简单丢弃（MVP）→ 分级策略（Phase 2）    | Phase 1 → Phase 2 |
| 🟡 查询工具复杂   | 分阶段实现（tail+grep → 结构化 → 高级） | Phase 1-3 ✅      |
| 🟢 性能优化       | 暂不实施，Phase 4 可选引入 orjson       | Phase 4+          |
| 🟢 日志轮转原子性 | 暂不实施（单进程无需）                  | Phase 3+          |

---

📝 实施注意事项

1. 向后兼容

- ✅ 日志系统完全可选（通过配置禁用）
- ✅ 不修改现有 Session 系统核心逻辑
- ✅ 通过依赖注入方式集成

2. 测试策略

- TDD 模式：先写测试，再写实现（尤其是健康检查逻辑）
- 持续集成：每个 Day 结束后运行完整测试套件
- 手动测试：每个 Phase 结束后人工验收关键功能

3. 代码审查检查点

- Phase 1 Day 2 结束：代码审查（核心架构）
- Phase 2 Day 5 结束：代码审查（功能完整性）
- Phase 3 Day 7 结束：最终审查（生产就绪）

4. 性能监控

- 每天结束后运行性能测试
- 记录关键指标：日志延迟、吞吐量、内存占用
- 如果性能下降 > 20%，立即排查

---

✅ 最终交付清单

代码交付：

- src/logging/ 模块（5 个文件）
- 5 个集成点代码修改
- /log 命令实现
- 配置模板更新（templates/settings.json）

测试交付：

- 单元测试（tests/unit/test_action_logger.py 等）
- 集成测试（tests/integration/test_logging_integration.py）
- E2E 测试（tests/e2e/test_full_logging_workflow.py）
- 性能测试（tests/performance/test_logging_performance.py）

文档交付：

- README.md 更新（添加日志系统说明）
- docs/logging_guide.md（用户使用指南）
- CLAUDE.md 更新（架构说明）
- 设计文档（已有：p11-structured-action-logging.md）
