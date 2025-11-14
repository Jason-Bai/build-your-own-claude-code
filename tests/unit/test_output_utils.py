"""
Unit tests for Output Utilities

Tests OutputFormatter class with output levels, styling, markdown detection,
code highlighting, and table rendering.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from src.utils.output import OutputFormatter, OutputLevel


@pytest.mark.unit
class TestOutputLevel:
    """Tests for OutputLevel enum"""

    def test_output_level_quiet_value(self):
        """Test QUIET level has value 0"""
        assert OutputLevel.QUIET.value == 0

    def test_output_level_normal_value(self):
        """Test NORMAL level has value 1"""
        assert OutputLevel.NORMAL.value == 1

    def test_output_level_verbose_value(self):
        """Test VERBOSE level has value 2"""
        assert OutputLevel.VERBOSE.value == 2

    def test_output_level_enum_members(self):
        """Test all OutputLevel members exist"""
        levels = list(OutputLevel)
        assert len(levels) == 3
        assert OutputLevel.QUIET in levels
        assert OutputLevel.NORMAL in levels
        assert OutputLevel.VERBOSE in levels


@pytest.mark.unit
class TestOutputFormatterInitialization:
    """Tests for OutputFormatter initialization"""

    def test_formatter_has_console(self):
        """Test OutputFormatter has console attribute"""
        assert hasattr(OutputFormatter, 'console')

    def test_formatter_has_level(self):
        """Test OutputFormatter has level attribute"""
        assert hasattr(OutputFormatter, 'level')

    def test_default_level_is_normal(self):
        """Test default output level is NORMAL"""
        assert OutputFormatter.level == OutputLevel.NORMAL

    def test_set_level_changes_level(self):
        """Test set_level changes the output level"""
        original_level = OutputFormatter.level
        try:
            OutputFormatter.set_level(OutputLevel.VERBOSE)
            assert OutputFormatter.level == OutputLevel.VERBOSE

            OutputFormatter.set_level(OutputLevel.QUIET)
            assert OutputFormatter.level == OutputLevel.QUIET
        finally:
            OutputFormatter.set_level(original_level)


@pytest.mark.unit
class TestOutputFormatterBasicMethods:
    """Tests for basic output methods"""

    def setup_method(self):
        """Reset level before each test"""
        self.original_level = OutputFormatter.level
        OutputFormatter.set_level(OutputLevel.NORMAL)

    def teardown_method(self):
        """Restore level after each test"""
        OutputFormatter.set_level(self.original_level)

    def test_success_message_in_normal_mode(self):
        """Test success message prints in normal mode"""
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.success("Test success")
            mock_print.assert_called()

    def test_success_message_silent_in_quiet_mode(self):
        """Test success message silent in quiet mode"""
        OutputFormatter.set_level(OutputLevel.QUIET)
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.success("Test success")
            # Should not be called because QUIET < NORMAL
            assert not mock_print.called

    def test_error_message_always_shows(self):
        """Test error message shows in all modes"""
        for level in [OutputLevel.QUIET, OutputLevel.NORMAL, OutputLevel.VERBOSE]:
            OutputFormatter.set_level(level)
            with patch.object(OutputFormatter.console, 'print') as mock_print:
                OutputFormatter.error("Test error")
                mock_print.assert_called()

    def test_info_message_in_normal_mode(self):
        """Test info message prints in normal mode"""
        OutputFormatter.set_level(OutputLevel.NORMAL)
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.info("Test info")
            mock_print.assert_called()

    def test_info_message_silent_in_quiet_mode(self):
        """Test info message silent in quiet mode"""
        OutputFormatter.set_level(OutputLevel.QUIET)
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.info("Test info")
            assert not mock_print.called

    def test_warning_message_in_normal_mode(self):
        """Test warning message prints in normal mode"""
        OutputFormatter.set_level(OutputLevel.NORMAL)
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.warning("Test warning")
            mock_print.assert_called()

    def test_thinking_message_in_verbose_mode(self):
        """Test thinking message only prints in verbose mode"""
        OutputFormatter.set_level(OutputLevel.VERBOSE)
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.thinking("Thinking...")
            mock_print.assert_called()

    def test_thinking_message_silent_in_normal_mode(self):
        """Test thinking message silent in normal mode"""
        OutputFormatter.set_level(OutputLevel.NORMAL)
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.thinking("Thinking...")
            assert not mock_print.called

    def test_debug_message_in_verbose_mode(self):
        """Test debug message only prints in verbose mode"""
        OutputFormatter.set_level(OutputLevel.VERBOSE)
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.debug("Debug info")
            mock_print.assert_called()

    def test_debug_message_silent_in_normal_mode(self):
        """Test debug message silent in normal mode"""
        OutputFormatter.set_level(OutputLevel.NORMAL)
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.debug("Debug info")
            assert not mock_print.called


@pytest.mark.unit
class TestOutputFormatterToolMethods:
    """Tests for tool-related output methods"""

    def setup_method(self):
        """Reset level before each test"""
        self.original_level = OutputFormatter.level
        OutputFormatter.set_level(OutputLevel.NORMAL)

    def teardown_method(self):
        """Restore level after each test"""
        OutputFormatter.set_level(self.original_level)

    def test_tool_use_prints_tool_name(self):
        """Test tool_use prints tool name"""
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.tool_use("ReadTool")
            mock_print.assert_called()

    def test_tool_use_without_params_in_normal_mode(self):
        """Test tool_use without params doesn't print parameters"""
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.tool_use("ReadTool", None)
            # Should print tool name but not parameters
            assert mock_print.call_count >= 1

    def test_tool_use_with_params_in_verbose_mode(self):
        """Test tool_use with params prints in verbose mode"""
        OutputFormatter.set_level(OutputLevel.VERBOSE)
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            params = {"path": "/test", "limit": 10}
            OutputFormatter.tool_use("ReadTool", params)
            # Should print both tool name and parameters
            assert mock_print.call_count >= 2

    def test_tool_result_success_in_verbose_mode(self):
        """Test tool_result for successful execution"""
        OutputFormatter.set_level(OutputLevel.VERBOSE)
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.tool_result("ReadTool", success=True, output="content")
            mock_print.assert_called()

    def test_tool_result_failure_in_verbose_mode(self):
        """Test tool_result for failed execution"""
        OutputFormatter.set_level(OutputLevel.VERBOSE)
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.tool_result("ReadTool", success=False, output="error")
            mock_print.assert_called()

    def test_tool_result_truncates_long_output(self):
        """Test tool_result truncates output longer than 200 chars"""
        OutputFormatter.set_level(OutputLevel.VERBOSE)
        long_output = "x" * 300
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.tool_result("ReadTool", success=True, output=long_output)
            # Call should be made with truncated output
            mock_print.assert_called()


