"""Permission diagnostic commands"""
import sys
import platform
from .base import Command, CLIContext
from ..utils.output import OutputFormatter


class CheckPermissionsCommand(Command):
    """Check and diagnose permission status for features"""

    @property
    def name(self) -> str:
        return "check-permissions"

    @property
    def description(self) -> str:
        return "Check permission status for ESC cancellation and other features"

    async def execute(self, args: str, context: CLIContext) -> str:
        """Execute permission check"""
        output = []
        output.append("\n🔍 Permission Diagnostic Report\n")
        output.append("=" * 70)

        # 1. Platform info
        output.append(f"\n📊 System Information:")
        output.append(f"   Platform: {platform.system()} {platform.release()}")
        output.append(f"   Python: {sys.version.split()[0]}")

        # 2. Check pynput availability
        output.append(f"\n📦 Dependencies:")
        try:
            import pynput
            version_str = getattr(pynput, '__version__', 'unknown')
            output.append(f"   ✅ pynput: {version_str} (installed)")
        except ImportError:
            output.append(f"   ❌ pynput: Not installed")
            output.append(f"      Fix: pip install pynput")
            return "\n".join(output)

        # 3. Check keyboard monitoring permissions
        output.append(f"\n⌨️  Keyboard Monitoring:")

        if platform.system() == "Darwin":  # macOS
            try:
                from pynput import keyboard

                # Try to create and start a listener
                test_listener = keyboard.Listener(on_press=lambda k: None)
                test_listener.start()
                test_listener.stop()

                output.append(f"   ✅ Accessibility permissions: GRANTED")
                output.append(f"   ✅ ESC cancellation: AVAILABLE")

            except PermissionError:
                output.append(f"   ❌ Accessibility permissions: DENIED")
                output.append(f"   ❌ ESC cancellation: UNAVAILABLE")
                output.append(f"\n   📋 How to fix:")
                output.append(f"   1. Open System Settings (System Preferences)")
                output.append(f"   2. Go to: Privacy & Security → Accessibility")
                output.append(f"   3. Click lock icon and authenticate")
                output.append(f"   4. Add your terminal app:")

                # Detect current terminal
                terminal_hints = []
                if "TERM_PROGRAM" in sys.platform:
                    terminal_hints.append(f"      - {sys.platform['TERM_PROGRAM']}")
                terminal_hints.extend([
                    "      - Terminal.app",
                    "      - iTerm2",
                    "      - VS Code",
                    "      - Your current terminal emulator"
                ])
                output.extend(terminal_hints)
                output.append(f"   5. Restart this CLI")

            except Exception as e:
                output.append(f"   ⚠️  Unexpected error: {e}")

        elif platform.system() == "Linux":
            output.append(f"   ℹ️  Linux: No special permissions typically needed")
            output.append(f"   ✅ ESC cancellation: Should work")
            output.append(f"\n   Note: If ESC doesn't work, check /dev/input permissions")

        elif platform.system() == "Windows":
            output.append(f"   ℹ️  Windows: No special permissions needed")
            output.append(f"   ✅ ESC cancellation: Should work")

        else:
            output.append(f"   ⚠️  Unknown platform: {platform.system()}")

        # 4. Window focus detection (macOS only)
        if platform.system() == "Darwin":
            output.append(f"\n🪟 Window Focus Detection:")
            try:
                from AppKit import NSWorkspace

                active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
                app_name = active_app.localizedName()

                output.append(f"   Current active app: {app_name}")

                terminal_names = ['Terminal', 'iTerm', 'iTerm2', 'Code', 'Hyper',
                                  'Alacritty', 'kitty', 'WezTerm']
                is_terminal = any(term in app_name for term in terminal_names)

                if is_terminal:
                    output.append(f"   ✅ Terminal is focused (ESC will work)")
                else:
                    output.append(f"   ⚠️  Terminal not focused (ESC may be ignored)")
                    output.append(f"      Note: require_window_focus is disabled by default")

            except ImportError:
                output.append(f"   ⚠️  AppKit not available (PyObjC not installed)")
            except Exception as e:
                output.append(f"   ⚠️  Error: {e}")

        # 5. Summary and recommendations
        output.append(f"\n💡 Recommendations:")

        # Check if we detected any issues
        has_issues = "❌" in "\n".join(output)

        if not has_issues:
            output.append(f"   ✅ All permissions look good!")
            output.append(f"   ✅ ESC cancellation should work")
            output.append(f"\n   Test it: Send a query, then press ESC to cancel")
        else:
            output.append(f"   ⚠️  Some permissions are missing")
            output.append(f"   📖 Follow the steps above to enable all features")

        output.append(f"\n" + "=" * 70)
        output.append(f"For more help: /help\n")

        return "\n".join(output)
