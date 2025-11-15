#!/usr/bin/env python3
"""
实时测试 Kimi 工具调用功能
模拟用户输入，测试完整的工具调用流程
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.initialization.setup import initialize_agent
from src.config.loader import load_config


async def test_kimi_with_real_example():
    """测试 Kimi 提供商的真实例子"""

    print("=" * 80)
    print("开始测试 Kimi 工具调用功能")
    print("=" * 80)

    # 从 .env 加载配置
    from dotenv import load_dotenv
    load_dotenv()

    # 验证 Kimi API key
    kimi_api_key = os.getenv("OPENAI_API_KEY")
    if not kimi_api_key:
        print("❌ 错误：未设置 OPENAI_API_KEY (Kimi API key)")
        return False

    print(f"✅ 检测到 Kimi API key: {kimi_api_key[:20]}...")

    try:
        # 加载配置
        print("\n正在加载配置...")
        config = load_config()
        print(f"✅ 配置加载成功")
        print(f"   选定提供商: {config.get('model', {}).get('provider', 'unknown')}")

        # 初始化 Agent
        print("\n正在初始化 Agent...")

        class MockArgs:
            dangerously_skip_permissions = True
            auto_approve_all = False
            always_ask = False

        agent = await initialize_agent(config, MockArgs())

        print(f"✅ Agent 初始化成功")
        print(f"   客户端类型: {agent.client.__class__.__name__}")
        print(f"   客户端提供商: {agent.client.provider_name}")
        print(f"   客户端模型: {agent.client.model_name}")

        # 模拟用户输入
        user_input = "explain to me this project structure"

        print(f"\n{'=' * 80}")
        print(f"用户输入: {user_input}")
        print(f"{'=' * 80}\n")

        # 运行 Agent
        print("🤖 Agent 正在处理请求...\n")
        result = await agent.run(user_input, verbose=True)

        print(f"\n{'=' * 80}")
        print("✅ Agent 执行完成")
        print(f"{'=' * 80}")

        # 显示结果
        print(f"\n📝 最终响应:")
        print(f"-" * 80)
        final_response = result.get("final_response", "")
        if final_response:
            # 显示前 500 字符
            if len(final_response) > 500:
                print(final_response[:500] + "\n... (省略)")
            else:
                print(final_response)
        else:
            print("(无响应)")
        print(f"-" * 80)

        # 显示统计信息
        print(f"\n📊 执行统计:")
        agent_state = result.get("agent_state", {})
        print(f"  - 总轮数: {agent_state.get('current_turn', 0)}")
        print(f"  - 输入 tokens: {agent_state.get('input_tokens', 0)}")
        print(f"  - 输出 tokens: {agent_state.get('output_tokens', 0)}")
        print(f"  - 工具调用次数: {len(agent_state.get('tool_calls', []))}")

        tool_calls = agent_state.get("tool_calls", [])
        if tool_calls:
            print(f"\n🔧 工具调用详情:")
            for i, tool_call in enumerate(tool_calls, 1):
                print(f"  {i}. ID: {tool_call.get('id', '?')}")
                print(f"     名称: {tool_call.get('name', '?')}")

        # 显示反馈
        feedback = result.get("feedback", [])
        if feedback:
            print(f"\n💬 反馈信息:")
            for item in feedback:
                print(f"  - {item}")

        print(f"\n✅ 测试成功！Kimi 工具调用正常工作")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败，发生错误:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_kimi_with_real_example())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
