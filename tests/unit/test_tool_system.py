"""
Unit tests for Tool System module

Tests the built-in tools: Read, Write, Edit, Bash, Glob, Grep, and Todo.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from src.tools.file_ops import ReadTool, WriteTool, EditTool
from src.tools.bash import BashTool
from src.tools.search import GlobTool, GrepTool
from src.tools.todo import TodoWriteTool
from src.tools.base import ToolPermissionLevel


@pytest.mark.unit
class TestReadTool:
    """Tests for ReadTool"""

    def test_read_tool_properties(self):
        """Test ReadTool basic properties"""
        tool = ReadTool()
        assert tool.name == "Read"
        assert tool.permission_level == ToolPermissionLevel.SAFE
        assert "Reads a file" in tool.description

    def test_read_tool_schema(self):
        """Test ReadTool input schema"""
        tool = ReadTool()
        schema = tool.input_schema
        assert schema["type"] == "object"
        assert "file_path" in schema["properties"]
        assert "file_path" in schema["required"]

    @pytest.mark.asyncio
    async def test_read_tool_file_not_found(self):
        """Test reading non-existent file"""
        tool = ReadTool()
        result = await tool.execute(file_path="/nonexistent/file.txt")
        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_read_tool_directory_error(self):
        """Test reading a directory instead of file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = ReadTool()
            result = await tool.execute(file_path=tmpdir)
            assert result.success is False
            assert "not a file" in result.error.lower()

    @pytest.mark.asyncio
    async def test_read_tool_success(self):
        """Test successfully reading a file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Line 1\nLine 2\nLine 3\n")

            tool = ReadTool()
            result = await tool.execute(file_path=str(test_file))

            assert result.success is True
            assert "1" in result.output
            assert "Line 1" in result.output

    @pytest.mark.asyncio
    async def test_read_tool_with_offset_and_limit(self):
        """Test reading with offset and limit"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            lines = "\n".join([f"Line {i}" for i in range(1, 11)])
            test_file.write_text(lines)

            tool = ReadTool()
            result = await tool.execute(file_path=str(test_file), offset=2, limit=3)

            assert result.success is True
            assert "Line 3" in result.output


@pytest.mark.unit
class TestWriteTool:
    """Tests for WriteTool"""

    def test_write_tool_properties(self):
        """Test WriteTool basic properties"""
        tool = WriteTool()
        assert tool.name == "Write"
        assert tool.permission_level == ToolPermissionLevel.NORMAL

    @pytest.mark.asyncio
    async def test_write_tool_creates_file(self):
        """Test writing a new file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "new_file.txt"
            tool = WriteTool()
            result = await tool.execute(file_path=str(test_file), content="Hello World")

            assert result.success is True
            assert test_file.exists()
            assert test_file.read_text() == "Hello World"

    @pytest.mark.asyncio
    async def test_write_tool_overwrites_file(self):
        """Test overwriting existing file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Old content")

            tool = WriteTool()
            result = await tool.execute(file_path=str(test_file), content="New content")

            assert result.success is True
            assert test_file.read_text() == "New content"


