"""
Simple interactive list selector for TUI.
"""
from typing import List, Optional, Tuple


class InteractiveListSelector:
    """
    A simple interactive list selector.
    Shows items and allows user to select one using numeric input.
    """

    def __init__(self, title: str, items: List[Tuple[str, str]]):
        """
        Initialize selector.

        Args:
            title: The title to display
            items: List of tuples (return_value, display_text)
        """
        self.title = title
        self.items = items

    async def run(self) -> Optional[str]:
        """
        Run the selector and return the selected item's return value.

        Returns:
            The first element of the selected tuple, or None if cancelled.
        """
        if not self.items:
            return None

        # Display title
        print(f"\n{self.title}")
        print("-" * 70)

        # Display items with numbers
        for i, (_, display_text) in enumerate(self.items):
            # Handle multi-line display text
            lines = display_text.split('\n')
            print(f"[{i}] {lines[0]}")
            for line in lines[1:]:
                print(f"    {line}")

        print("-" * 70)

        # Get user selection
        try:
            choice = input("Enter selection (0-{}), or 'q' to cancel: ".format(len(self.items) - 1)).strip()
            if choice.lower() == 'q':
                return None

            idx = int(choice)
            if 0 <= idx < len(self.items):
                return self.items[idx][0]
            else:
                print("❌ Invalid selection. Please try again.")
                return await self.run()  # Re-run on invalid input
        except (ValueError, EOFError):
            return None
