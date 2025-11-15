#!/usr/bin/env python3
"""
直接检查 tool_results 的结构
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
from src.agents.enhanced_agent import EnhancedAgent

# 拦截 add_tool_results 调用
original_add_tool_results = EnhancedAgent._execute_tools

async def patched_execute_tools(self, tool_uses, verbose=True, feedback=None):
    """拦截 _execute_tools 方法"""
    print("\n" + "="  * 80)
    print("🔍 _execute_tools 被调用")
    print("=" * 80)
    print(f"tool_uses 数量: {len(tool_uses)}")
    for i, tool_use in enumerate(tool_uses):
        print(f"\n  [{i}] 工具使用:")
        print(f"      id: {tool_use.get('id')}")
        print(f"      name: {tool_use.get('name')}")
        print(f"      input: {str(tool_use.get('input'))[:100]}")

    # 调用原始方法
    tool_results = await original_add_tool_results(self, tool_uses, verbose, feedback)

    print(f"\n💾 返回的 tool_results:")
    print(json.dumps(tool_results, indent=2, ensure_ascii=False))

    return tool_results

EnhancedAgent._execute_tools = patched_execute_tools

async def test():
    """测试"""
    print("="  * 80)
    print("开始测试 tool_results 结构")
    print("=" * 80)

    config = load_config()
    print(f"\n✅ 选定提供商: {config.get('model', {}).get('provider')}")

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