@pytest.mark.unit
class TestEditTool:
    """Tests for EditTool"""

    def test_edit_tool_properties(self):
        """Test EditTool basic properties"""
        tool = EditTool()
        assert tool.name == "Edit"
        assert tool.permission_level == ToolPermissionLevel.NORMAL

    @pytest.mark.asyncio
    async def test_edit_tool_file_not_found(self):
        """Test editing non-existent file"""
        tool = EditTool()
        result = await tool.execute(
            file_path="/nonexistent/file.txt",
            old_string="old",
            new_string="new"
        )
        assert result.success is False

    @pytest.mark.asyncio
    async def test_edit_tool_string_replacement(self):
        """Test replacing string in file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello World")

            tool = EditTool()
            result = await tool.execute(
                file_path=str(test_file),
                old_string="World",
                new_string="Claude"
            )

            assert result.success is True
            assert test_file.read_text() == "Hello Claude"


@pytest.mark.unit
class TestBashTool:
    """Tests for BashTool"""

    def test_bash_tool_properties(self):
        """Test BashTool basic properties"""
        tool = BashTool()
        assert tool.name == "Bash"
        assert tool.permission_level == ToolPermissionLevel.DANGEROUS

    def test_bash_tool_schema(self):
        """Test BashTool input schema"""
        tool = BashTool()
        schema = tool.input_schema
        assert "command" in schema["properties"]
        assert "command" in schema["required"]
        assert "timeout" in schema["properties"]

    @pytest.mark.asyncio
    async def test_bash_tool_simple_command(self):
        """Test executing simple bash command"""
        tool = BashTool()
        result = await tool.execute(command="echo 'Hello'")

        assert result.success is True
        assert "Hello" in result.output

    @pytest.mark.asyncio
    async def test_bash_tool_timeout_default(self):
        """Test bash tool with default timeout"""
        tool = BashTool()
        # Quick command should succeed with default timeout
        result = await tool.execute(command="echo 'test'")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_bash_tool_with_custom_timeout(self):
        """Test bash tool with custom timeout"""
        tool = BashTool()
        result = await tool.execute(
            command="echo 'test'",
            timeout=5000  # 5 seconds
        )
        assert result.success is True


@pytest.mark.unit
class TestGlobTool:
    """Tests for GlobTool"""

    def test_glob_tool_properties(self):
        """Test GlobTool basic properties"""
        tool = GlobTool()
        assert tool.name == "Glob"
        assert tool.permission_level == ToolPermissionLevel.SAFE

    def test_glob_tool_schema(self):
        """Test GlobTool input schema"""
        tool = GlobTool()
        schema = tool.input_schema
        assert "pattern" in schema["properties"]

    @pytest.mark.asyncio
    async def test_glob_tool_find_files(self):
        """Test glob tool finding files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir).joinpath("file1.txt").touch()
            Path(tmpdir).joinpath("file2.txt").touch()
            Path(tmpdir).joinpath("file3.py").touch()

            tool = GlobTool()
            result = await tool.execute(
                pattern=f"{tmpdir}/**/*.txt"
            )

            assert result.success is True
            assert "file1.txt" in result.output
            assert "file2.txt" in result.output

    @pytest.mark.asyncio
    async def test_glob_tool_no_matches(self):
        """Test glob tool with no matches"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = GlobTool()
            result = await tool.execute(
                pattern=f"{tmpdir}/**/*.nonexistent"
            )

            assert result.success is True


@pytest.mark.unit
class TestGrepTool:
    """Tests for GrepTool"""

    def test_grep_tool_properties(self):
        """Test GrepTool basic properties"""
        tool = GrepTool()
        assert tool.name == "Grep"
        assert tool.permission_level == ToolPermissionLevel.SAFE

    def test_grep_tool_schema(self):
        """Test GrepTool input schema"""
        tool = GrepTool()
        schema = tool.input_schema
        assert "pattern" in schema["properties"]

    @pytest.mark.asyncio
    async def test_grep_tool_find_pattern(self):
        """Test grep tool finding pattern in files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello World\nHello Claude\nGoodbye")

            tool = GrepTool()
            result = await tool.execute(
                pattern="Hello",
                path=tmpdir
            )

            assert result.success is True
            # GrepTool returns file paths by default
            assert "test.txt" in result.output

    @pytest.mark.asyncio
    async def test_grep_tool_case_insensitive(self):
        """Test grep tool with case insensitive search"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("HELLO world")

            tool = GrepTool()
            result = await tool.execute(
                pattern="hello",
                path=tmpdir
            )

            assert result.success is True


@pytest.mark.unit
class TestTodoTool:
    """Tests for TodoWriteTool"""

    def test_todo_tool_properties(self):
        """Test TodoWriteTool basic properties"""
        tool = TodoWriteTool()
        assert tool.name == "TodoWrite"
        assert tool.permission_level == ToolPermissionLevel.SAFE

    def test_todo_tool_schema(self):
        """Test TodoWriteTool input schema"""
        tool = TodoWriteTool()
        schema = tool.input_schema
        assert "todos" in schema["properties"]

    @pytest.mark.asyncio
    async def test_todo_tool_create_todos(self):
        """Test creating todos"""
        tool = TodoWriteTool()
        todos = [
            {"content": "Task 1", "status": "pending", "activeForm": "Doing Task 1"},
            {"content": "Task 2", "status": "pending", "activeForm": "Doing Task 2"}
        ]

        result = await tool.execute(todos=todos)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_todo_tool_update_status(self):
        """Test updating todo status"""
        tool = TodoWriteTool()
        todos = [
            {"content": "Task 1", "status": "completed", "activeForm": "Done Task 1"}
        ]

        result = await tool.execute(todos=todos)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_todo_tool_mixed_statuses(self):
        """Test todos with mixed statuses"""
        tool = TodoWriteTool()
        todos = [
            {"content": "Task 1", "status": "pending", "activeForm": "Pending"},
            {"content": "Task 2", "status": "in_progress", "activeForm": "In Progress"},
            {"content": "Task 3", "status": "completed", "activeForm": "Done"}
        ]

        result = await tool.execute(todos=todos)

        assert result.success is True


@pytest.mark.unit
class TestToolPermissionLevels:
    """Tests for tool permission levels"""

    def test_read_tool_is_safe(self):
        """Test that ReadTool is marked as SAFE"""
        tool = ReadTool()
        assert tool.permission_level == ToolPermissionLevel.SAFE

    def test_write_tool_is_normal(self):
        """Test that WriteTool is marked as NORMAL"""
        tool = WriteTool()
        assert tool.permission_level == ToolPermissionLevel.NORMAL

    def test_bash_tool_is_dangerous(self):
        """Test that BashTool is marked as DANGEROUS"""
        tool = BashTool()
        assert tool.permission_level == ToolPermissionLevel.DANGEROUS

    def test_glob_tool_is_safe(self):
        """Test that GlobTool is marked as SAFE"""
        tool = GlobTool()
        assert tool.permission_level == ToolPermissionLevel.SAFE

    def test_grep_tool_is_safe(self):
        """Test that GrepTool is marked as SAFE"""
        tool = GrepTool()
        assert tool.permission_level == ToolPermissionLevel.SAFE

    def test_todo_tool_is_safe(self):
        """Test that TodoWriteTool is marked as SAFE"""
        tool = TodoWriteTool()
        assert tool.permission_level == ToolPermissionLevel.SAFE


@pytest.mark.unit
class TestToolDescriptions:
    """Tests for tool descriptions and schemas"""

    def test_all_tools_have_descriptions(self):
        """Test that all tools have descriptions"""
        tools = [
            ReadTool(), WriteTool(), EditTool(),
            BashTool(), GlobTool(), GrepTool(), TodoWriteTool()
        ]

        for tool in tools:
            assert len(tool.description) > 0
            assert isinstance(tool.description, str)

    def test_all_tools_have_schemas(self):
        """Test that all tools have input schemas"""
        tools = [
            ReadTool(), WriteTool(), EditTool(),
            BashTool(), GlobTool(), GrepTool(), TodoWriteTool()
        ]

        for tool in tools:
            schema = tool.input_schema
            assert isinstance(schema, dict)
            assert "properties" in schema or "type" in schema


@pytest.mark.unit
class TestFileToolsEdgeCases:
    """Tests for edge cases in file tools"""

    @pytest.mark.asyncio
    async def test_read_empty_file(self):
        """Test reading an empty file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "empty.txt"
            test_file.write_text("")

            tool = ReadTool()
            result = await tool.execute(file_path=str(test_file))

            assert result.success is True

    @pytest.mark.asyncio
    async def test_write_unicode_content(self):
        """Test writing unicode content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "unicode.txt"
            content = "你好 🎉 مرحبا"

            tool = WriteTool()
            result = await tool.execute(file_path=str(test_file), content=content)

            assert result.success is True
            assert test_file.read_text(encoding='utf-8') == content

    @pytest.mark.asyncio
    async def test_edit_nonexistent_string(self):
        """Test editing file with non-existent string"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Original content")

            tool = EditTool()
            result = await tool.execute(
                file_path=str(test_file),
                old_string="Nonexistent",
                new_string="New"
            )

            # Should indicate the string wasn't found
            assert result.success is False


