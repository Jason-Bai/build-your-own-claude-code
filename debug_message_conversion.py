#!/usr/bin/env python3
"""
调试脚本：查看 Kimi 消息转换后的结构
"""

import json
from src.clients.openai import OpenAIClient

# 模拟 Anthropic 格式的消息
anthropic_messages = [
    {
        "role": "assistant",
        "content": [
            {"type": "text", "text": "I'll help you explore the project structure."},
            {
                "type": "tool_use",
                "id": "call_123",
                "name": "Bash",
                "input": {"command": "find . -type f -name '*.py' | head -20"}
            }
        ]
    },
    {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_call_id": "call_123",
                "content": "src/main.py\nsrc/agents/__init__.py\n..."
            }
        ]
    }
]

print("=" * 80)
print("Anthropic 格式的消息:")
print("=" * 80)
print(json.dumps(anthropic_messages, indent=2, ensure_ascii=False))

# 创建 OpenAI 客户端来演示转换
client = OpenAIClient(
    api_key="sk-test",
    model="kimi-k2-thinking",
    api_base="https://api.moonshot.cn/v1"
)

print("\n" + "=" * 80)
print("OpenAI 客户端消息转换逻辑:")
print("=" * 80)

# 模拟转换过程
openai_messages = [{"role": "system", "content": "You are a helpful assistant"}]

for msg in anthropic_messages:
    role = msg["role"]
    content = msg["content"]
    print(f"\n处理消息 (role={role}):")
    print(f"  内容类型: {type(content)}")

    if isinstance(content, list):
        if role == "assistant":
            print(f"  → 这是 assistant 消息，需要处理 tool_use 块")
            text_content = ""
            tool_calls = []

            for block in content:
                print(f"    - 块类型: {block.get('type')}")
                if block.get("type") == "text":
                    text_content += block.get("text", "")
                elif block.get("type") == "tool_use":
                    import json
                    tool_calls.append({
                        "id": block.get("id"),
                        "type": "function",
                        "function": {
                            "name": block.get("name"),
                            "arguments": json.dumps(block.get("input", {}))
                        }
                    })

            assistant_msg = {"role": "assistant", "content": text_content}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls

            openai_messages.append(assistant_msg)
            print(f"  ✅ 生成 assistant 消息，包含 {len(tool_calls)} 个 tool_calls")

        elif role == "user":
            print(f"  → 这是 user 消息，需要处理 tool_result 块")
            for block in content:
                print(f"    - 块类型: {block.get('type')}")
                if block.get("type") == "text":
                    openai_messages.append({
                        "role": role,
                        "content": block.get("text", "")
                    })
                elif block.get("type") == "tool_result":
                    openai_messages.append({
                        "role": "tool",
                        "tool_call_id": block.get("tool_call_id", block.get("tool_use_id")),
                        "content": block.get("content", "")
                    })
                    print(f"      tool_call_id: {block.get('tool_call_id', block.get('tool_use_id'))}")

print("\n" + "=" * 80)
print("OpenAI 格式的消息 (转换后):")
print("=" * 80)
print(json.dumps(openai_messages, indent=2, ensure_ascii=False))

print("\n" + "=" * 80)
print("验证工具 ID 匹配:")
print("=" * 80)

# 检查 tool_call_id 是否能找到对应的 tool_calls
tool_call_ids = set()
for msg in openai_messages:
    if msg.get("role") == "assistant" and "tool_calls" in msg:
        for tc in msg["tool_calls"]:
            tool_call_ids.add(tc["id"])
            print(f"✅ 找到 tool_calls ID: {tc['id']}")

for msg in openai_messages:
    if msg.get("role") == "tool":
        tool_call_id = msg.get("tool_call_id")
        if tool_call_id in tool_call_ids:
            print(f"✅ tool_result 的 tool_call_id '{tool_call_id}' 能找到对应的 tool_calls")
        else:
            print(f"❌ tool_result 的 tool_call_id '{tool_call_id}' 无法找到对应的 tool_calls!")
            print(f"   已知的 IDs: {tool_call_ids}")
