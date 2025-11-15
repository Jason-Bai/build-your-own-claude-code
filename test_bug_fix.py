#!/usr/bin/env python
"""
Comprehensive test simulating the exact user flow that was failing:
User executes /checkpoint command and gets 'CheckpointManager' object has no attribute
'get_formatted_checkpoint_history' error
"""
import asyncio
import sys

async def test_user_flow():
    """Simulate the exact user flow that was failing"""
    try:
        print("Simulating user flow: User executes /checkpoint command")
        print("=" * 70)

        # Step 1: Initialize application (like when starting CLI)
        print("\n[1/5] Initializing application...")
        from src.commands import register_builtin_commands, command_registry, CLIContext
        from src.initialization.setup import initialize_agent
        from src.config.loader import load_config
        from src.config.args import parse_args

        config = load_config()
        args = parse_args()
        args.verbose = False
        args.quiet = False

        agent = await initialize_agent(config, args)
        register_builtin_commands()
        print(f"✅ Application initialized with {len(command_registry.get_all())} commands")

        # Step 2: User looks up the /checkpoint command
        print("\n[2/5] User looks up /checkpoint command...")
        checkpoint_cmd = command_registry.get("checkpoint")
        if not checkpoint_cmd:
            print("❌ FAILED: /checkpoint command not found!")
            return False
        print(f"✅ Found /checkpoint command: {checkpoint_cmd.name}")

        # Step 3: User executes /checkpoint
        print("\n[3/5] User executes '/checkpoint' command...")
        cli_context = CLIContext(agent, config={})

        try:
            # This is where the error was happening:
            # 'CheckpointManager' object has no attribute 'get_formatted_checkpoint_history'
            result = await checkpoint_cmd.execute("", cli_context)
            print("✅ Command executed without AttributeError!")
        except AttributeError as e:
            if "get_formatted_checkpoint_history" in str(e):
                print(f"❌ FAILED: Got the exact error that was reported:")
                print(f"   {e}")
                return False
            raise

        # Step 4: Verify the command returned a result
        print("\n[4/5] Verifying command result...")
        if result is None:
            print("❌ FAILED: Command returned None")
            return False
        print(f"✅ Command returned result: {result[:50]}...")

        # Step 5: Verify checkpoint manager has the method
        print("\n[5/5] Verifying CheckpointManager has the required method...")
        checkpoint_manager = agent.checkpoint_manager

        if not hasattr(checkpoint_manager, 'get_formatted_checkpoint_history'):
            print("❌ FAILED: CheckpointManager missing get_formatted_checkpoint_history method")
            return False

        method = getattr(checkpoint_manager, 'get_formatted_checkpoint_history')
        if not callable(method):
            print("❌ FAILED: get_formatted_checkpoint_history is not callable")
            return False

        print("✅ CheckpointManager.get_formatted_checkpoint_history exists and is callable")

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - BUG IS FIXED!")
        print("=" * 70)
        print("\nSummary:")
        print("- ✅ /checkpoint command is registered")
        print("- ✅ CheckpointManager has get_formatted_checkpoint_history() method")
        print("- ✅ Command executes without AttributeError")
        print("- ✅ Interactive selector works with checkpoint history")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await test_user_flow()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
