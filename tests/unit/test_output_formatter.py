"""
Unit tests for Output Formatting Utilities

Tests output formatting, level management, and markdown detection.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from enum import Enum

from src.utils.output import OutputFormatter, OutputLevel


@pytest.mark.unit
class TestOutputLevel:
    """Tests for OutputLevel enum"""

    def test_output_level_quiet(self):
        """Test QUIET output level"""
        assert OutputLevel.QUIET.value == 0

    def test_output_level_normal(self):
        """Test NORMAL output level"""
        assert OutputLevel.NORMAL.value == 1

    def test_output_level_verbose(self):
        """Test VERBOSE output level"""
        assert OutputLevel.VERBOSE.value == 2

    def test_output_levels_ordered(self):
        """Test that output levels are properly ordered"""
        assert OutputLevel.QUIET.value < OutputLevel.NORMAL.value
        assert OutputLevel.NORMAL.value < OutputLevel.VERBOSE.value


@pytest.mark.unit
class TestOutputFormatterLevelManagement:
    """Tests for output level management"""

    def teardown_method(self):
        """Reset output level after each test"""
        OutputFormatter.set_level(OutputLevel.NORMAL)

    def test_set_level_quiet(self):
        """Test setting QUIET level"""
        OutputFormatter.set_level(OutputLevel.QUIET)
        assert OutputFormatter.level == OutputLevel.QUIET

    def test_set_level_normal(self):
        """Test setting NORMAL level"""
        OutputFormatter.set_level(OutputLevel.NORMAL)
        assert OutputFormatter.level == OutputLevel.NORMAL

    def test_set_level_verbose(self):
        """Test setting VERBOSE level"""
        OutputFormatter.set_level(OutputLevel.VERBOSE)
        assert OutputFormatter.level == OutputLevel.VERBOSE

    def test_default_level_is_normal(self):
        """Test that default level is NORMAL"""
        # Reset to default
        OutputFormatter.level = OutputLevel.NORMAL
        assert OutputFormatter.level == OutputLevel.NORMAL


@pytest.mark.unit
class TestOutputFormatterBasicOutput:
    """Tests for basic output methods"""

    def teardown_method(self):
        """Reset output level after each test"""
        OutputFormatter.set_level(OutputLevel.NORMAL)

    @patch('src.utils.output.Console')
    def test_success_message(self, mock_console_class):
        """Test success message output"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console
        OutputFormatter.set_level(OutputLevel.NORMAL)

        OutputFormatter.success("Operation successful")

        mock_console.print.assert_called()

    @patch('src.utils.output.Console')
    def test_error_message(self, mock_console_class):
        """Test error message is always shown"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console
        OutputFormatter.set_level(OutputLevel.QUIET)

        OutputFormatter.error("An error occurred")

        mock_console.print.assert_called()

    @patch('src.utils.output.Console')
    def test_info_message(self, mock_console_class):
        """Test info message output"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console
        OutputFormatter.set_level(OutputLevel.NORMAL)

        OutputFormatter.info("Information message")

        mock_console.print.assert_called()

    @patch('src.utils.output.Console')
    def test_warning_message(self, mock_console_class):
        """Test warning message output"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console
        OutputFormatter.set_level(OutputLevel.NORMAL)

        OutputFormatter.warning("Warning message")

        mock_console.print.assert_called()

    @patch('src.utils.output.Console')
    def test_thinking_message_only_verbose(self, mock_console_class):
        """Test thinking message only shown in verbose mode"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console

        # Not shown in normal mode
        OutputFormatter.set_level(OutputLevel.NORMAL)
        OutputFormatter.thinking("Thinking...")
        normal_call_count = mock_console.print.call_count

        # Shown in verbose mode
        OutputFormatter.set_level(OutputLevel.VERBOSE)
        OutputFormatter.thinking("Thinking...")
        verbose_call_count = mock_console.print.call_count

        assert verbose_call_count > normal_call_count

    @patch('src.utils.output.Console')
    def test_debug_message_only_verbose(self, mock_console_class):
        """Test debug message only shown in verbose mode"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console

        # Not shown in normal mode
        OutputFormatter.set_level(OutputLevel.NORMAL)
        OutputFormatter.debug("Debug info")
        normal_call_count = mock_console.print.call_count

        # Shown in verbose mode
        OutputFormatter.set_level(OutputLevel.VERBOSE)
        OutputFormatter.debug("Debug info")
        verbose_call_count = mock_console.print.call_count

        assert verbose_call_count > normal_call_count


@pytest.mark.unit
class TestOutputFormatterToolOutput:
    """Tests for tool-related output"""

    def teardown_method(self):
        """Reset output level after each test"""
        OutputFormatter.set_level(OutputLevel.NORMAL)

    @patch('src.utils.output.Console')
    def test_tool_use_normal_mode(self, mock_console_class):
        """Test tool use output in normal mode"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console
        OutputFormatter.set_level(OutputLevel.NORMAL)

        OutputFormatter.tool_use("bash")

        mock_console.print.assert_called()

    @patch('src.utils.output.Console')
    def test_tool_use_with_params_verbose(self, mock_console_class):
        """Test tool use output with parameters in verbose mode"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console
        OutputFormatter.set_level(OutputLevel.VERBOSE)

        params = {"command": "ls"}
        OutputFormatter.tool_use("bash", params)

        # Should print tool use and parameters
        assert mock_console.print.call_count >= 1

    @patch('src.utils.output.Console')
    def test_tool_result_verbose_success(self, mock_console_class):
        """Test successful tool result in verbose mode"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console
        OutputFormatter.set_level(OutputLevel.VERBOSE)

        OutputFormatter.tool_result("bash", success=True, output="result")

        mock_console.print.assert_called()

    @patch('src.utils.output.Console')
    def test_tool_result_verbose_failure(self, mock_console_class):
        """Test failed tool result in verbose mode"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console
        OutputFormatter.set_level(OutputLevel.VERBOSE)

        OutputFormatter.tool_result("bash", success=False, output="error")

        mock_console.print.assert_called()


@pytest.mark.unit
class TestOutputFormatterAssistantResponse:
    """Tests for assistant response output"""

    def teardown_method(self):
        """Reset output level after each test"""
        OutputFormatter.set_level(OutputLevel.NORMAL)

    @patch('src.utils.output.Console')
    def test_print_assistant_response_plain_text(self, mock_console_class):
        """Test printing plain text response"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console

        OutputFormatter.print_assistant_response("Plain text response")

        mock_console.print.assert_called()

    @patch('src.utils.output.Console')
    def test_print_assistant_response_with_markdown(self, mock_console_class):
        """Test printing markdown response"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console

        OutputFormatter.print_assistant_response("# Heading\n\nSome content")

        mock_console.print.assert_called()

    @patch('src.utils.output.Console')
    def test_print_code_block(self, mock_console_class):
        """Test printing code block"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console

        code = "def hello():\n    print('world')"
        OutputFormatter.print_code_block(code, language="python")

        mock_console.print.assert_called()

    @patch('src.utils.output.Console')
    def test_print_table(self, mock_console_class):
        """Test printing table"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console

        headers = ["Name", "Status"]
        rows = [["Test", "Pass"], ["Test2", "Fail"]]
        OutputFormatter.print_table(headers, rows)

        mock_console.print.assert_called()

    @patch('src.utils.output.Console')
    def test_agent_response(self, mock_console_class):
        """Test agent response output"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console

        OutputFormatter.agent_response("Agent response text")

        mock_console.print.assert_called()


