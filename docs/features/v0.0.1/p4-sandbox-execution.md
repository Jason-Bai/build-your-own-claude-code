# 功能：P4 - 沙箱执行（Sandbox Execution）

**日期**: 待实现
**优先级**: P0 🔴
**难度**: ⭐⭐⭐
**预计周期**: 1.5 周
**状态**: 📋 未开始

---

## 概述

实现一个**安全的代码执行沙箱环境**，用于隔离执行用户提交的代码、命令和工具，防止恶意代码对系统的危害，提供生产级的安全保障。

---

## 问题描述

### 当前状况

当前系统直接执行 Bash 命令和代码，存在以下安全风险：

```python
# ❌ 不安全的执行方式
result = os.system(user_command)  # 直接执行，无限制
exec(user_code)                   # 直接执行，无隔离
```

**安全隐患**：
- 可以访问系统全部文件
- 可以修改或删除重要数据
- 可以安装恶意软件
- 无法限制资源占用
- 无法审计执行过程

### 期望改进

需要一个**可信的执行环境**，具备：
- 文件系统隔离（只能访问指定目录）
- 网络隔离（禁止网络访问）
- 资源限制（CPU、内存、时间）
- 权限最小化（只给必要权限）
- 执行审计（记录所有操作）

---

## 设计方案

### 核心架构

```
用户请求
  ↓
权限检查
  ↓
沙箱初始化
  ├─ 创建隔离容器 (Docker/Chroot)
  ├─ 设置资源限制 (CPU/内存/时间)
  ├─ 挂载安全的文件系统
  └─ 配置网络隔离
  ↓
在沙箱内执行
  ├─ 运行用户命令/代码
  ├─ 实时监控资源
  └─ 记录执行日志
  ↓
清理沙箱
  ├─ 收集执行结果
  ├─ 清理临时文件
  └─ 释放资源
  ↓
返回结果
```

### 沙箱实现方案

#### 方案 1: Docker 容器（推荐生产）
- 完全隔离（进程、网络、文件系统）
- 资源限制完整
- 跨平台支持
- 缺点：需要 Docker 环境

#### 方案 2: Chroot 监狱（轻量级）
- 文件系统隔离
- 低开销
- 缺点：进程隔离不完全

#### 方案 3: seccomp + rlimit（系统级）
- 系统调用过滤
- 资源限制
- 缺点：依赖 Linux

### 资源限制

```python
# CPU 限制：最多使用 1 核 CPU，最多 30 秒
cpu_limit = "1"
timeout = 30

# 内存限制：最多使用 512MB
memory_limit = "512m"

# 磁盘限制：最多写入 100MB
disk_limit = "100m"
```

### 文件系统隔离

```
/sandbox/execution-{id}/
├── workdir/          # 工作目录（可读写）
├── /tmp -> tmpfs     # 临时文件
├── /home -> 只读     # 用户主目录
└── 其他系统目录 -> 只读
```

### 审计日志

```python
# 记录所有沙箱操作
{
    "execution_id": "exec-20250113-001",
    "user": "admin",
    "command": "python script.py",
    "start_time": "2025-01-13T10:30:00Z",
    "end_time": "2025-01-13T10:30:05Z",
    "duration": 5.2,
    "exit_code": 0,
    "resources": {
        "cpu_usage": 0.8,
        "memory_peak": 256,
        "disk_written": 10
    },
    "status": "success",
    "output": "...",
    "errors": ""
}
```

---

## 实现细节

### 核心组件

#### 1. SandboxManager（沙箱管理器）
```python
class SandboxManager:
    """管理沙箱的创建、执行和清理"""

    async def create_sandbox(self, execution_id: str) -> Sandbox:
        """创建沙箱"""
        pass

    async def execute_in_sandbox(
        self,
        sandbox: Sandbox,
        command: str,
        timeout: int = 30
    ) -> ExecutionResult:
        """在沙箱内执行命令"""
        pass

    async def cleanup_sandbox(self, sandbox: Sandbox):
        """清理沙箱"""
        pass
```

#### 2. ResourceMonitor（资源监控）
```python
class ResourceMonitor:
    """监控沙箱内的资源使用"""

    async def monitor(self, sandbox: Sandbox):
        """实时监控资源"""
        pass

    def check_limits(self, usage: ResourceUsage) -> bool:
        """检查是否超过限制"""
        pass

    async def enforce_limits(self, sandbox: Sandbox):
        """强制执行限制"""
        pass
```

