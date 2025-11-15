from typing import Optional
from .base import Command, CLIContext
from ..cli.interactive import InteractiveListSelector


class CheckpointCommand(Command):
    """Interactively restore the agent and workspace to a previous checkpoint."""

    @property
    def name(self) -> str:
        return "checkpoint"

    @property
    def description(self) -> str:
        return "Interactively restore the agent and workspace to a previous checkpoint."

    @property
    def aliases(self):
        return ["rewind", "restore"]

    async def execute(self, args: str, context: CLIContext) -> Optional[str]:
        """
        Fetches checkpoint history and uses an interactive selector to let the user
        choose a checkpoint to resume from.
        """
        checkpoint_manager = context.agent.checkpoint_manager
        
        # Fetch and format checkpoints
        history_items = await checkpoint_manager.get_formatted_checkpoint_history()

        if not history_items:
            return "No checkpoints found."

        # Add a special "(current)" item that does nothing
        current_display = "(current)\n  Do not restore, continue with the current session."
        history_items.insert(0, ("__current__", current_display))

        selector = InteractiveListSelector(
            title="Checkpoints",
            items=history_items
        )

        selected_execution_id = await selector.run()

        if selected_execution_id and selected_execution_id != "__current__":
            # In a full implementation, we would find the latest checkpoint for this execution ID
            # and then call the recovery manager.
            # For now, we will just confirm the selection.
            # last_checkpoint = await checkpoint_manager.get_last_successful_checkpoint(selected_execution_id)
            # if last_checkpoint:
            #     await context.agent.recovery.resume_from_checkpoint(last_checkpoint.id)
            #     return f"Restored state from checkpoint for execution {selected_execution_id}."
            # else:
            #     return f"Error: No successful checkpoint found for execution {selected_execution_id}."
            return f"Selected execution to restore: {selected_execution_id}. (Resume logic not yet fully implemented)."
        
        return "Exited checkpoint selection."