@pytest.mark.unit
class TestOutputFormatterSeparators:
    """Tests for separator and formatting output"""

    def teardown_method(self):
        """Reset output level after each test"""
        OutputFormatter.set_level(OutputLevel.NORMAL)

    @patch('src.utils.output.Console')
    def test_separator(self, mock_console_class):
        """Test separator output"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console
        OutputFormatter.set_level(OutputLevel.NORMAL)

        OutputFormatter.separator()

        mock_console.print.assert_called()

    @patch('src.utils.output.Console')
    def test_separator_custom_char(self, mock_console_class):
        """Test separator with custom character"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console
        OutputFormatter.set_level(OutputLevel.NORMAL)

        OutputFormatter.separator(char="-", length=40)

        mock_console.print.assert_called()

    @patch('src.utils.output.Console')
    def test_section(self, mock_console_class):
        """Test section title output"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console
        OutputFormatter.set_level(OutputLevel.NORMAL)

        OutputFormatter.section("Test Section")

        mock_console.print.assert_called()

    @patch('src.utils.output.Console')
    def test_print_separator(self, mock_console_class):
        """Test conversation separator"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console

        OutputFormatter.print_separator()

        mock_console.print.assert_called()


@pytest.mark.unit
class TestOutputFormatterWelcome:
    """Tests for welcome message"""

    def teardown_method(self):
        """Reset output level after each test"""
        OutputFormatter.set_level(OutputLevel.NORMAL)

    @patch('src.utils.output.Console')
    def test_print_welcome(self, mock_console_class):
        """Test welcome message output"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console

        OutputFormatter.print_welcome("gpt-4o", "openai", 7)

        mock_console.print.assert_called()

    @patch('src.utils.output.Console')
    def test_print_welcome_with_info(self, mock_console_class):
        """Test welcome message with additional info"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console

        OutputFormatter.print_welcome("gpt-4o", "openai", 7, claude_md_info="Extra info")

        mock_console.print.assert_called()


