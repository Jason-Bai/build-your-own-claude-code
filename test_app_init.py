#!/usr/bin/env python
"""
Simulate the actual application initialization
"""
import asyncio
import sys
from pathlib import Path

async def simulate_app():
    """Simulate app initialization"""
    try:
        print("Initializing application components...\n")

        # Import modules
        from src.commands import register_builtin_commands, command_registry, CLIContext
        from src.utils import OutputFormatter, get_input_manager
        from src.config.loader import load_config
        from src.initialization.setup import initialize_agent
        from src.events import get_event_bus
        from src.cli.interactive import InteractiveListSelector

        print("✅ All imports successful\n")

        # Load config
        print("Loading configuration...")
        config = load_config()
        print(f"✅ Config loaded\n")

        # Import args parser
        from src.config.args import parse_args

        # Initialize agent
        print("Initializing agent...")
        # Use actual argument parser to get proper Args object
        args = parse_args()
        args.verbose = False
        args.quiet = False

        agent = await initialize_agent(config, args)
        print(f"✅ Agent initialized: {agent.client.model_name}\n")

        # Register commands
        print("Registering commands...")
        register_builtin_commands()
        all_commands = command_registry.get_all()
        print(f"✅ {len(all_commands)} commands registered")
        cmd_names = [cmd.name for cmd in all_commands]
        print(f"   Commands: {', '.join(sorted(cmd_names))}\n")

        # Test welcome message
        print("Testing welcome message...")
        OutputFormatter.print_welcome(
            model_name=agent.client.model_name,
            provider=config.get("model", {}).get("provider", "unknown"),
            tools_count=len(agent.tool_manager.tools),
            claude_md_info=None
        )

        # Test input manager
        print("\n✅ Getting input manager...")
        input_manager = get_input_manager()
        print(f"   Input manager type: {type(input_manager).__name__}")
        print(f"   Commands in input manager: {len(input_manager.commands)}")

        # Test interactive selector
        print("\n✅ Testing interactive selector...")
        items = [
            ("current", "(current)\nDo not restore"),
            ("exec-1", "Restore exec-1\nPrevious: analyze code"),
        ]
        selector = InteractiveListSelector("Checkpoints", items)
        print(f"   Selector ready with {len(items)} items")

        # Test checkpoint command
        print("\n✅ Testing checkpoint command...")
        checkpoint_cmd = command_registry.get("checkpoint")
        if checkpoint_cmd:
            print(f"   Command: {checkpoint_cmd.name}")
            print(f"   Aliases: {checkpoint_cmd.aliases}")
            print(f"   Description: {checkpoint_cmd.description}")
        else:
            print("   ❌ Checkpoint command not found!")
            return False

        print("\n" + "="*60)
        print("✅ ALL INITIALIZATION TESTS PASSED!")
        print("="*60)
        return True

    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await simulate_app()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
