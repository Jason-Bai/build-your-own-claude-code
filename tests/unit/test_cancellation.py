"""Unit tests for CancellationToken"""

import asyncio
import pytest
from src.utils.cancellation import CancellationToken


def test_cancellation_token_initial_state():
    """Test CancellationToken is not cancelled initially"""
    token = CancellationToken()
    assert not token.is_cancelled()
    assert token.reason == ""


def test_cancellation_token_cancel():
    """Test CancellationToken can be cancelled"""
    token = CancellationToken()
    token.cancel("Test reason")
    assert token.is_cancelled()
    assert token.reason == "Test reason"


def test_cancellation_token_cancel_default_reason():
    """Test CancellationToken uses default reason"""
    token = CancellationToken()
    token.cancel()
    assert token.is_cancelled()
    assert token.reason == "User cancelled"


def test_cancellation_token_raise_if_cancelled():
    """Test raise_if_cancelled raises CancelledError when cancelled"""
    token = CancellationToken()
    token.cancel("Test cancellation")

    with pytest.raises(asyncio.CancelledError) as exc_info:
        token.raise_if_cancelled()

    assert str(exc_info.value) == "Test cancellation"


def test_cancellation_token_raise_if_not_cancelled():
    """Test raise_if_cancelled does not raise when not cancelled"""
    token = CancellationToken()
    # Should not raise
    token.raise_if_cancelled()


@pytest.mark.asyncio
async def test_cancellation_token_async_wait():
    """Test CancellationToken async wait functionality"""
    token = CancellationToken()

    # Create a task that waits for cancellation
    async def wait_for_cancel():
        await token.wait()
        return "cancelled"

    task = asyncio.create_task(wait_for_cancel())

    # Give task time to start waiting
    await asyncio.sleep(0.01)

    # Cancel the token
    token.cancel("Test async wait")

    # Task should complete immediately
    result = await asyncio.wait_for(task, timeout=0.5)
    assert result == "cancelled"
    assert token.is_cancelled()


@pytest.mark.asyncio
async def test_cancellation_token_wait_immediate():
    """Test wait() returns immediately if already cancelled"""
    token = CancellationToken()
    token.cancel("Already cancelled")

    # wait() should return immediately
    await asyncio.wait_for(token.wait(), timeout=0.1)
    assert token.is_cancelled()


@pytest.mark.asyncio
async def test_cancellation_from_thread():
    """Test cancellation from background thread"""
    import threading

    token = CancellationToken()
    loop = asyncio.get_running_loop()

    # Create async task that waits for cancellation
    async def wait_for_cancel():
        await token.wait()
        return "cancelled"

    task = asyncio.create_task(wait_for_cancel())

    # Cancel from background thread (simulating GlobalKeyboardMonitor)
    def cancel_from_thread():
        import time
        time.sleep(0.1)
        # Use call_soon_threadsafe to schedule on the event loop
        loop.call_soon_threadsafe(token.cancel, "Thread cancellation")

    thread = threading.Thread(target=cancel_from_thread)
    thread.start()

    # Task should complete when thread cancels
    result = await asyncio.wait_for(task, timeout=1.0)
    assert result == "cancelled"
    assert token.reason == "Thread cancellation"

    thread.join()
