#!/usr/bin/env python3
"""
Test script to simulate consecutive user queries and verify UI behavior
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.loader import load_config
from src.initialization.setup import initialize_agent, _setup_event_listeners
from src.events import get_event_bus
from src.cli.ui_manager import InterfaceManager
from src.utils.output import OutputFormatter


async def test_consecutive_queries():
    """Test two consecutive queries to verify UI behavior"""

    print('\n' + '='*70)
    print('🧪 Testing Consecutive Queries - Event-Driven UI')
    print('='*70 + '\n')

    # Setup (use default config)
    try:
        config = load_config(None)  # Will use ~/.tiny-claude-code/settings.json
    except Exception as e:
        print(f"⚠️  Warning: Could not load config: {e}")
        print("Using minimal config...")
        config = {
            'model': {'provider': 'anthropic'},
            'mcp_servers': []
        }

    # Mock args
    args = type('Args', (), {
        'config': None,
        'verbose': False,
        'quiet': False,
        'model': None,
        'provider': None,
        'mcp_config': None
    })()

    print("🔧 Initializing agent...")
    agent = await initialize_agent(config, args)

    event_bus = get_event_bus()
    await _setup_event_listeners(event_bus)

    print("🎨 Initializing UI Manager...")
    ui_manager = InterfaceManager(event_bus, OutputFormatter.console, refresh_rate=0.1)

    print("✅ Setup complete!\n")

    # ==================================================================
    # Test 1: Simple greeting (should not use tools)
    # ==================================================================
    print('\n' + '='*70)
    print('[Test 1] 👤 User: "hi"')
    print('='*70)

    try:
        result1 = await agent.run('hi', verbose=False)

        if result1.get('final_response'):
            response = result1['final_response']
            print(f"\n🤖 Assistant: {response[:150]}...")
            print(f"\n📊 Stats: {result1['agent_state']['total_turns']} turns, "
                  f"{result1['agent_state']['total_tools_used']} tools used")
    except Exception as e:
        print(f"❌ Error in Test 1: {e}")
        import traceback
        traceback.print_exc()

    # Wait a bit to ensure UI cleanup
    await asyncio.sleep(0.5)

    # ==================================================================
    # Test 2: Project structure (will use Glob/Read tools)
    # ==================================================================
    print('\n\n' + '='*70)
    print('[Test 2] 👤 User: "explain to me this project structure"')
    print('='*70)

    try:
        result2 = await agent.run('explain to me this project structure', verbose=False)

        if result2.get('final_response'):
            response = result2['final_response']
            print(f"\n🤖 Assistant: {response[:300]}...")
            print(f"\n📊 Stats: {result2['agent_state']['total_turns']} turns, "
                  f"{result2['agent_state']['total_tools_used']} tools used")
    except Exception as e:
        print(f"❌ Error in Test 2: {e}")
        import traceback
        traceback.print_exc()

    # ==================================================================
    # Final Statistics
    # ==================================================================
    await asyncio.sleep(0.5)

    stats = agent.get_statistics()

    print('\n\n' + '='*70)
    print('📊 Final Test Statistics')
    print('='*70)
    print(f"  • Total conversation turns: {stats['agent_state']['total_turns']}")
    print(f"  • Total tools used: {stats['agent_state']['total_tools_used']}")
    print(f"  • Input tokens: {stats['agent_state']['total_input_tokens']}")
    print(f"  • Output tokens: {stats['agent_state']['total_output_tokens']}")

    print('\n' + '='*70)
    print('🎨 UI Manager Final State')
    print('='*70)
    print(f"  • Active spinner: {'Yes' if ui_manager.spinner else 'No'}")
    print(f"  • Active live display: {'Yes' if ui_manager.live_display else 'No'}")
    print(f"  • Pending chunks: {len(ui_manager._pending_chunks)}")
    print(f"  • Last tool used: {ui_manager.current_tool_name or 'None'}")
    print(f"  • Background task active: {ui_manager._refresh_task and not ui_manager._refresh_task.done()}")

    # Verify clean state
    print('\n' + '='*70)
    print('✅ Verification')
    print('='*70)

    checks = []
    checks.append(("No active spinner", ui_manager.spinner is None))
    checks.append(("No active display", ui_manager.live_display is None))
    checks.append(("No pending chunks", len(ui_manager._pending_chunks) == 0))
    checks.append(("Background task cleaned",
                   ui_manager._refresh_task is None or ui_manager._refresh_task.done()))

    all_passed = all(check[1] for check in checks)

    for name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")

    if all_passed:
        print("\n🎉 All verifications passed! UI is in clean state.")
    else:
        print("\n⚠️  Some verifications failed. UI may have leaks.")

    # Cleanup
    if agent.mcp_client:
        await agent.mcp_client.disconnect_all()

    print('\n' + '='*70)
    print('✅ Test completed successfully!')
    print('='*70 + '\n')


if __name__ == '__main__':
    try:
        asyncio.run(test_consecutive_queries())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