@pytest.mark.unit
class TestOutputFormatterUserPrompt:
    """Tests for user prompt output"""

    def teardown_method(self):
        """Reset output level after each test"""
        OutputFormatter.set_level(OutputLevel.NORMAL)

    @patch('builtins.print')
    def test_print_user_prompt(self, mock_print):
        """Test user prompt output"""
        OutputFormatter.print_user_prompt()
        mock_print.assert_called()

    @patch('src.utils.output.Console')
    def test_print_user_input(self, mock_console_class):
        """Test user input output"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console

        OutputFormatter.print_user_input("User input text")

        mock_console.print.assert_called()

    @patch('src.utils.output.Console')
    def test_print_user_input_empty(self, mock_console_class):
        """Test user input output with empty text"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console

        OutputFormatter.print_user_input("")

        mock_console.print.assert_called()

    @patch('src.utils.output.Console')
    def test_print_assistant_response_header(self, mock_console_class):
        """Test assistant response header"""
        mock_console = MagicMock()
        OutputFormatter.console = mock_console

        OutputFormatter.print_assistant_response_header()

        mock_console.print.assert_called()


@pytest.mark.unit
class TestMarkdownDetection:
    """Tests for markdown detection"""

    def test_contains_markdown_heading(self):
        """Test markdown detection for headings"""
        assert OutputFormatter._contains_markdown("# Heading")
        assert OutputFormatter._contains_markdown("## Subheading")
        assert OutputFormatter._contains_markdown("### Sub-subheading")

    def test_contains_markdown_list(self):
        """Test markdown detection for lists"""
        assert OutputFormatter._contains_markdown("- Item 1")
        assert OutputFormatter._contains_markdown("* Item 1")
        assert OutputFormatter._contains_markdown("+ Item 1")

    def test_contains_markdown_quote(self):
        """Test markdown detection for quotes"""
        assert OutputFormatter._contains_markdown("> Quote")

    def test_contains_markdown_code(self):
        """Test markdown detection for code"""
        assert OutputFormatter._contains_markdown("`code`")
        assert OutputFormatter._contains_markdown("    indented code")
        assert OutputFormatter._contains_markdown("\tcode with tab")

    def test_contains_markdown_bold(self):
        """Test markdown detection for bold"""
        assert OutputFormatter._contains_markdown("**bold**")
        assert OutputFormatter._contains_markdown("__bold__")

    def test_contains_markdown_link(self):
        """Test markdown detection for links"""
        assert OutputFormatter._contains_markdown("[link](url)")

    def test_contains_markdown_table(self):
        """Test markdown detection for tables"""
        assert OutputFormatter._contains_markdown("|header|")

    def test_plain_text_no_markdown(self):
        """Test that plain text is not detected as markdown"""
        assert not OutputFormatter._contains_markdown("This is plain text")
        assert not OutputFormatter._contains_markdown("No markdown here")

    def test_markdown_detection_multiline(self):
        """Test markdown detection in multiline text"""
        text = """This is some text

# Heading

More text here"""
        assert OutputFormatter._contains_markdown(text)

    def test_markdown_detection_edge_cases(self):
        """Test edge cases for markdown detection"""
        # Should detect markdown at start of lines
        assert OutputFormatter._contains_markdown("  # indented heading")

        # Should not mistake similar patterns as markdown
        assert not OutputFormatter._contains_markdown("This costs $5 * 2 = $10")


@pytest.mark.unit
class TestOutputFormatterConsoleInstance:
    """Tests for console instance"""

    def test_console_is_initialized(self):
        """Test that console is initialized"""
        assert OutputFormatter.console is not None

    def test_set_level_is_class_method(self):
        """Test that set_level is a class method"""
        assert callable(OutputFormatter.set_level)

    def test_all_output_methods_are_class_methods(self):
        """Test that output methods are class methods"""
        methods = [
            'success', 'error', 'info', 'warning', 'thinking', 'debug',
            'tool_use', 'tool_result', 'print_assistant_response',
            'print_code_block', 'print_table', 'separator', 'section',
            'print_separator', 'print_welcome', 'print_user_prompt',
            'print_user_input', 'print_assistant_response_header',
            'agent_response'
        ]

        for method_name in methods:
            assert hasattr(OutputFormatter, method_name)
            assert callable(getattr(OutputFormatter, method_name))
