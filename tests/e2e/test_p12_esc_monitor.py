"""
P12: Global ESC Monitor - End-to-End Tests

These tests simulate REAL user behavior to expose gaps between design and reality.

Test Strategy:
- Tests are expected to FAIL initially (permission issues, focus detection, etc.)
- Each failure reveals a documentation-reality gap
- Tests use real CLI process, not mocks

Prerequisites:
- macOS: Accessibility permissions required (tests will skip if not available)
- Linux/Windows: Should work without special permissions
"""

import pytest
import subprocess
import sys
import time
import signal
import os
from pathlib import Path


class CLISession:
    """
    Wrapper for real CLI subprocess.

    Simulates user interactions with the actual application.
    """

    def __init__(self, timeout=30):
        self.timeout = timeout
        self.process = None
        self.output_lines = []

    def start(self, env=None):
        """Start CLI process"""
        cmd = [sys.executable, "-m", "src.main"]

        # Merge with current env
        full_env = {**os.environ}
        if env:
            full_env.update(env)

        # Disable buffering for real-time output
        full_env["PYTHONUNBUFFERED"] = "1"

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=full_env
        )

        # Wait for startup (look for welcome message)
        self._wait_for_ready()

    def _wait_for_ready(self, timeout=10):
        """Wait for CLI to be ready for input"""
        start = time.time()
        while time.time() - start < timeout:
            line = self._read_line(timeout=0.5)
            if line and ("You:" in line or "started" in line or "session" in line.lower()):
                return True

        # Timeout - dump what we got
        print("\n⚠️  CLI startup timeout. Captured output:")
        print("STDOUT:", "".join(self.output_lines))
        if self.process and self.process.stderr:
            stderr = self.process.stderr.read()
            print("STDERR:", stderr)

        raise TimeoutError(f"CLI failed to start within {timeout}s")

    def _read_line(self, timeout=1.0):
        """Read one line from stdout with timeout"""
        import select

        if not self.process or not self.process.stdout:
            return None

        ready, _, _ = select.select([self.process.stdout], [], [], timeout)
        if ready:
            line = self.process.stdout.readline()
            self.output_lines.append(line)
            return line
        return None

    def send_input(self, text):
        """Send user input to CLI"""
        if not self.process or not self.process.stdin:
            raise RuntimeError("CLI not started")

        self.process.stdin.write(text + "\n")
        self.process.stdin.flush()

    def send_esc(self):
        """
        Simulate ESC key press by sending SIGINT.

        Note: This is NOT a perfect ESC simulation - it's Ctrl+C.
        Real ESC requires pynput or similar keyboard library.
        For true E2E testing, need manual verification or OS-level automation.
        """
        if not self.process:
            raise RuntimeError("CLI not started")

        self.process.send_signal(signal.SIGINT)

    def read_output(self, timeout=2.0, expect_keyword=None):
        """
        Read output until timeout or keyword found.

        Returns:
            str: Accumulated output
        """
        output = []
        start = time.time()

        while time.time() - start < timeout:
            line = self._read_line(timeout=0.1)
            if line:
                output.append(line)
                if expect_keyword and expect_keyword in line:
                    break

        return "".join(output)

    def terminate(self):
        """Clean shutdown"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()


# ============================================================================
# Scenario 1: Permission Detection
# ============================================================================

@pytest.mark.e2e
class TestPermissionDetection:
    """Scenario 1: Verify permission detection on startup"""

    def test_startup_shows_permission_status(self):
        """
        Test 1.1/1.2: CLI should indicate whether ESC monitoring is available

        Expected:
        - If no permissions: Warning message displayed
        - If has permissions: No warning, monitor starts
        """
        with CLISession() as session:
            output = session.read_output(timeout=3)

            # Check for either warning or successful start
            has_warning = "Accessibility" in output or "permission" in output.lower()
            has_success = "GlobalKeyboardMonitor started" in output or "started" in output.lower()

            # At least one should be true
            assert has_warning or has_success, (
                "Expected either permission warning or successful start, "
                f"but got: {output[:200]}"
            )

            # CLI should not crash
            assert session.process.poll() is None, "CLI crashed on startup"

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS-specific test")
    def test_macos_permission_check(self):
        """
        Test 1.1: Verify macOS permission check behavior

        Reality Check: Does the permission check actually work?
        """
        with CLISession() as session:
            output = session.read_output(timeout=3)

            # On macOS, we should see some indication of permission status
            # Either "started" (has permission) or "disabled" (no permission)
            assert "monitor" in output.lower() or "keyboard" in output.lower(), (
                f"Expected monitor status message, got: {output[:200]}"
            )


# ============================================================================
# Scenario 2: ESC During LLM Execution
# ============================================================================

@pytest.mark.e2e
class TestESCDuringLLM:
    """Scenario 2: Verify ESC cancels LLM calls"""

    @pytest.mark.skip(reason="Requires real LLM API and manual ESC press - manual test only")
    def test_esc_cancels_llm_call(self):
        """
        Test 2.1: ESC should cancel LLM call within 1 second

        Manual Test Procedure:
        1. Run: python -m src.main
        2. Send: "帮我生成一个包含1000个函数的Python模块"
        3. Press ESC after 2 seconds
        4. Verify: "cancelled" message appears within 1 second

        Expected: ⚠️ Execution cancelled by user (ESC pressed)
        """
        pytest.skip("This test requires manual execution with real ESC key")

    def test_cli_handles_cancellation_signal(self):
        """
        Test 2.1 (Partial): Verify CLI handles cancellation signals

        Note: Uses SIGINT instead of real ESC key
        """
        with CLISession() as session:
            # Send a command that would trigger LLM
            session.send_input("hello")
            time.sleep(0.5)

            # Simulate cancellation (not perfect, but closest we can get)
            session.send_esc()

            # Check output
            output = session.read_output(timeout=2)

            # Should either show cancellation or "Use /exit" message
            has_cancellation_handling = (
                "cancelled" in output.lower() or
                "exit" in output.lower() or
                "interrupt" in output.lower()
            )

            assert has_cancellation_handling, (
                f"Expected cancellation handling, got: {output[:200]}"
            )


# ============================================================================
# Scenario 3: ESC During Tool Execution
# ============================================================================

@pytest.mark.e2e
class TestESCDuringTool:
    """Scenario 3: Verify ESC cancels tool execution"""

    @pytest.mark.skip(reason="Requires manual ESC press during tool execution")
    def test_esc_cancels_subprocess_tool(self):
        """
        Test 3.1: ESC should kill subprocess tools

        Manual Test Procedure:
        1. Run: python -m src.main
        2. Send: "运行命令: sleep 30"
        3. Press ESC after 2 seconds
        4. Verify: Process killed, no zombie processes

        Expected: ⚠️ Tool execution cancelled by user
        """
        pytest.skip("This test requires manual execution")

    @pytest.mark.skip(reason="Requires MCP server setup and manual ESC")
    def test_esc_cancels_mcp_tool(self):
        """
        Test 3.2: ESC should cancel MCP tool calls

        Manual Test Procedure:
        1. Setup MCP filesystem server
        2. Run: python -m src.main
        3. Send: "读取这个超大文件"
        4. Press ESC during read
        5. Verify: MCP call cancelled, no hanging connections
        """
        pytest.skip("This test requires MCP server setup")


# ============================================================================
# Scenario 4: ESC During Input Prompt
# ============================================================================

@pytest.mark.e2e
class TestESCDuringInput:
    """Scenario 4: Verify ESC during input clears text (doesn't cancel)"""

    @pytest.mark.skip(reason="Requires interactive terminal with prompt_toolkit")
    def test_esc_clears_input_not_cancels(self):
        """
        Test 4.1: ESC while typing should clear input, NOT cancel execution

        Manual Test Procedure:
        1. Run: python -m src.main
        2. Start typing: "帮我创建一个Flas"
        3. Press ESC (before Enter)
        4. Verify: Input cleared, prompt resets
        5. Verify: No cancellation message

        Expected: Input cleared, no "cancelled" message
        """
        pytest.skip("This test requires interactive terminal")


# ============================================================================
# Scenario 5: Edge Cases
# ============================================================================

@pytest.mark.e2e
class TestEdgeCases:
    """Scenario 5: Edge case behaviors"""

    def test_esc_before_first_input(self):
        """
        Test 5.1: ESC before any execution should not crash
        """
        with CLISession() as session:
            # Immediately send ESC
            session.send_esc()

            # Should still be running
            time.sleep(1)
            assert session.process.poll() is None, "CLI crashed after ESC"

    @pytest.mark.skip(reason="Requires timing control of LLM completion")
    def test_esc_after_execution_completes(self):
        """
        Test 5.2: ESC after execution completes should have no effect
        """
        pytest.skip("This test requires precise timing control")

    def test_cancellation_token_reuse(self):
        """
        Test 5.3: New queries should use new cancellation tokens

        Indirect test: Send multiple queries, verify CLI doesn't reuse old state
        """
        with CLISession() as session:
            # Send first query
            session.send_input("/status")
            output1 = session.read_output(timeout=2)
            assert "status" in output1.lower() or "session" in output1.lower()

            # Send second query
            session.send_input("/status")
            output2 = session.read_output(timeout=2)
            assert "status" in output2.lower() or "session" in output2.lower()

            # Should not see "already cancelled" errors
            combined = output1 + output2
            assert "already cancelled" not in combined.lower()


# ============================================================================
# Scenario 6: Platform-Specific Behavior
# ============================================================================

@pytest.mark.e2e
class TestPlatformSpecific:
    """Scenario 6: Platform-specific behaviors"""

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS-specific")
    def test_terminal_detection_fallback(self):
        """
        Test 6.1: Verify terminal detection doesn't crash on unknown terminal

        This test verifies that even if terminal name is not in the hardcoded
        list, the focus check falls back gracefully.
        """
        with CLISession() as session:
            output = session.read_output(timeout=3)

            # Should start successfully regardless of terminal type
            assert session.process.poll() is None, "CLI crashed during terminal detection"

    @pytest.mark.skipif(sys.platform == "darwin", reason="Non-macOS test")
    def test_non_macos_no_focus_check(self):
        """
        Test 6.2/6.3: Verify Linux/Windows don't require focus check

        Expected: _is_window_focused() returns True (fallback behavior)
        """
        with CLISession() as session:
            output = session.read_output(timeout=3)

            # Should start successfully
            assert session.process.poll() is None

            # Should not see macOS-specific permission warnings
            assert "Accessibility" not in output


# ============================================================================
# Helper Functions for Manual Testing
# ============================================================================

def run_manual_esc_test():
    """
    Helper function for manual ESC testing.

    Usage:
        python -m pytest tests/e2e/test_p12_esc_monitor.py::run_manual_esc_test -v -s

    This will guide you through manual testing steps.
    """
    print("\n" + "="*70)
    print("MANUAL ESC CANCELLATION TEST")
    print("="*70)
    print("\nThis test requires manual keyboard input.")
    print("\nProcedure:")
    print("  1. The CLI will start automatically")
    print("  2. When you see the prompt, send a query that triggers LLM")
    print("  3. Press ESC while the LLM is processing")
    print("  4. Observe the behavior")
    print("\nPress Enter to start...")
    input()

    with CLISession() as session:
        print("\n✅ CLI started. Send a query now (e.g., '生成一个复杂的程序')")
        print("   Then press ESC to cancel.\n")

        # Wait for user interaction
        time.sleep(30)

        print("\n📊 Output captured:")
        print("-" * 70)
        for line in session.output_lines[-20:]:  # Last 20 lines
            print(line, end="")
        print("-" * 70)


if __name__ == "__main__":
    # Run manual test helper
    run_manual_esc_test()