@pytest.mark.unit
class TestMarkdownDetection:
    """Tests for Markdown detection"""

    def test_contains_markdown_h1_header(self):
        """Test markdown detection for h1 headers"""
        assert OutputFormatter._contains_markdown("# Header")

    def test_contains_markdown_h2_header(self):
        """Test markdown detection for h2 headers"""
        assert OutputFormatter._contains_markdown("## Subheader")

    def test_contains_markdown_h3_header(self):
        """Test markdown detection for h3 headers"""
        assert OutputFormatter._contains_markdown("### Sub-subheader")

    def test_contains_markdown_h4_header(self):
        """Test markdown detection for h4 headers"""
        assert OutputFormatter._contains_markdown("#### Fourth level")

    def test_contains_markdown_unordered_list_dash(self):
        """Test markdown detection for unordered lists with dash"""
        assert OutputFormatter._contains_markdown("- item one")

    def test_contains_markdown_unordered_list_asterisk(self):
        """Test markdown detection for unordered lists with asterisk"""
        assert OutputFormatter._contains_markdown("* item one")

    def test_contains_markdown_unordered_list_plus(self):
        """Test markdown detection for unordered lists with plus"""
        assert OutputFormatter._contains_markdown("+ item one")

    def test_contains_markdown_blockquote(self):
        """Test markdown detection for blockquotes"""
        assert OutputFormatter._contains_markdown("> quoted text")

    def test_contains_markdown_code_block_spaces(self):
        """Test markdown detection for code blocks with spaces"""
        assert OutputFormatter._contains_markdown("    code line")

    def test_contains_markdown_code_block_tab(self):
        """Test markdown detection for code blocks with tabs"""
        assert OutputFormatter._contains_markdown("\tcode line")

    def test_contains_markdown_inline_bold(self):
        """Test markdown detection for inline bold"""
        assert OutputFormatter._contains_markdown("This is **bold** text")

    def test_contains_markdown_inline_bold_underscore(self):
        """Test markdown detection for inline bold with underscores"""
        assert OutputFormatter._contains_markdown("This is __bold__ text")

    def test_contains_markdown_inline_code(self):
        """Test markdown detection for inline code"""
        assert OutputFormatter._contains_markdown("Use `command` here")

    def test_contains_markdown_link(self):
        """Test markdown detection for links"""
        assert OutputFormatter._contains_markdown("[link text](http://url)")

    def test_contains_markdown_table(self):
        """Test markdown detection for tables"""
        assert OutputFormatter._contains_markdown("| Header | Value |")

    def test_no_markdown_plain_text(self):
        """Test plain text is not detected as markdown"""
        assert not OutputFormatter._contains_markdown("Plain text without formatting")

    def test_no_markdown_single_dash(self):
        """Test single dash not detected as markdown (needs space)"""
        assert not OutputFormatter._contains_markdown("text-with-dashes")

    def test_contains_markdown_multiline_with_headers(self):
        """Test markdown detection in multiline text"""
        text = """Some intro text
# Main Header
More content here"""
        assert OutputFormatter._contains_markdown(text)


