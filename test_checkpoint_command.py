#!/usr/bin/env python
"""
Test the /checkpoint command end-to-end with actual checkpoint data
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

async def test_checkpoint_command():
    """Test checkpoint command with real checkpoint data"""
    try:
        print("Testing /checkpoint command end-to-end...\n")

        # Import modules
        from src.commands import register_builtin_commands, command_registry, CLIContext
        from src.checkpoint.manager import CheckpointManager
        from src.checkpoint.types import Checkpoint
        from src.persistence.manager import PersistenceManager
        from src.initialization.setup import initialize_agent
        from src.config.loader import load_config
        from src.config.args import parse_args

        print("✅ All imports successful\n")

        # Load config and initialize agent
        print("Loading configuration and initializing agent...")
        config = load_config()
        args = parse_args()
        args.verbose = False
        args.quiet = False
        agent = await initialize_agent(config, args)
        print(f"✅ Agent initialized: {agent.client.model_name}\n")

        # Register commands
        print("Registering commands...")
        register_builtin_commands()
        all_commands = command_registry.get_all()
        checkpoint_cmd = command_registry.get("checkpoint")
        print(f"✅ Checkpoint command registered: {checkpoint_cmd.name}")
        print(f"   Aliases: {checkpoint_cmd.aliases}\n")

        # Create test checkpoints
        print("Creating test checkpoints...")
        checkpoint_manager = agent.checkpoint_manager

        # Create first checkpoint
        cp1 = await checkpoint_manager.create_checkpoint(
            execution_id="exec-001",
            step_name="analyze_codebase",
            step_index=1,
            state={"files_analyzed": 5},
            context={"project": "my-app"},
            variables={"total_lines": 1000},
            status="success"
        )
        print(f"✅ Created checkpoint 1: {cp1.id}")

        # Create second checkpoint
        cp2 = await checkpoint_manager.create_checkpoint(
            execution_id="exec-001",
            step_name="generate_summary",
            step_index=2,
            state={"summary_length": 500},
            context={"project": "my-app"},
            variables={"total_lines": 1000},
            status="success"
        )
        print(f"✅ Created checkpoint 2: {cp2.id}")

        # Create checkpoint for different execution
        cp3 = await checkpoint_manager.create_checkpoint(
            execution_id="exec-002",
            step_name="analyze_requirements",
            step_index=1,
            state={"requirements": 10},
            context={"project": "other-app"},
            variables={"priority": "high"},
            status="success"
        )
        print(f"✅ Created checkpoint 3: {cp3.id}\n")

        # Test get_formatted_checkpoint_history
        print("Testing get_formatted_checkpoint_history()...")
        history_items = await checkpoint_manager.get_formatted_checkpoint_history()
        print(f"✅ Got {len(history_items)} execution groups:\n")

        for exec_id, display_text in history_items:
            print(f"   ID: {exec_id}")
            for line in display_text.split('\n'):
                print(f"      {line}")
            print()

        # Test checkpoint command execution
        print("Testing checkpoint command execution...")
        cli_context = CLIContext(agent, config={})

        # The command will try to show an interactive selector
        # For testing, we'll just verify it gets past the initial setup
        result = await checkpoint_cmd.execute("", cli_context)
        print(f"✅ Command executed successfully")
        print(f"   Result: {result}\n")

        print("=" * 60)
        print("✅ ALL CHECKPOINT COMMAND TESTS PASSED!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await test_checkpoint_command()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
