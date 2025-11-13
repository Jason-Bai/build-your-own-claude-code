# 文档指南

这个目录包含 Build Your Own Claude Code 项目的全部文档。

## 📋 快速索引

### 🚀 快速开始
- [主项目 README](../README.md) - 项目概览和快速开始
- [项目上下文 CLAUDE.md](../CLAUDE.md) - 详细的项目背景和技术栈

### 📚 核心设计文档
- [架构设计](./architecture.md) - 系统架构和技术设计

### ✨ 功能增强文档

#### 已完成 ✅
- [Phase 1&2: 输入输出增强](./phases/input-output-enhancement.md) - Prompt-Toolkit 和 Rich 集成
- [Phase 3: 事件驱动反馈](./phases/event-driven-feedback.md) - 事件总线和实时反馈
- [Phase 1: Hook 系统](./evolution/phase-1-hooks.md) - 事件驱动基础设施

### 📊 项目管理文档
- [进化规划总览](./evolution/EVOLUTION_PLAN.md) - 完整的改进路线图
- [完成日志](./evolution/COMPLETION_LOG.md) - 各 Phase 的进度跟踪
- [优化计划](./optimization_plan.md) - 性能优化方向

---

## 📖 文档结构

```
docs/
├── phases/                             # 📋 功能增强阶段文档
│   ├── input-output-enhancement.md    # Phase 1&2: Prompt-Toolkit & Rich
│   └── event-driven-feedback.md       # Phase 3: 事件驱动反馈
│
├── evolution/                          # 📊 项目演进文档
│   ├── EVOLUTION_PLAN.md              # 总体规划和时间表
│   ├── COMPLETION_LOG.md              # 进度追踪
│   └── phase-1-hooks.md               # Phase 1 Hook 系统详细设计
│
├── README.md                           # 本文件（文档导航）
├── architecture.md                     # 系统架构设计
└── optimization_plan.md                # 性能优化计划
```

---

## 🎯 按场景查找文档

### 我想...

#### ...快速了解项目
1. 👉 [README.md](../README.md) - 项目概览和特性列表
2. 👉 [CLAUDE.md](../CLAUDE.md) - 详细技术背景

#### ...了解系统架构
- 👉 [架构设计](./architecture.md) - 完整的系统设计

#### ...学习 CLI 增强
- 👉 [Phase 1&2: 输入输出增强](./phases/input-output-enhancement.md)
  - Prompt-Toolkit 智能输入
  - Rich 美化输出
  - Markdown 自动渲染

#### ...了解事件系统
- 👉 [Phase 3: 事件驱动反馈](./phases/event-driven-feedback.md)
  - 事件总线架构
  - Hook 系统集成
  - 实时反馈机制

#### ...理解 Hook 扩展
- 👉 [Phase 1: Hook 系统](./evolution/phase-1-hooks.md)
  - 事件类型定义
  - Hook 注册和执行
  - 安全验证

#### ...跟踪项目进度
- 👉 [完成日志](./evolution/COMPLETION_LOG.md) - 各 Phase 完成情况
- 👉 [进化规划](./evolution/EVOLUTION_PLAN.md) - 长期规划

#### ...参与开发
1. 阅读 [架构设计](./architecture.md)
2. 查看相关的 Phase 文档
3. 参考 [README.md](../README.md#开发工作流) 中的开发流程

---

## 📅 文档维护

### 何时更新文档

- **Phase 完成时**: 更新对应的 Phase 文档和 [完成日志](./evolution/COMPLETION_LOG.md)
- **重大功能时**: 更新主 [README.md](../README.md)
- **架构变更时**: 更新 [架构设计](./architecture.md)

### 清晰标记状态
- ✅ 完成 / 🔄 进行中 / 📋 设计 / ⏳ 待开始

---

## ✨ 文档清单

### 已有文档
- ✅ [README.md](../README.md) - 项目概览和快速开始
- ✅ [CLAUDE.md](../CLAUDE.md) - 项目技术背景和结构
- ✅ [架构设计](./architecture.md) - 系统架构详解
- ✅ [Phase 1&2: 输入输出增强](./phases/input-output-enhancement.md)
- ✅ [Phase 3: 事件驱动反馈](./phases/event-driven-feedback.md)
- ✅ [Phase 1: Hook 系统](./evolution/phase-1-hooks.md)
- ✅ [进化规划](./evolution/EVOLUTION_PLAN.md)
- ✅ [完成日志](./evolution/COMPLETION_LOG.md)
- ✅ [优化计划](./optimization_plan.md)

### 可选文档
- [API 参考](./api.md) - 接口和类的详细说明（可添加）
- [贡献指南](./CONTRIBUTING.md) - 如何参与项目（可添加）

---

## 🔗 相关文档

### 项目文档
- [主 README](../README.md) - 项目概览
- [CLAUDE.md](../CLAUDE.md) - 项目上下文

### 开发参考
- 项目根目录查看 [setup.py](../setup.py) 了解包配置
- 项目根目录查看 [requirements.txt](../requirements.txt) 了解依赖
- 项目根目录查看 [config.json](../config.json) 了解配置选项

---

## ℹ️ 文档说明

本 docs 文件夹组织如下：

1. **phases/** - 功能增强阶段的详细设计和实现指南
2. **evolution/** - 项目演进、规划和进度追踪
3. **archived/** - 历史设计文档（设计阶段的参考文档）
4. **README.md** - 本文档导航页面
5. **architecture.md** - 系统架构和设计决策
6. **optimization_plan.md** - 性能优化方向

### archived 文件夹说明

`archived/` 文件夹包含项目早期设计阶段的规划文档。这些文档已经被实现代码和最新的 Phase 文档所取代，但保留下来用于：

- 📚 查看项目的演进历史
- 🎓 学习功能设计的方法
- 🔍 理解设计决策的背景

**不需要查看** `archived/` 文件夹中的内容来开发或使用项目，请参考 `phases/` 文件夹中的最新实现文档。

---

**最后更新**: 2025-01-13
**文档语言**: 中文
**项目状态**: 生产就绪