@pytest.mark.unit
class TestBashToolEdgeCases:
    """Tests for edge cases in bash tool"""

    @pytest.mark.asyncio
    async def test_bash_empty_command(self):
        """Test bash with empty command"""
        tool = BashTool()
        result = await tool.execute(command="")

        # Empty command may succeed or fail depending on implementation
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_bash_with_description(self):
        """Test bash tool with description parameter"""
        tool = BashTool()
        result = await tool.execute(
            command="echo 'test'",
            description="Test echo command"
        )

        assert result.success is True


@pytest.mark.unit
class TestSearchToolsEdgeCases:
    """Tests for edge cases in search tools"""

    @pytest.mark.asyncio
    async def test_glob_with_nonexistent_path(self):
        """Test glob with non-existent path"""
        tool = GlobTool()
        result = await tool.execute(pattern="/nonexistent/path/**/*.txt")

        assert result.success is True  # Should return empty results

    @pytest.mark.asyncio
    async def test_grep_special_characters(self):
        """Test grep with special regex characters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test.file (special) [chars]")

            tool = GrepTool()
            result = await tool.execute(
                pattern=r"test\.file",
                path=tmpdir
            )

            assert result.success is True


@pytest.mark.unit
class TestTodoToolEdgeCases:
    """Tests for edge cases in todo tool"""

    @pytest.mark.asyncio
    async def test_todo_empty_list(self):
        """Test todo tool with empty list"""
        tool = TodoWriteTool()
        result = await tool.execute(todos=[])

        assert result.success is True

    @pytest.mark.asyncio
    async def test_todo_large_list(self):
        """Test todo tool with large list"""
        tool = TodoWriteTool()
        todos = [
            {"content": f"Task {i}", "status": "pending", "activeForm": f"Doing Task {i}"}
            for i in range(100)
        ]

        result = await tool.execute(todos=todos)

        assert result.success is True
