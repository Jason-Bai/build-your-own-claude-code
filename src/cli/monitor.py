"""Global keyboard monitor for ESC cancellation"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GlobalKeyboardMonitor:
    """Monitors global keyboard events for ESC cancellation

    This monitor listens for ESC key presses globally (even when the terminal
    is not focused) and triggers cancellation via SessionManager.

    The monitor respects two conditions before triggering cancellation:
    1. The user is not currently typing in the input prompt
    2. The terminal window is focused (on supported platforms)

    Usage:
        monitor = GlobalKeyboardMonitor(session_manager, input_manager)
        monitor.start()
        # ... application runs ...
        monitor.stop()
    """

    def __init__(self, session_manager, input_manager, require_window_focus: bool = False):
        """Initialize the monitor

        Args:
            session_manager: SessionManager instance to call cancel_all()
            input_manager: PromptInputManager instance to check is_waiting_input
            require_window_focus: If True, only trigger ESC when terminal is focused.
                                  If False, trigger ESC regardless of focus (useful for debugging)
        """
        self.session_manager = session_manager
        self.input_manager = input_manager
        self._listener: Optional[object] = None
        self._enabled = True
        self._require_window_focus = require_window_focus

        logger.info(f"GlobalKeyboardMonitor initialized (require_window_focus={require_window_focus})")

    def start(self):
        """Start the global keyboard listener

        Raises:
            PermissionError: On macOS if Accessibility permissions not granted
        """
        try:
            from pynput import keyboard

            self._listener = keyboard.Listener(on_press=self._on_press)
            self._listener.start()
            logger.info("GlobalKeyboardMonitor started")
        except PermissionError as e:
            logger.error(
                "Permission denied: macOS requires Accessibility permissions. "
                "Go to System Settings → Privacy & Security → Accessibility "
                "and enable access for your terminal app."
            )
            raise
        except ImportError:
            logger.warning("pynput not available, global ESC monitoring disabled")
            self._enabled = False
        except Exception as e:
            logger.error(f"Failed to start keyboard monitor: {e}")
            self._enabled = False

    def stop(self):
        """Stop the global keyboard listener"""
        if self._listener:
            try:
                self._listener.stop()
                logger.info("GlobalKeyboardMonitor stopped")
            except Exception as e:
                logger.error(f"Error stopping keyboard monitor: {e}")

    def _on_press(self, key):
        """Handle key press events

        Args:
            key: The key that was pressed
        """
        if not self._enabled:
            return

        try:
            from pynput import keyboard

            if key == keyboard.Key.esc:
                logger.debug("ESC key pressed, checking conditions...")

                # 1. Check if user is in input prompt
                if self.input_manager.is_waiting_input:
                    logger.debug("ESC blocked: user is in input prompt")
                    # Let prompt_toolkit handle it (clear input)
                    return

                # 2. Check if window is focused (optional)
                if self._require_window_focus:
                    if not self._is_window_focused():
                        logger.debug("ESC blocked: terminal not focused (and require_window_focus=True)")
                        # Terminal not focused, ignore ESC
                        return
                    logger.debug("ESC allowed: terminal is focused")
                else:
                    logger.debug("ESC allowed: window focus check disabled")

                # 3. Trigger cancellation
                logger.info("✅ ESC pressed, triggering cancellation")
                self.session_manager.cancel_all("User pressed ESC")
        except Exception as e:
            logger.error(f"Error in keyboard event handler: {e}")

    def _is_window_focused(self) -> bool:
        """Check if terminal window is focused

        Platform-specific implementation:
        - macOS: Use AppKit to check frontmost app
        - Linux: Use xdotool or wmctrl (not implemented yet)
        - Windows: Use win32gui (not implemented yet)

        Returns:
            True if terminal is focused, or True by default if check fails
        """
        try:
            # macOS implementation
            from AppKit import NSWorkspace

            active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            app_name = active_app.localizedName()

            # Check for common terminal names
            terminal_names = [
                'Terminal',  # macOS Terminal
                'iTerm',     # iTerm2
                'iTerm2',    # iTerm2 (full name)
                'Code',      # VS Code
                'Hyper',     # Hyper terminal
                'Alacritty', # Alacritty
                'kitty',     # kitty terminal
                'WezTerm',   # WezTerm
            ]

            is_focused = any(term in app_name for term in terminal_names)
            logger.debug(f"Active app: {app_name}, is_focused: {is_focused}")
            return is_focused

        except ImportError:
            # AppKit not available (not macOS or PyObjC not installed)
            # Fallback to True (always active) to maintain functionality
            logger.debug("AppKit not available, assuming window is focused")
            return True
        except Exception as e:
            # Any error in focus check, fallback to True
            logger.debug(f"Focus check failed: {e}, assuming window is focused")
            return True
