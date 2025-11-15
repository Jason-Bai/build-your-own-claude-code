#!/usr/bin/env python
"""
Simple test to verify no import/syntax errors
"""
import sys
import asyncio

async def test_imports():
    """Test if all imports work"""
    try:
        print("Testing imports...")

        from src.cli.main import main, cli
        print("✅ src.cli.main imports OK")

        from src.commands import register_builtin_commands, command_registry
        print("✅ src.commands imports OK")

        from src.utils import OutputFormatter, get_input_manager
        print("✅ src.utils imports OK")

        from src.cli.interactive import InteractiveListSelector
        print("✅ src.cli.interactive imports OK")

        # Test command registration
        register_builtin_commands()
        all_commands = command_registry.get_all()
        print(f"✅ Commands registered: {len(all_commands)} commands")

        # Check checkpoint command exists
        checkpoint_cmd = command_registry.get("checkpoint")
        if checkpoint_cmd:
            print(f"✅ /checkpoint command: {checkpoint_cmd.name}")
            print(f"   Aliases: {checkpoint_cmd.aliases}")
        else:
            print("❌ /checkpoint command not found!")
            return False

        # Test output formatter
        print("✅ OutputFormatter imports OK")

        # Test interactive selector
        items = [("test", "Test item")]
        selector = InteractiveListSelector("Test", items)
        print("✅ InteractiveListSelector works")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await test_imports()
    if success:
        print("\n✅ All imports and basic functionality verified!")
        return 0
    else:
        print("\n❌ Some errors found")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