@pytest.mark.unit
class TestPrintAssistantResponse:
    """Tests for print_assistant_response method"""

    def test_print_assistant_response_with_markdown(self):
        """Test printing assistant response with markdown"""
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.print_assistant_response("# Title\nSome content")
            mock_print.assert_called()

    def test_print_assistant_response_plain_text(self):
        """Test printing assistant response with plain text"""
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.print_assistant_response("Just plain text")
            mock_print.assert_called()

    def test_print_assistant_response_with_code_block(self):
        """Test printing assistant response with code block"""
        code_response = """Here's the code:
    def hello():
        print('world')"""
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.print_assistant_response(code_response)
            mock_print.assert_called()


@pytest.mark.unit
class TestCodeBlockPrinting:
    """Tests for code block printing"""

    def test_print_code_block_python_default(self):
        """Test printing Python code block with default language"""
        code = "print('hello')"
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.print_code_block(code)
            mock_print.assert_called()

    def test_print_code_block_with_language(self):
        """Test printing code block with specific language"""
        code = "SELECT * FROM users"
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.print_code_block(code, language="sql")
            mock_print.assert_called()

    def test_print_code_block_with_title(self):
        """Test printing code block with title"""
        code = "echo 'hello'"
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.print_code_block(code, title="Bash Example")
            mock_print.assert_called()

    def test_print_code_block_without_title(self):
        """Test printing code block without title"""
        code = "x = 10"
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.print_code_block(code)
            mock_print.assert_called()


@pytest.mark.unit
class TestTablePrinting:
    """Tests for table printing"""

    def test_print_table_basic(self):
        """Test printing basic table"""
        headers = ["Name", "Value"]
        rows = [["Item1", "10"], ["Item2", "20"]]
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.print_table(headers, rows)
            mock_print.assert_called()

    def test_print_table_with_title(self):
        """Test printing table with title"""
        headers = ["Header1", "Header2"]
        rows = [["A", "B"], ["C", "D"]]
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.print_table(headers, rows, title="Test Table")
            mock_print.assert_called()

    def test_print_table_empty_rows(self):
        """Test printing table with no rows"""
        headers = ["Col1", "Col2"]
        rows = []
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.print_table(headers, rows)
            mock_print.assert_called()

    def test_print_table_converts_types_to_string(self):
        """Test printing table converts numeric types to strings"""
        headers = ["Name", "Count", "Active"]
        rows = [[1, 100, True], ["Item", 50, False]]
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.print_table(headers, rows)
            mock_print.assert_called()