#### 3. AuditLogger（审计日志）
```python
class AuditLogger:
    """记录沙箱执行的审计日志"""

    async def log_execution(self, record: ExecutionRecord):
        """记录执行信息"""
        pass

    async def log_file_access(self, file_path: str, operation: str):
        """记录文件访问"""
        pass

    async def log_network_attempt(self, destination: str):
        """记录网络访问尝试"""
        pass
```

### 文件修改

- `src/sandbox/manager.py` - 沙箱管理器
- `src/sandbox/monitor.py` - 资源监控
- `src/sandbox/audit.py` - 审计日志
- `src/sandbox/executor.py` - 执行器
- `src/tools/bash.py` - 集成沙箱

---

## 工作原理

### 执行流程

```
用户执行命令
  ↓
验证权限 (Permission Manager)
  ↓
审查沙箱策略 (Policy Check)
  ↓
创建沙箱环境 (SandboxManager.create)
  ├─ 启动容器
  ├─ 挂载文件系统
  └─ 设置资源限制
  ↓
启动资源监控 (ResourceMonitor)
  ├─ 监听 CPU/内存/磁盘
  └─ 检查是否超限
  ↓
执行用户命令 (execute_in_sandbox)
  ├─ 捕获输出
  ├─ 记录退出码
  └─ 审计日志
  ↓
清理沙箱 (cleanup_sandbox)
  ├─ 收集日志
  ├─ 清理临时文件
  └─ 释放资源
  ↓
返回执行结果
```

### 超时处理

```
命令执行超时 (30s)
  ↓
ResourceMonitor 检测到超时
  ↓
发送 SIGTERM（优雅终止）
  ↓
5 秒后检查进程状态
  ↓
如果仍运行 → 发送 SIGKILL（强制终止）
  ↓
收集部分输出和超时信息
```

---

## 测试验证

### 测试场景

#### 1. 安全隔离测试
```python
# 尝试访问 /etc/passwd
# 预期：权限拒绝

# 尝试修改系统文件
# 预期：失败，文件系统只读

# 尝试网络连接
# 预期：连接拒绝
```

#### 2. 资源限制测试
```python
# CPU 密集任务运行超过限制
# 预期：自动终止

# 内存占用超过限制
# 预期：OOM killer 介入

# 磁盘写入超过限制
# 预期：磁盘满错误
```

#### 3. 审计日志测试
```python
# 执行命令后
# 预期：记录详细的执行信息

# 检查日志完整性
# 预期：包含时间、用户、命令、结果、资源等
```

#### 4. 正常执行测试
```python
# 在沙箱内运行正常命令
# 预期：正确执行并返回结果

# 读写安全的文件
# 预期：正常工作
```

---

## 性能影响

### 开销分析

- **沙箱创建**: ~100-500ms（取决于实现）
- **命令执行**: 与实际执行时间相同
- **内存占用**: 每个沙箱 ~50-100MB
- **磁盘占用**: 每个沙箱 ~10-20MB

### 优化策略

- 沙箱复用（不每次创建）
- 镜像缓存
- 异步执行
- 批量清理

---

## 安全考虑

### 威胁模型

| 威胁 | 防护措施 |
|------|--------|
| 系统文件访问 | 文件系统隔离 |
| 网络攻击 | 网络隔离 |
| 资源耗尽 | 资源限制 |
| 权限提升 | 最小权限 |
| 日志篡改 | 审计日志保护 |

### 最佳实践

1. **最小权限原则** - 仅给必要的权限
2. **深度防御** - 多层保护
3. **完整审计** - 记录所有操作
4. **定期更新** - 安全补丁
5. **隔离测试** - 定期安全测试

---

## 相关资源

- **Docker 文档**: https://docs.docker.com/
- **seccomp**: https://man7.org/linux/man-pages/man2/seccomp.2.html
- **cgroups**: https://man7.org/linux/man-pages/man7/cgroups.7.html
- **安全最佳实践**: https://cheatsheetseries.owasp.org/

---

## 常见问题

### Q: 如何处理合法的网络请求？
**A**: 使用白名单机制，允许特定的网络访问。

### Q: 如何调试沙箱内的问题？
**A**: 通过审计日志和完整的输出捕获进行调试。

### Q: 性能如何？
**A**: 取决于沙箱实现，Docker 通常为 100-500ms 开销。

### Q: 可以禁用沙箱吗？
**A**: 可以，通过配置选项，但不推荐用于生产环境。

---

**实现者**: 待安排
**状态**: 📋 未开始
**相关 Phase**: Phase 1 (Hooks 系统)
