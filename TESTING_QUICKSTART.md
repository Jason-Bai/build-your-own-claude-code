# Testing Quick Start Guide

## 🚀 一分钟快速开始

### 第1步：安装测试依赖

```bash
pip install pytest pytest-asyncio pytest-cov pytest-timeout
```

### 第2步：验证安装

```bash
pytest --version
```

### 第3步：运行示例测试

```bash
pytest tests/unit/test_agent_state_example.py -v
```

应该看到输出：
```
tests/unit/test_agent_state_example.py::TestAgentState::test_agent_state_initialization PASSED
...
12 passed in 0.12s
```

---

## 📊 查看覆盖率报告

运行带覆盖率的测试：

```bash
pytest --cov=src --cov-report=html tests/
```

然后在浏览器打开覆盖率报告：

```bash
# macOS
open htmlcov/index.html

# Linux
firefox htmlcov/index.html

# Windows
start htmlcov/index.html
```

---

## 📝 写你的第一个测试

### 步骤 1：在 `tests/unit/` 中创建文件

比如：`test_my_module.py`

### 步骤 2：使用 conftest.py 的 fixtures

```python
import pytest

@pytest.mark.unit
class TestMyModule:
    """My module tests"""

    def test_with_fixtures(self, mock_agent_state, sample_messages):
        """使用 fixtures 的测试"""
        assert mock_agent_state.model == "claude-sonnet-4.5"
        assert len(sample_messages) == 3

    @pytest.mark.asyncio
    async def test_async_function(self, mock_llm_client):
        """异步测试"""
        result = await mock_llm_client.create_message([], [])
        assert result == "Mock response from LLM"
```

### 步骤 3：运行你的测试

```bash
pytest tests/unit/test_my_module.py -v
```

---

## 🎯 常用命令

| 命令 | 说明 |
|------|------|
| `pytest tests/` | 运行所有测试 |
| `pytest tests/unit/` | 只运行单元测试 |
| `pytest tests/integration/` | 只运行集成测试 |
| `pytest -v tests/` | 详细输出 |
| `pytest -x tests/` | 第一个失败时停止 |
| `pytest --cov=src tests/` | 显示覆盖率 |
| `pytest -m asyncio tests/` | 只运行异步测试 |
| `pytest -k "test_agent" tests/` | 运行名字匹配的测试 |

---

## 🔧 可用的 Fixtures（30+）

### 最常用的：

```python
# Mock 对象
mock_agent_state       # Agent 状态
mock_context_manager   # 上下文管理器
mock_tool_manager      # 工具管理器
mock_llm_client        # LLM 客户端

# 示例数据
sample_messages        # 对话消息
sample_agent_config    # Agent 配置
sample_tools           # 工具集合

# 文件操作
temp_test_dir          # 临时目录
sample_python_file     # Python 文件示例
```

### 完整列表，见：`tests/conftest.py`

---

## ✅ 测试模式示例

### 单元测试

```python
@pytest.mark.unit
def test_simple_function():
    """简单的单元测试"""
    assert 1 + 1 == 2
```

### 使用 Mock

```python
@pytest.mark.unit
def test_with_mock(mock_agent_state):
    """使用 mock fixture"""
    assert mock_agent_state.status == "IDLE"
```

### 异步测试

```python
@pytest.mark.asyncio
async def test_async_code(mock_llm_client):
    """异步函数测试"""
    result = await mock_llm_client.create_message([], [])
    assert result is not None
```

### 集成测试

```python
@pytest.mark.integration
def test_workflow(mock_agent_state, mock_tool_manager):
    """集成测试"""
    # 组合多个组件测试
    assert True
```

### 使用临时文件

```python
def test_file_operations(temp_test_dir):
    """文件操作测试"""
    test_file = temp_test_dir / "test.txt"
    test_file.write_text("content")
    assert test_file.read_text() == "content"
```

---

## 🐛 调试测试

### 显示打印输出

```bash
pytest -s tests/test_my.py
```

### 详细的失败信息

```bash
pytest -vv tests/test_my.py
```

### 进入 debugger

```python
def test_debug():
    x = 10
    import pdb; pdb.set_trace()  # 这里暂停
    assert x == 10
```

### 查看跳过的测试

```bash
pytest -v -rs tests/
```

---

## 📈 下一步

1. **Week 1 (本周)**
   - ✅ 安装依赖
   - ✅ 运行示例测试
   - ⬜ 写 Agent State 测试 (~40 个)

2. **Week 2**
   - ⬜ LLM Clients 测试 (~30 个)
   - ⬜ Tool System 测试 (~45 个)

3. **Week 3**
   - ⬜ Events 测试 (~15 个)
   - ⬜ Commands 测试 (~25 个)

4. **Week 4**
   - ⬜ 整合所有测试
   - ⬜ 生成覆盖率报告
   - ⬜ 设置 CI/CD

---

## 📚 更多信息

- **详细测试计划**: [docs/testing_strategy.md](../docs/testing_strategy.md)
- **概览总结**: [docs/testing_plan_summary.md](../docs/testing_plan_summary.md)
- **Pytest 官方文档**: https://docs.pytest.org/
- **Pytest-asyncio**: https://github.com/pytest-dev/pytest-asyncio

---

## ❓ 常见问题

**Q: 如何跳过某个测试？**
```python
@pytest.mark.skip(reason="还没实现")
def test_future_feature():
    pass
```

**Q: 如何标记测试为预期失败？**
```python
@pytest.mark.xfail
def test_known_bug():
    pass
```

**Q: 如何只运行未来要做的测试？**
```bash
pytest -m xfail tests/
```

**Q: 如何在 CI/CD 中运行测试？**
见 [docs/testing_strategy.md](../docs/testing_strategy.md) 的 GitHub Actions 部分

---

💡 **提示**: 每周完成 30-40 个测试，4 周完成 140+ 测试，达到 80%+ 覆盖率！
