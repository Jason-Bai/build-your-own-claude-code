# 修复：Google Gemini API 响应处理

**日期**: 2025-01-13
**相关 Commit**: 4fecdea
**影响范围**: Google Gemini 客户端
**严重程度**: 中（API 边缘情况导致崩溃）

---

## 问题描述

### 症状
在某些情况下，使用 Google Gemini 客户端时应用崩溃：
```
Exception: Invalid operation on a dead response
AttributeError: 'NoneType' object has no attribute ...
ValueError: Unknown finish_reason value
```

特别是当 Google API 返回特定的 `finish_reason` 值（如 12 或其他未定义的值）时。

### 原因分析

Google Gemini API 在某些边缘情况下会返回：
1. 无效的 finish_reason 值（不在预期的枚举中）
2. 异常的响应对象状态
3. 无法访问 `response.text` 的情况

**原始代码问题**：
```python
# ❌ 不安全的响应处理
def create_message(...):
    response = client.models.generate_content(...)

    # 这里可能失败，因为：
    # 1. response.text 在某些响应状态下不可访问
    # 2. finish_reason 可能有无法识别的值
    # 3. 没有异常处理的备选方案
    text = response.text  # ❌ 可能抛出异常
    reason = response.finish_reason  # ❌ 可能是无效值
```

---

## 解决方案

### 实现细节

添加多层防御性编程来处理 Google API 的边缘情况：

```python
# ✅ 安全的响应处理
async def create_message(...):
    try:
        # 1. 捕获 API 调用异常
        response = await client.models.generate_content_async(...)
    except Exception as e:
        return ModelResponse(
            text=f"Error from Google API: {str(e)}",
            finish_reason="error",
            ...
        )

    try:
        # 2. 尝试获取响应文本
        text = response.text
    except Exception:
        # 3. 备选方案：从候选对象获取
        try:
            text = response.candidates[0].content.parts[0].text
        except (IndexError, AttributeError):
            text = ""

    # 4. 安全地处理 finish_reason
    finish_reason = _convert_finish_reason(response.finish_reason)
```

### 关键改进

#### 1. API 调用异常处理
```python
try:
    response = await client.models.generate_content_async(
        model=self.model,
        contents=contents,
    )
except Exception as e:
    # 返回错误响应而不是崩溃
    return ModelResponse(
        text=f"Error from Google API: {str(e)}",
        finish_reason="error",
        ...
    )
```

#### 2. 响应文本的多层访问
```python
try:
    text = response.text
except Exception:
    # 备选：从内部结构访问
    try:
        text = response.candidates[0].content.parts[0].text
    except (IndexError, AttributeError):
        text = ""
```

#### 3. Finish Reason 的安全映射
```python
def _convert_finish_reason(reason) -> str:
    """安全地转换 finish_reason，处理未知值"""

    # 支持两种形式：enum 和 integer
    finish_reason_map = {
        # 枚举名称
        "STOP": "stop",
        "MAX_TOKENS": "length",
        "SAFETY": "content_filter",
        "RECITATION": "error",
        "OTHER": "other",
        "FINISH_REASON_UNSPECIFIED": "unknown",

        # 整数值（API 可能返回的）
        0: "unknown",           # FINISH_REASON_UNSPECIFIED
        1: "stop",              # STOP
        2: "length",            # MAX_TOKENS
        3: "content_filter",    # SAFETY
        4: "error",             # RECITATION
        5: "other",             # OTHER
    }

    # 处理 enum 对象
    if hasattr(reason, 'name'):
        reason = reason.name

    # 查找映射，未知值默认为 "unknown"
    return finish_reason_map.get(reason, "unknown")
```

### 文件修改

- **文件**: `src/clients/google.py`
  - 在 `create_message_async()` 添加 try-except
  - 实现响应文本的多层访问策略
  - 扩展 `_convert_finish_reason()` 支持整数值
  - 添加对缺失内容的安全处理

---

## 工作原理

