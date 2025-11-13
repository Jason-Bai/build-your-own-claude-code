# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Phase 4: 高级代理能力 (规划中)
- 多模型支持完善
- 性能优化和 Token 压缩
- 更多 MCP 服务器集成

---

## [1.0.0] - 2025-01-13

### Added

#### Phase 1: Prompt-Toolkit 输入增强 ✅
详见：[docs/features/v0.0.1-phase-1-input.md](./features/v0.0.1-phase-1-input.md)

- **智能命令自动补全**
  - CommandCompleter 自定义补全器，支持 "/" 前缀
  - 大小写不敏感匹配
  - 多行输入支持
  - 补全快捷键：Tab 触发补全

- **历史记录管理**
  - 持久化历史到 `~/.cache/tiny_claude_code/`
  - Up/Down 键浏览历史
  - Ctrl+R 搜索历史
  - 跨会话历史保留

- **键盘快捷键支持**
  - Ctrl+A/E: 行首/行尾
  - Ctrl+K/U: 删除到行尾/行首
  - Ctrl+W: 删除前一个单词
  - Alt+Enter: 多行编辑
  - 鼠标支持：选择、复制、粘贴

- **异步兼容性**
  - async_get_input() 方法支持 asyncio 事件循环
  - 完美集成主应用事件循环
  - 无阻塞用户输入

**Commits:**
- `1a81d61` - P1: Implement Prompt-Toolkit input enhancement
- `ff3f221` - Refactor: Rename src/utils/prompt_input.py to src/utils/input.py
- `0370ab7` - Fix: Add async support to PromptInputManager
- `2c8e340` - Fix: Implement smart command autocomplete

#### Phase 2: Rich 输出增强 ✅
详见：[docs/features/v0.0.1-phase-2-output.md](./features/v0.0.1-phase-2-output.md)

- **彩色样式输出**
  - 6 种预定义样式：Success (绿), Error (红), Info (青), Warning (黄), Thinking (暗紫), Debug (暗灰)
  - 一致的样式主题
  - 易于扩展的样式系统

- **Markdown 自动渲染**
  - 自动检测 Markdown 元素
  - 在 Panel 中智能渲染
  - 支持标题、列表、引用、代码块
  - 保留原始格式的备选输出

- **代码语法高亮**
  - Monokai 主题
  - 行号和缩进指南
  - 多语言支持（Python, JavaScript, SQL, Bash 等）
  - 自动语言检测

- **表格和 Panel 支持**
  - 格式化表格显示
  - 带样式的 Panel 包装
  - 可扩展的布局
  - 边框和标题自定义

**Commit:**
- `e697509` - P2: Enhance output with Rich library

#### Phase 3: 事件驱动实时反馈 ✅
详见：[docs/features/v0.0.2-phase-3-events.md](./features/v0.0.2-phase-3-events.md)

- **事件总线 (EventBus)**
  - 中央事件分发器
  - 发布-订阅消息传递
  - 异步事件处理
  - 事件优先级管理
  - 事件去重机制

- **Hook 系统**
  - 事件驱动的可扩展性
  - 工具执行前/后 Hook
  - Agent 状态变化 Hook
  - 消息发送/接收 Hook
  - 安全的 Python 代码加载
  - AST 验证和执行沙盒

- **完整的事件流**
  - 工具调用日志
  - Token 使用追踪
  - 状态变化通知
  - 异步事件处理

- **持久化配置**
  - 全局配置：`~/.tiny-claude/settings.json`
  - 项目配置：`.tiny-claude/settings.json`
  - 本地配置：`.tiny-claude/settings.local.json` (gitignored)

**Commit:**
- `1a17886` - P3: Implement Event-Driven Real-Time Feedback System

#### 项目文档和上下文
- **CLAUDE.md** - 详细的项目技术背景和结构说明
- **README.md** - 完整的项目概览和快速开始指南
- **docs/architecture.md** - 系统架构详细设计
- **docs/development_guide.md** - 开发工作流和贡献指南
- **docs/troubleshooting_guide.md** - 故障排除指南

### Fixed

#### asyncio 事件循环冲突修复 ✅
详见：[hotfixes/v2025.01.13.1-fix-asyncio-loop.md](./hotfixes/v2025.01.13.1-fix-asyncio-loop.md)

- **问题**：`asyncio.run() cannot be called from a running event loop`
- **原因**：Prompt-Toolkit 同步方法在异步上下文中创建新事件循环导致冲突
- **解决**：实现 `async_get_input()` 方法使用 `session.prompt_async()`
- **影响**：Phase 1 输入增强功能现在可以在异步上下文中正常运行
- **相关 Commit**：`0370ab7`

#### Tab 自动补全 "/" 前缀问题修复 ✅
详见：[hotfixes/v2025.01.13.2-fix-tab-autocomplete.md](./hotfixes/v2025.01.13.2-fix-tab-autocomplete.md)

- **问题**：NestedCompleter 删除 "/" 前缀，导致补全失败
- **症状**：输入 `/h<TAB>` 补全为 `help` 而不是 `/help`
- **原因**：NestedCompleter 假设补全词汇中不包含前缀字符
- **解决**：创建自定义 CommandCompleter 类保留 "/" 前缀
- **影响**：所有命令补全现在正确保留 "/" 前缀
- **相关 Commit**：`2c8e340`

### Changed

- 优化了输入响应性，减少了延迟
- 改进了输出格式，增强了可读性
- 增强了错误消息的清晰度
- 改进了代码注释和文档字符串

### Known Issues

- Google Gemini 客户端集成进行中，免费版本不支持工具调用
- OpenAI 客户端集成进行中
- 某些终端（如 IDLE）可能不支持完整的颜色和样式

---

## [0.9.0] - 2024-12-XX

### Added
- 初始项目框架
- 基础 Agent 实现
- Anthropic Claude 客户端集成
- 基础工具系统
- 对话持久化

---

## 版本说明

### 版本号方案

- **主版本号 (Major)**: 重大功能或 API 变更
- **副版本号 (Minor)**: 新增功能，向后兼容
- **修订版本号 (Patch)**: 缺陷修复

### 发布周期

- 定期更新新功能
- 及时发布重要修复
- 保持文档同步更新

---

## 历史版本

查看特定版本的详细信息：

- **Phase 1 文档**: [docs/features/v0.0.1-phase-1-input.md](./features/v0.0.1-phase-1-input.md)
- **Phase 2 文档**: [docs/features/v0.0.1-phase-2-output.md](./features/v0.0.1-phase-2-output.md)
- **Phase 3 文档**: [docs/features/v0.0.2-phase-3-events.md](./features/v0.0.2-phase-3-events.md)

---

## 修复和热补丁

### 2025-01-13
- [v2025.01.13.1](./hotfixes/v2025.01.13.1-fix-asyncio-loop.md) - asyncio 事件循环冲突修复
- [v2025.01.13.2](./hotfixes/v2025.01.13.2-fix-tab-autocomplete.md) - Tab 自动补全修复

查看更多修复：[docs/hotfixes/README.md](./hotfixes/README.md)

---

## 贡献者

感谢所有为此项目做出贡献的人！

---

**最后更新**: 2025-01-13

有问题或建议？查看 [README.md](../README.md) 或提交 Issue。
