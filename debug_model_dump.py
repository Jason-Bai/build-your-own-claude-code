#!/usr/bin/env python3
"""
追踪 Message.model_dump() 是否正确保留了 tool_call_id
"""

import json
from src.agents.context_manager import Message

# 创建消息
msg = Message(
    role="user",
    content=[{
        "type": "tool_result",
        "tool_call_id": "Glob:0",
        "content": "test"
    }]
)

print("原始消息对象:")
print(f"  msg.content[0] = {msg.content[0]}")
print(f"  msg.content[0].get('tool_call_id') = {msg.content[0].get('tool_call_id')}")

print("\nmodel_dump() 输出:")
dumped = msg.model_dump()
print(json.dumps(dumped, indent=2))

print("\nmodel_dump(exclude_none=False) 输出:")
dumped2 = msg.model_dump(exclude_none=False)
print(json.dumps(dumped2, indent=2))
