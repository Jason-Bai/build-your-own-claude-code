#!/usr/bin/env python3
"""
详细追踪第二轮 LLM 调用时的消息状态
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from src.initialization.setup import initialize_agent
from src.config.loader import load_config
from src.clients.openai import OpenAIClient

call_count = 0

original_create_message = OpenAIClient.create_message

async def patched_create_message(self, system, messages, tools, max_tokens=8000, temperature=1.0, stream=False):
    """拦截并详细记录第二轮调用"""
    global call_count
    call_count += 1

    print("\n" + "=" * 80)
    print(f"🔍 OpenAI.create_message 调用 #{call_count}")
    print("=" * 80)

    print(f"\n📬 接收到的消息 (总计 {len(messages)} 条):")
    for i, msg in enumerate(messages):
        print(f"\n  [{i}] role={msg.get('role')}")
        content = msg.get("content", [])
        if isinstance(content, list):
            print(f"      content块数={len(content)}")
            for j, block in enumerate(content):
                print(f"        [{j}] type={block.get('type')}", end="")
                if block.get("type") == "tool_use":
                    print(f" id='{block.get('id')}' name='{block.get('name')}'")
                elif block.get("type") == "tool_result":
                    tcid = block.get("tool_call_id") or block.get("tool_use_id")
                    print(f" tool_call_id='{tcid}'")
                else:
                    print()
        elif isinstance(content, str):
            print(f"      content='{content[:80]}...'")

    if call_count == 2:
        print("\n⚠️  这是第二轮调用！详细检查 assistant 消息中的 tool_use:")
        for i, msg in enumerate(messages):
            if msg.get("role") == "assistant" and isinstance(msg.get("content"), list):
                for block in msg.get("content", []):
                    if block.get("type") == "tool_use":
                        print(f"\n🔍 找到 tool_use 块:")
                        print(f"   完整内容: {json.dumps(block, indent=4, ensure_ascii=False)}")

    # 调用原始
    return await original_create_message(self, system, messages, tools, max_tokens, temperature, stream)

OpenAIClient.create_message = patched_create_message


async def test():
    config = load_config()
    print(f"✅ 选定提供商: {config.get('model', {}).get('provider')}")

    class MockArgs:
        dangerously_skip_permissions = True
        auto_approve_all = False
        always_ask = False
        verbose = False

    agent = await initialize_agent(config, MockArgs())
    print(f"✅ Agent 初始化成功")

    user_input = "list 3 python files"
    print(f"\n👤 用户输入: {user_input}\n")

    try:
        result = await agent.run(user_input, verbose=False)
        print(f"\n✅ 测试完成")
    except Exception as e:
        print(f"\n❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(test())
