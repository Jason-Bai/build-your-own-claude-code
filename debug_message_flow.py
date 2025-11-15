#!/usr/bin/env python3
"""
追踪完整的消息流 - 调试 Kimi 工具调用问题
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


# 猴补丁：拦截 OpenAI 客户端的 create_message 调用
original_create_message = None

async def patched_create_message(self, system, messages, tools, max_tokens=8000, temperature=1.0, stream=False):
    """拦截并记录 create_message 调用"""
    print("\n" + "=" * 80)
    print("🔍 OpenAI 客户端收到的消息:")
    print("=" * 80)

    print(f"\n📋 系统提示: {system[:100]}...")
    print(f"\n📬 消息列表 (总计 {len(messages)} 条):")
    for i, msg in enumerate(messages):
        role = msg.get("role", "?")
        print(f"\n  {i}. role='{role}'")
        content = msg.get("content", [])
        if isinstance(content, list):
            print(f"     内容块数: {len(content)}")
            for j, block in enumerate(content):
                block_type = block.get("type", "?")
                print(f"       [{j}] type='{block_type}'", end="")
                if block_type == "tool_result":
                    print(f" tool_call_id='{block.get('tool_call_id', 'MISSING')}'")
                elif block_type == "tool_use":
                    print(f" id='{block.get('id', 'MISSING')}'")
                else:
                    print()
        elif isinstance(content, str):
            print(f"     内容: {content[:100]}...")

    print(f"\n🔧 工具定义数: {len(tools)}")
    if tools:
        for tool in tools[:2]:
            print(f"   - {tool.get('name', '?')}")
        if len(tools) > 2:
            print(f"   ... 还有 {len(tools) - 2} 个工具")

    print("\n" + "=" * 80)
    print("📤 转换为 OpenAI 格式后的消息:")
    print("=" * 80)

    # 执行原始方法
    result = await original_create_message(self, system, messages, tools, max_tokens, temperature, stream)

    # 记录 OpenAI API 收到的消息
    # （需要重新构造，因为原始方法已执行）

    return result


async def test():
    """测试 Kimi 工具调用，记录消息流"""

    print("=" * 80)
    print("开始调试 Kimi 消息流")
    print("=" * 80)

    from src.clients.openai import OpenAIClient
    global original_create_message
    original_create_message = OpenAIClient.create_message
    OpenAIClient.create_message = patched_create_message

    try:
        # 加载配置
        config = load_config()
        print(f"\n✅ 选定提供商: {config.get('model', {}).get('provider')}")

        # 初始化 Agent
        class MockArgs:
            dangerously_skip_permissions = True
            auto_approve_all = False
            always_ask = False
            verbose = False

        agent = await initialize_agent(config, MockArgs())
        print(f"✅ Agent 初始化成功，客户端: {agent.client.__class__.__name__}")

        # 运行一个简单的请求
        user_input = "list 3 python files"

        print(f"\n👤 用户输入: {user_input}")
        print(f"\n🤖 Agent 开始处理...")

        result = await agent.run(user_input, verbose=False)

        print(f"\n✅ Agent 执行完成")
        print(f"响应: {result.get('final_response', '')[:200]}...")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test())
