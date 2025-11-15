#!/usr/bin/env python3
"""
追踪消息从 tool_results 到 OpenAI 的完整路径
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
from src.agents.context_manager import AgentContextManager

# 拦截 add_tool_results
original_add_tool_results = AgentContextManager.add_tool_results

def patched_add_tool_results(self, tool_results, provider="anthropic"):
    """拦截 add_tool_results"""
    print("\n" + "=" * 80)
    print("🔍 context_manager.add_tool_results 被调用")
    print("=" * 80)
    print(f"provider: {provider}")
    print(f"tool_results:")
    print(json.dumps(tool_results, indent=2, ensure_ascii=False))

    # 调用原始方法
    original_add_tool_results(self, tool_results, provider)

    # 检查添加后的消息
    print(f"\n📬 消息列表长度: {len(self.messages)}")
    if self.messages:
        last_msg = self.messages[-1]
        print(f"最后一条消息:")
        print(f"  role: {last_msg.role}")
        print(f"  content:")
        print(json.dumps(last_msg.content, indent=4, ensure_ascii=False))

AgentContextManager.add_tool_results = patched_add_tool_results


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
    print(f"\n👤 用户输入: {user_input}")

    result = await agent.run(user_input, verbose=False)
    print(f"\n✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(test())
