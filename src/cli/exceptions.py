"""Custom exceptions for the CLI interface"""

class SessionPausedException(Exception):
    """Raised when the user pauses the session via the ESC key."""
    pass