### 正常情况（API 返回有效响应）
```
API 返回 → 访问 response.text ✅ → 转换 finish_reason ✅ → 返回结果
```

### 异常情况 1：response.text 不可访问
```
API 返回 → response.text 失败 → 尝试备选方案 ✅ → 返回内容
                    ❌         (candidates[0].content.parts[0].text)
```

### 异常情况 2：无效的 finish_reason
```
API 返回 (finish_reason=12) → 映射查询 → 不在映射中 → 返回 "unknown" ✅
```

### 异常情况 3：API 调用失败
```
API 错误 → catch exception → 返回错误响应 ✅ → 应用继续运行
```

---

## 测试验证

### 测试 1：正常响应处理

```python
# 模拟正常的 Google API 响应
response = create_message(
    model="gemini-pro",
    messages=[...]
)

# 预期结果
assert response.text is not None
assert response.finish_reason == "stop"
```

### 测试 2：异常 finish_reason 处理

```python
# finish_reason = 12（未定义的值）
response = create_message(...)

# 预期结果
assert response.finish_reason == "unknown"  # 而不是崩溃
assert response.text is not None
```

### 测试 3：响应文本不可访问

```python
# 模拟 response.text 失败的情况
response = create_message(...)

# 预期结果
# 应该从 candidates 结构获取文本
assert response.text is not None
assert len(response.text) > 0
```

### 测试 4：API 错误处理

```python
# 模拟 API 调用失败
response = create_message(...)

# 预期结果
assert response.text.startswith("Error from Google API")
assert response.finish_reason == "error"
assert response.usage is not None  # 即使失败也返回响应对象
```

### 预期结果

- ✅ 应用不会因为 Google API 边缘情况而崩溃
- ✅ 用户会得到有意义的错误消息
- ✅ 应用继续运行，可以尝试其他操作
- ✅ 所有响应都被适当处理

---

## 影响范围

### Google Gemini 客户端
- ✅ 更健壮的错误处理
- ✅ 支持更多 API 响应形式
- ✅ 优雅降级而不是崩溃

### API 兼容性
- ✅ 处理整数格式的 finish_reason
- ✅ 处理字符串格式的 finish_reason
- ✅ 处理缺失或格式错误的响应

### 用户体验
- ✅ 清晰的错误消息
- ✅ 应用不会意外崩溃
- ✅ 可以继续使用其他功能

### 向后兼容性
- ✅ 现有的有效响应处理不变
- ✅ API 接口完全相同
- ✅ 配置文件无需更改

---

## 防守层级

这个修复采用了多层防御策略：

1. **第一层**：API 调用异常处理
   - 捕获所有 API 调用异常
   - 返回有意义的错误响应

2. **第二层**：响应文本访问
   - 首选：直接访问 `response.text`
   - 备选 1：从 `candidates` 结构获取
   - 备选 2：返回空字符串（防止 None）

3. **第三层**：Finish Reason 转换
   - 支持多种输入格式（enum、string、int）
   - 未知值映射到 "unknown"
   - 不会抛出异常

4. **第四层**：响应完整性
   - 确保返回完整的 ModelResponse 对象
   - 包含所有必需的字段
   - 即使出错也有合理的默认值

---

## 相关技术资源

- **Google Generative AI 文档**: https://ai.google.dev/
- **Google Gemini API**: https://cloud.google.com/docs/generative-ai
- **错误处理最佳实践**: https://docs.python.org/3/tutorial/errors.html

---

## 结论

通过添加多层异常处理和防御性编程，我们成功地：
1. 消除了 Google API 边缘情况导致的崩溃
2. 提高了客户端的健壮性
3. 改善了用户体验
4. 保持了向后兼容性

这个修复遵循了防守层级的设计原则，即使在 API 返回非预期响应的情况下，应用也能优雅地继续运行。

---

**修复者**: Build Your Own Claude Code 项目维护者
**修复日期**: 2025-01-13
**相关 Commit**: `4fecdea Fix Google Gemini API response handling for invalid finish_reason`
