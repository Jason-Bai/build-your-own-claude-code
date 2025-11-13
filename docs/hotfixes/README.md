# Hotfixes 文档

本文件夹包含项目线上问题修复历史和说明。

按时间倒序组织，便于查找和追踪最新的修复。

---

## 📋 已修复问题总览

### 2025-01-13 (最新)

#### [v2025.01.13.5 - Google Gemini API 响应处理](./v2025.01.13/5-fix-gemini-response.md)

- **问题**：Google API 返回无效 finish_reason 导致应用崩溃
- **症状**：API 边缘情况下 response.text 不可访问或 finish_reason 值无效
- **影响范围**：Google Gemini 客户端
- **严重程度**：中（API 边缘情况）
- **状态**：✅ 已修复
- **相关 Commit**：4fecdea

#### [v2025.01.13.4 - 可选客户端导入错误](./v2025.01.13/4-fix-optional-imports.md)

- **问题**：缺少 openai 或 google-generativeai 包时无法启动
- **症状**：ImportError - 即使不使用可选客户端也会出错
- **影响范围**：应用初始化、客户端加载
- **严重程度**：中（启动失败）
- **状态**：✅ 已修复
- **相关 Commit**：bbf4956

#### [v2025.01.13.3 - 应用启动错误和 asyncio 兼容性](./v2025.01.13/3-fix-application-startup.md)

- **问题**：三个关键启动时错误
  - load_dotenv() API 变更
  - asyncio.run() 冲突
  - StatusCommand 属性引用错误
- **影响范围**：应用启动、Hook 系统、状态命令
- **严重程度**：高（应用无法启动）
- **状态**：✅ 已修复
- **相关 Commit**：0d3476f

#### [v2025.01.13.2 - Tab 自动补全 "/" 前缀问题](./v2025.01.13/2-fix-tab-autocomplete.md)

- **问题**：NestedCompleter 删除 "/" 前缀，导致命令补全失败
- **症状**：输入 `/h<TAB>` 补全为 `help` 而不是 `/help`
- **影响范围**：Phase 1 命令补全功能
- **严重程度**：中（功能故障）
- **状态**：✅ 已修复
- **相关 Commit**：2c8e340

#### [v2025.01.13.1 - asyncio 事件循环冲突](./v2025.01.13/1-fix-asyncio-loop.md)

- **问题**：`asyncio.run() cannot be called from a running event loop`
- **影响范围**：Phase 1 输入增强功能
- **严重程度**：高（致命错误）
- **状态**：✅ 已修复
- **相关 Commit**：0370ab7

---

## 🔍 按类型查找修复

### 输入相关

- [v2025.01.13/2-fix-tab-autocomplete.md](./v2025.01.13/2-fix-tab-autocomplete.md) - Tab 自动补全修复

### 异步相关

- [v2025.01.13/1-fix-asyncio-loop.md](./v2025.01.13/1-fix-asyncio-loop.md) - asyncio 事件循环修复
- [v2025.01.13/3-fix-application-startup.md](./v2025.01.13/3-fix-application-startup.md) - 启动时 asyncio 冲突修复

### 启动相关

- [v2025.01.13/3-fix-application-startup.md](./v2025.01.13/3-fix-application-startup.md) - 应用启动错误修复
- [v2025.01.13/4-fix-optional-imports.md](./v2025.01.13/4-fix-optional-imports.md) - 导入错误修复

### 客户端相关

- [v2025.01.13/4-fix-optional-imports.md](./v2025.01.13/4-fix-optional-imports.md) - 可选客户端导入
- [v2025.01.13/5-fix-gemini-response.md](./v2025.01.13/5-fix-gemini-response.md) - Google Gemini API 处理

---

## 🎯 修复文件命名规约

格式：`v{年}.{月}.{日}.{序号}-{问题名}.md`

**示例**：

- `v2025.01.13/1-fix-asyncio-loop.md` - 2025 年 1 月 13 日第 1 个修复
- `v2025.01.13/2-fix-tab-autocomplete.md` - 2025 年 1 月 13 日第 2 个修复
- `v2025.01.15/1-fix-something.md` - 2025 年 1 月 15 日的修复

---

## 📝 修复记录模板

新的修复文档应包含以下内容：

```markdown
# 修复：[问题标题]

**日期**: YYYY-MM-DD
**相关 Commit**: [commit hash]
**影响范围**: [哪些功能或组件受影响]
**严重程度**: [低/中/高]

## 问题描述

### 症状

[用户观察到的现象]

### 原因分析

[根本原因是什么]

## 解决方案

### 实现细节

[如何解决，包括代码示例]

### 文件修改

- **文件**: [路径]
- **类**: [类名]
- **新增方法**: [方法名]

## 测试验证

[如何验证修复有效]

## 影响范围

[修复带来的其他影响]

## 相关链接

- 源代码: [文件路径]
- Commit: [commit hash]
- 相关文档: [链接]
```

---

## 📊 统计数据

| 年月    | 修复数 | 最严重 | 状态      |
| ------- | ------ | ------ | --------- |
| 2025-01 | 2      | 高     | ✅ 已修复 |
| 2025-02 | 0      | -      | 待添加    |

---

## 🔗 相关文档

- **版本日志** → [../CHANGELOG.md](../CHANGELOG.md)
- **故障排除** → [../troubleshooting_guide.md](../troubleshooting_guide.md)
- **功能文档** → [../features/](../features/)
- **开发指南** → [../development_guide.md](../development_guide.md)

---

**最后更新**: 2025-01-13
