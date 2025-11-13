# 故障排除指南

本文档包含常见问题的诊断和解决方案。

## 目录

- [安装和配置](#安装和配置)
- [API 和网络](#api-和网络)
- [输入和输出](#输入和输出)
- [工具执行](#工具执行)
- [MCP 和 Hook](#mcp-和-hook)
- [异步和并发](#异步和并发)
- [文件和权限](#文件和权限)
- [性能问题](#性能问题)

---

## 安装和配置

### 问题：ImportError 模块未找到

**症状**:
```
ModuleNotFoundError: No module named 'anthropic'
```

**原因**: 依赖未安装或 Python 路径配置不正确

**解决方案**:
1. 确保已安装所有依赖:
   ```bash
   pip install -r requirements.txt
   ```

2. 确保在虚拟环境中运行:
   ```bash
   python -m venv venv
   source venv/bin/activate  # 在 Windows 上: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. 检查 Python 版本（需要 3.10+）:
   ```bash
   python --version
   ```

---

### 问题：配置文件加载失败

**症状**:
```
Error loading config file: config.json not found
```

**原因**: 配置文件路径不正确或文件格式错误

**解决方案**:
1. 确保 `config.json` 在项目根目录
2. 验证 JSON 格式:
   ```bash
   python -m json.tool config.json
   ```

3. 使用有效的配置模板:
   ```json
   {
     "model": {
       "provider": "anthropic",
       "ANTHROPIC_API_KEY": "your-key",
       "ANTHROPIC_MODEL": "claude-sonnet-4-5-20250929"
     },
     "ui": {
       "output_level": "normal"
     }
   }
   ```

---

## API 和网络

### 问题：没有配置 API 提供商

**症状**:
```
RuntimeError: No API provider configured
```

**原因**: 未设置 API 密钥或提供商配置不正确

**解决方案**:

选择以下任一方式配置 API 密钥（优先级从高到低）：

**方法 1：环境变量（推荐）**
```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
export ANTHROPIC_MODEL="claude-sonnet-4-5-20250929"  # 可选

python -m src.main
```

**方法 2：.env 文件**
```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env 并添加：
ANTHROPIC_API_KEY=your-key
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

**方法 3：config.json**
```json
{
  "model": {
    "provider": "anthropic",
    "ANTHROPIC_API_KEY": "your-key"
  }
}
```

**验证配置**:
```bash
python -m src.main --verbose
# 输出中应该显示 "Model loaded: claude-sonnet-4-5-20250929"
```

---

### 问题：API 连接超时

**症状**:
```
TimeoutError: Request to API timed out after 30 seconds
```

**原因**: 网络连接慢或 API 服务响应慢

**解决方案**:
1. 检查网络连接:
   ```bash
   ping api.anthropic.com
   ```

2. 查看你的 API 配额是否已用完（在 Anthropic 控制面板检查）

3. 重试请求（系统会自动重试）

4. 在 `config.json` 中增加超时时间（如果支持）:
   ```json
   {
     "timeout_seconds": 60
   }
   ```

---

### 问题：API 返回 401 Unauthorized

**症状**:
```
APIError: 401 Unauthorized - Invalid API key
```

**原因**: API 密钥错误或过期

**解决方案**:
1. 检查 API 密钥是否正确复制（注意空格）
2. 从 Anthropic 控制面板重新生成 API 密钥
3. 更新环境变量或配置文件
4. 重启应用

---

## 输入和输出

### 问题：命令自动补全不工作

**症状**:
- Tab 键无响应
- 补全显示错误的命令
- "/" 前缀被删除

**原因**: Prompt-Toolkit 配置或 CommandCompleter 问题

**解决方案**:
1. 确保输入以 "/" 开头（例如 `/he<TAB>` 而不是 `he<TAB>`）

2. 检查详细信息:
   ```bash
   python -m src.main --verbose
   # 查找 "CommandCompleter" 相关信息
   ```

3. 尝试重新启动应用

4. 查看修复记录：[hotfixes/v2025.01.13.2-fix-tab-autocomplete.md](../hotfixes/v2025.01.13.2-fix-tab-autocomplete.md)

---

### 问题：Markdown 没有被渲染

**症状**:
- 输出显示原始 Markdown 语法
- 代码块没有高亮
- 表格显示为文本

**原因**: Rich 库配置或输出级别不适合

**解决方案**:
1. 检查输出级别：
   ```bash
   # 在应用中运行
   /status  # 查看 "Output level"
   ```

2. 确保输出级别为 "normal"（不是 "quiet"）:
   ```bash
   /quiet off
   ```

3. 验证 Rich 库已正确安装:
   ```bash
   pip show rich
   ```

4. 尝试重新启动应用

---

### 问题：颜色和样式显示错误

**症状**:
- 输出全是颜色代码
- 终端显示奇怪的字符
- 样式不一致

**原因**: 终端不支持 ANSI 颜色或环境变量配置

**解决方案**:
1. 检查终端是否支持颜色（大多数现代终端都支持）

2. 在 `config.json` 中禁用颜色（如果需要）:
   ```json
   {
     "ui": {
       "no_color": true
     }
   }
   ```

3. 对于 Windows，使用 Windows Terminal 或启用 ANSI 支持

4. 对于 SSH 会话，确保使用了 `-X` 或 `-Y` 标志（如果需要）

---

## 工具执行

### 问题：工具执行权限被拒绝

**症状**:
```
PermissionError: Operation not permitted
```

**原因**: 工具被权限系统拒绝或文件/目录权限不足

**解决方案**:
1. 检查权限级别：
   ```bash
   /status  # 查看权限设置
   ```

2. 对于 NORMAL 权限的工具，确认对话中的确认提示

3. 检查文件/目录权限:
   ```bash
   # 对于文件操作工具
   ls -la /path/to/file
   chmod 644 /path/to/file  # 如果需要
   ```

4. 使用适当的标志运行应用:
   ```bash
   # 仅对测试或信任的环境
   python -m src.main --auto-approve-all
   ```

---

### 问题：工具执行超时

**症状**:
```
TimeoutError: Tool execution timed out after 30 seconds
```

**原因**: 工具执行时间过长或程序被锁定

**解决方案**:
1. 检查是否有后台进程占用资源

2. 尝试重新启动应用

3. 对于长时间运行的命令，增加超时时间（在 `config.json` 中配置，如果支持）

4. 尝试简化命令或分成多个步骤

---

### 问题：文件操作工具无法找到文件

**症状**:
```
FileNotFoundError: [Errno 2] No such file or directory
```

**原因**: 文件路径错误或文件不存在

**解决方案**:
1. 验证文件路径是否正确（使用绝对路径更可靠）

2. 使用 Glob 工具查找文件:
   ```bash
   # 在对话中询问 Agent
   # "find all .py files in src/"
   ```

3. 检查当前工作目录:
   ```bash
   # Agent 会显示工作目录
   /status
   ```

4. 确保文件权限允许读取:
   ```bash
   ls -la /path/to/file
   ```

---

### 问题：Bash 工具返回错误退出码

**症状**:
```
Command failed with exit code 1
```

**原因**: 执行的命令有问题

**解决方案**:
1. 查看完整的错误消息（使用 `--verbose` 标志）

2. 直接在终端运行命令以验证:
   ```bash
   # 复制命令并在终端中运行
   your-command-here
   ```

3. 检查命令的依赖是否已安装

4. 验证命令的权限和所有权

---

## MCP 和 Hook

### 问题：MCP 服务器无法加载

**症状**:
```
Error loading MCP servers
RuntimeError: Failed to start MCP server: filesystem
```

**原因**: MCP 服务器配置错误或依赖缺失

**解决方案**:
1. 检查 MCP 是否已安装:
   ```bash
   pip install mcp
   ```

2. 验证 `config.json` 中的 MCP 配置:
   ```json
   {
     "mcp_servers": [
       {
         "name": "filesystem",
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
         "enabled": true
       }
     ]
   }
   ```

3. 检查 Node.js 是否已安装（用于 npx）:
   ```bash
   node --version
   npm --version
   ```

4. 手动测试 MCP 服务器:
   ```bash
   npx @modelcontextprotocol/server-filesystem .
   ```

5. 使用 `--verbose` 标志查看详细错误:
   ```bash
   python -m src.main --verbose
   ```

---

### 问题：Hook 未执行

**症状**:
- Hook 在 settings.json 中配置但未执行
- 特定事件没有触发 Hook

**原因**: Hook 配置错误或事件名称不匹配

**解决方案**:
1. 验证 Hook 配置文件位置：
   - 全局：`~/.tiny-claude/settings.json`
   - 项目：`.tiny-claude/settings.json`
   - 本地：`.tiny-claude/settings.local.json`（gitignored）

2. 检查 Hook 配置的 JSON 格式:
   ```bash
   python -m json.tool ~/.tiny-claude/settings.json
   ```

3. 验证事件名称是否正确（例如 `on_tool_execute`, `on_message_received`）

4. 检查 Hook 命令是否可执行:
   ```bash
   # 如果是 shell 命令
   bash -c "your-command"

   # 如果是 Python 代码
   python -c "your-code"
   ```

5. 查看日志或使用 `--verbose` 模式调试

---

### 问题：Hook 加载异常

**症状**:
```
Error loading hooks: Invalid hook configuration
SyntaxError: invalid syntax in hook code
```

**原因**: Hook 配置或代码有语法错误

**解决方案**:
1. 检查 Hook 配置的 JSON 格式

2. 如果使用 Python 代码，验证语法:
   ```bash
   python -m py_compile your-hook-code.py
   ```

3. 使用 JSON 验证工具检查配置

4. 从简单的 Hook 开始测试:
   ```json
   {
     "hooks": [
       {
         "event": "on_tool_execute",
         "type": "command",
         "command": "echo 'Test Hook'",
         "priority": 10
       }
     ]
   }
   ```

---

## 异步和并发

### 问题：asyncio 事件循环冲突

**症状**:
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**原因**: 在已有运行中的事件循环中尝试创建新事件循环

**解决方案**:
1. 确保使用了异步方法 `async_get_input()` 而不是同步的 `get_input()`

2. 查看修复记录：[hotfixes/v2025.01.13.1-fix-asyncio-loop.md](../hotfixes/v2025.01.13.1-fix-asyncio-loop.md)

3. 如果在自己的代码中遇到此错误，检查是否已有事件循环运行:
   ```python
   import asyncio

   # 不要使用：
   # asyncio.run(your_async_function())

   # 应该使用：
   try:
       loop = asyncio.get_running_loop()
   except RuntimeError:
       loop = asyncio.new_event_loop()
       asyncio.set_event_loop(loop)

   loop.run_until_complete(your_async_function())
   ```

---

## 文件和权限

### 问题：无法创建历史文件

**症状**:
```
PermissionError: [Errno 13] Permission denied: '~/.cache/tiny_claude_code/'
```

**原因**: 缺少目录权限或父目录不存在

**解决方案**:
1. 创建缓存目录:
   ```bash
   mkdir -p ~/.cache/tiny_claude_code/
   ```

2. 检查权限:
   ```bash
   ls -ld ~/.cache/tiny_claude_code/
   chmod 755 ~/.cache/tiny_claude_code/
   ```

3. 确保有写权限:
   ```bash
   touch ~/.cache/tiny_claude_code/.tiny_claude_code_history
   chmod 644 ~/.cache/tiny_claude_code/.tiny_claude_code_history
   ```

---

### 问题：CLAUDE.md 初始化失败

**症状**:
```
Error initializing CLAUDE.md
FileExistsError: CLAUDE.md already exists
```

**原因**: CLAUDE.md 文件已存在

**解决方案**:
1. 如果想更新现有 CLAUDE.md，手动编辑或删除后重新初始化:
   ```bash
   # 删除现有文件
   rm CLAUDE.md

   # 在应用中运行
   /init
   ```

2. 如果想保留现有文件，跳过初始化

---

## 性能问题

### 问题：应用响应缓慢

**症状**:
- 输入延迟
- 输出渲染缓慢
- 高 CPU 使用率

**原因**: 上下文窗口过大、工具输出巨大或系统资源不足

**解决方案**:
1. 检查上下文窗口大小:
   ```bash
   /status  # 查看 "Context: XXXX/8000 tokens"
   ```

2. 清除旧对话:
   ```bash
   /clear  # 清除当前对话
   ```

3. 检查待办项列表:
   ```bash
   /todos
   ```

4. 关闭不需要的 MCP 服务器（在 `config.json` 中设置 `"enabled": false`）

5. 减少历史行数（在配置中调整，如果支持）

---

### 问题：高内存使用

**症状**:
- 内存使用不断增加
- 应用变得无响应
- 系统整体变慢

**原因**: 内存泄漏或大消息历史

**解决方案**:
1. 重启应用（完全清除内存）

2. 使用 `/clear` 清除对话历史

3. 保存当前会话然后重新启动:
   ```bash
   /save important-session
   /exit
   python -m src.main
   ```

4. 检查是否有无限循环的 Hook（如果自定义了 Hook）

---

## 还是有问题？

如果以上解决方案都不能解决问题：

1. 查看详细日志:
   ```bash
   python -m src.main --verbose
   ```

2. 查看相关文档：
   - [README.md](../README.md) - 项目概览
   - [architecture_guide.md](./architecture_guide.md) - 系统架构
   - [development_guide.md](./development_guide.md) - 开发指南

3. 检查 [GitHub Issues](https://github.com/your-username/build-your-own-claude-code/issues)

4. 创建新 Issue 并包含：
   - Python 版本和操作系统
   - 完整的错误信息和堆栈跟踪
   - 重现问题的步骤

---

**最后更新**: 2025-01-13