@pytest.mark.unit
class TestSeparators:
    """Tests for separator and formatting methods"""

    def setup_method(self):
        """Reset level before each test"""
        self.original_level = OutputFormatter.level
        OutputFormatter.set_level(OutputLevel.NORMAL)

    def teardown_method(self):
        """Restore level after each test"""
        OutputFormatter.set_level(self.original_level)

    def test_separator_in_normal_mode(self):
        """Test separator prints in normal mode"""
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.separator()
            mock_print.assert_called()

    def test_separator_with_custom_char(self):
        """Test separator with custom character"""
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.separator(char="-", length=10)
            mock_print.assert_called()

    def test_separator_silent_in_quiet_mode(self):
        """Test separator silent in quiet mode"""
        OutputFormatter.set_level(OutputLevel.QUIET)
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.separator()
            assert not mock_print.called

    def test_print_separator(self):
        """Test print_separator method"""
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.print_separator()
            mock_print.assert_called()

    def test_section_in_normal_mode(self):
        """Test section prints in normal mode"""
        OutputFormatter.set_level(OutputLevel.NORMAL)
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.section("Test Section")
            mock_print.assert_called()

    def test_section_silent_in_quiet_mode(self):
        """Test section silent in quiet mode"""
        OutputFormatter.set_level(OutputLevel.QUIET)
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.section("Test Section")
            assert not mock_print.called


@pytest.mark.unit
class TestWelcomeScreen:
    """Tests for welcome screen printing"""

    def test_print_welcome_basic(self):
        """Test printing welcome screen"""
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.print_welcome("claude-sonnet-4", "anthropic", 7)
            mock_print.assert_called()

    def test_print_welcome_with_claude_info(self):
        """Test printing welcome screen with claude info"""
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.print_welcome("claude-sonnet-4", "anthropic", 7, claude_md_info="Version 1.0")
            mock_print.assert_called()


@pytest.mark.unit
class TestUserInputOutput:
    """Tests for user input/output methods"""

    def test_print_user_prompt(self):
        """Test print_user_prompt"""
        with patch('builtins.print') as mock_print:
            OutputFormatter.print_user_prompt()
            mock_print.assert_called_once()
            # Check that it ends with " " and no newline
            call_kwargs = mock_print.call_args[1]
            assert call_kwargs.get('end') == ""
            assert call_kwargs.get('flush') is True

    def test_print_user_input_with_text(self):
        """Test print_user_input with text"""
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.print_user_input("user typed this")
            mock_print.assert_called()

    def test_print_user_input_empty_text(self):
        """Test print_user_input with empty text"""
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.print_user_input("")
            mock_print.assert_called()

    def test_print_assistant_response_header(self):
        """Test print_assistant_response_header"""
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.print_assistant_response_header()
            mock_print.assert_called()

    def test_agent_response(self):
        """Test agent_response method"""
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.agent_response("Agent response text")
            mock_print.assert_called()


@pytest.mark.unit
class TestOutputEdgeCases:
    """Tests for edge cases in output methods"""

    def setup_method(self):
        """Reset level before each test"""
        self.original_level = OutputFormatter.level
        OutputFormatter.set_level(OutputLevel.NORMAL)

    def teardown_method(self):
        """Restore level after each test"""
        OutputFormatter.set_level(self.original_level)

    def test_success_with_emoji(self):
        """Test success message with emoji"""
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.success("✓ Operation successful")
            mock_print.assert_called()

    def test_error_with_special_chars(self):
        """Test error message with special characters"""
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.error("Error: file/path/not/found")
            mock_print.assert_called()

    def test_markdown_with_multiple_features(self):
        """Test markdown detection with multiple features"""
        text = """# Title
## Subtitle
- Item 1
- Item 2
**Bold text**
`code`"""
        assert OutputFormatter._contains_markdown(text)

    def test_tool_use_empty_params(self):
        """Test tool_use with empty params dict"""
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.tool_use("Tool", {})
            mock_print.assert_called()

    def test_print_table_with_numeric_headers(self):
        """Test print_table converts numeric headers"""
        headers = ["Col1", "Col2"]
        rows = [[1, 2], [3, 4]]
        with patch.object(OutputFormatter.console, 'print') as mock_print:
            OutputFormatter.print_table(headers, rows)
            mock_print.assert_called()

    def test_contains_markdown_indented_list(self):
        """Test markdown detection for indented lists"""
        text = """Normal text
  - Indented item"""
        assert OutputFormatter._contains_markdown(text)

    def test_contains_markdown_leading_spaces_in_header(self):
        """Test markdown detection with leading spaces in header"""
        text = "  # Indented header"
        assert OutputFormatter._contains_markdown(text)
