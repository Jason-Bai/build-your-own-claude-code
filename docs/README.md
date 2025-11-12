# 文档指南

这个目录包含项目的全部文档。

## 📋 快速索引

### 🚀 快速开始
- [主项目 README](../README.md) - 项目概览和快速开始

### 📚 核心文档
- [架构设计](./architecture.md) - 系统架构和设计决策
- [API 参考](./api.md) - 接口和类的详细说明
- [贡献指南](./CONTRIBUTING.md) - 如何参与项目

### 🔄 进化规划 (Evolution)
- [进化规划总览](./evolution/EVOLUTION_PLAN.md) - 完整的改进路线图
- [完成日志](./evolution/COMPLETION_LOG.md) - 各 Phase 的进度跟踪

#### Phase 详细文档
- [Phase 1: 全局 Hooks 系统](./evolution/phase-1-hooks.md) - 事件驱动基础设施
- Phase 2: 日志系统 (待开始)
- Phase 3: 沙箱执行 (待开始)
- Phase 4: 条件路由 (待开始)
- Phase 5: Checkpoint 系统 (待开始)
- Phase 6: 多Agent编排 (待开始)

---

## 📖 文档结构

```
docs/
├── evolution/                      # 📋 进化规划文档
│   ├── EVOLUTION_PLAN.md          # 总体规划和时间表
│   ├── COMPLETION_LOG.md          # 进度追踪
│   ├── phase-1-hooks.md           # Phase 1 详细设计
│   ├── phase-2-logging.md         # Phase 2 (待创建)
│   ├── phase-3-sandbox.md         # Phase 3 (待创建)
│   ├── phase-4-routing.md         # Phase 4 (待创建)
│   ├── phase-5-checkpoint.md      # Phase 5 (待创建)
│   └── phase-6-orchestration.md   # Phase 6 (待创建)
│
├── README.md                       # 本文件
├── architecture.md                 # 架构设计文档
├── api.md                          # API 参考
└── CONTRIBUTING.md                # 贡献指南
```

---

## 🎯 按场景查找文档

### 我想...

#### ...了解项目
- 👉 [主项目 README](../README.md)

#### ...开始开发
- 👉 [贡献指南](./CONTRIBUTING.md)
- 👉 [架构设计](./architecture.md)

#### ...理解系统架构
- 👉 [架构设计](./architecture.md)
- 👉 [API 参考](./api.md)

#### ...跟踪项目进度
- 👉 [完成日志](./evolution/COMPLETION_LOG.md)
- 👉 [进化规划](./evolution/EVOLUTION_PLAN.md)

#### ...参与 Phase X 的开发
1. 查看 [进化规划](./evolution/EVOLUTION_PLAN.md) 了解各 Phase
2. 查看具体 Phase 文档（如 [Phase 1](./evolution/phase-1-hooks.md)）
3. 按照 "实现清单" 章节开发
4. 完成后更新 [完成日志](./evolution/COMPLETION_LOG.md)

---

## 📅 何时更新文档

### 每天
- 无固定更新

### 每周（周一）
- 更新 [完成日志](./evolution/COMPLETION_LOG.md)
- 记录上周进度和本周计划

### Phase 完成时
- 更新对应的 `phase-x.md` 标记为完成 ✅
- 更新 [EVOLUTION_PLAN.md](./evolution/EVOLUTION_PLAN.md) 的状态
- 更新 [完成日志](./evolution/COMPLETION_LOG.md)

### 有重大功能时
- 更新 [API 参考](./api.md)
- 更新主 [README](../README.md)

---

## 💡 文档最佳实践

### 创建新文档时
1. 使用 Markdown 格式
2. 添加目录链接到本页面
3. 在头部添加元信息（优先级、难度、预计周期等）
4. 使用清晰的标题层级（# ## ###）
5. 添加代码示例时使用语法高亮

### 更新进度时
1. 更新对应的 Phase 文档
2. 更新 [完成日志](./evolution/COMPLETION_LOG.md)
3. 清晰标记状态（✅ 完成 / 🔄 进行中 / 📋 设计 / ⏳ 待开始）

### 添加代码示例时
1. 使用完整的、可运行的示例
2. 添加必要的导入语句
3. 包含输出示例或运行结果

---

## 🔗 外部链接

- 📌 [GitHub 仓库](https://github.com/Jason-Bai/build-your-own-claude-code)
- 📧 [提交 Issue](https://github.com/Jason-Bai/build-your-own-claude-code/issues)
- 🔀 [提交 PR](https://github.com/Jason-Bai/build-your-own-claude-code/pulls)

---

## ❓ 常见问题

### Q: 如何跟踪我的工作进度？
A: 在 [完成日志](./evolution/COMPLETION_LOG.md) 中更新你的进度

### Q: Phase 之间有什么依赖关系？
A: 查看 [EVOLUTION_PLAN.md](./evolution/EVOLUTION_PLAN.md) 中的"改进阶段概览"表格

### Q: 我想开始 Phase 1 的开发，应该从哪里开始？
A:
1. 阅读 [Phase 1 详细设计](./evolution/phase-1-hooks.md)
2. 查看"实现清单"部分
3. 按步骤实现各个模块

### Q: 完成 Phase 后应该做什么？
A:
1. 更新 Phase 文档状态为 ✅ 完成
2. 在 [完成日志](./evolution/COMPLETION_LOG.md) 记录完成时间
3. 提交 git commit（消息格式参考贡献指南）
4. 推送到 GitHub

---

**最后更新**: 2025-11-12
**维护者**: 架构团队
