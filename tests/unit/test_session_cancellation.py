"""Unit tests for SessionManager cancellation support"""

import pytest
from unittest.mock import Mock
from src.sessions.manager import SessionManager
from src.utils.cancellation import CancellationToken


def test_session_manager_initial_cancellation_token():
    """Test SessionManager has a valid cancellation token initially"""
    mock_persistence = Mock()
    manager = SessionManager(mock_persistence)
    token = manager.cancellation_token

    assert isinstance(token, CancellationToken)
    assert not token.is_cancelled()


def test_session_manager_start_new_execution():
    """Test start_new_execution creates fresh cancellation token"""
    mock_persistence = Mock()
    manager = SessionManager(mock_persistence)

    # Get initial token and cancel it
    old_token = manager.cancellation_token
    old_token.cancel("Old execution")
    assert old_token.is_cancelled()

    # Start new execution
    manager.start_new_execution()
    new_token = manager.cancellation_token

    # Should be a different token that is not cancelled
    assert new_token is not old_token
    assert not new_token.is_cancelled()


def test_session_manager_cancel_all():
    """Test cancel_all cancels the current token"""
    mock_persistence = Mock()
    manager = SessionManager(mock_persistence)
    token = manager.cancellation_token

    assert not token.is_cancelled()

    manager.cancel_all("Test cancellation")

    assert token.is_cancelled()
    assert token.reason == "Test cancellation"


def test_session_manager_cancel_all_default_reason():
    """Test cancel_all uses default reason"""
    mock_persistence = Mock()
    manager = SessionManager(mock_persistence)
    token = manager.cancellation_token

    manager.cancel_all()

    assert token.is_cancelled()
    assert token.reason == "User cancelled"


def test_session_manager_cancel_all_thread_safety():
    """Test cancel_all is thread-safe"""
    import threading
    import time

    mock_persistence = Mock()
    manager = SessionManager(mock_persistence)
    results = []

    def cancel_from_thread():
        time.sleep(0.01)
        manager.cancel_all("Thread cancellation")
        results.append("cancelled")

    # Start cancellation thread
    thread = threading.Thread(target=cancel_from_thread)
    thread.start()

    # Main thread also tries to cancel
    time.sleep(0.02)
    manager.cancel_all("Main cancellation")

    thread.join()

    # Token should be cancelled (from whichever thread got there first)
    assert manager.cancellation_token.is_cancelled()
    assert "cancelled" in results


def test_session_manager_multiple_executions():
    """Test multiple execution cycles"""
    mock_persistence = Mock()
    manager = SessionManager(mock_persistence)

    # First execution
    manager.start_new_execution()
    token1 = manager.cancellation_token
    assert not token1.is_cancelled()

    manager.cancel_all("First cancel")
    assert token1.is_cancelled()

    # Second execution
    manager.start_new_execution()
    token2 = manager.cancellation_token
    assert not token2.is_cancelled()
    assert token2 is not token1

    manager.cancel_all("Second cancel")
    assert token2.is_cancelled()

    # Third execution
    manager.start_new_execution()
    token3 = manager.cancellation_token
    assert not token3.is_cancelled()
    assert token3 is not token2
    assert token3 is not token1
