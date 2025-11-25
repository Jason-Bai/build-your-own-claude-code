"""Cancellation token for cooperative task cancellation"""

import asyncio


class CancellationToken:
    """Async-native cancellation token

    Provides a cooperative cancellation mechanism for long-running operations.
    Uses asyncio.Event for immediate notification when cancellation is requested.

    Usage:
        token = CancellationToken()

        # In long-running operation:
        while doing_work():
            token.raise_if_cancelled()  # Raises CancelledError if cancelled
            # ... do work ...

        # Or use async wait:
        task = asyncio.create_task(long_operation())
        cancel_task = asyncio.create_task(token.wait())
        done, pending = await asyncio.wait([task, cancel_task], return_when=asyncio.FIRST_COMPLETED)

        # To cancel (can be called from sync or async context):
        token.cancel("User requested cancellation")
    """

    def __init__(self):
        """Initialize a new cancellation token"""
        self._cancelled = asyncio.Event()
        self._reason = ""

    def cancel(self, reason: str = "User cancelled"):
        """Cancel the operation (thread-safe when called via loop.call_soon_threadsafe)

        Args:
            reason: Human-readable reason for cancellation
        """
        self._reason = reason
        self._cancelled.set()

    def is_cancelled(self) -> bool:
        """Check if cancellation was requested (sync check)

        Returns:
            True if cancel() was called, False otherwise
        """
        return self._cancelled.is_set()

    async def wait(self):
        """Wait asynchronously until cancellation is requested

        This method blocks until cancel() is called, allowing immediate
        response to cancellation requests without polling.

        Example:
            await token.wait()
            print("Cancellation requested!")
        """
        await self._cancelled.wait()

    def raise_if_cancelled(self):
        """Raise CancelledError if cancellation was requested

        Raises:
            asyncio.CancelledError: If cancel() was called
        """
        if self.is_cancelled():
            raise asyncio.CancelledError(self._reason)

    @property
    def reason(self) -> str:
        """Get the cancellation reason

        Returns:
            The reason string passed to cancel(), or empty string if not cancelled
        """
        return self._reason
