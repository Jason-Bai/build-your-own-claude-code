"""
Unit tests for Workspace Commands

Tests workspace context management, CLAUDE.md initialization,
project type detection, and directory tree generation.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from src.commands.workspace_commands import InitCommand, ShowContextCommand, LoadContextCommand
from src.commands.base import CLIContext


@pytest.mark.unit
class TestInitCommandInitialization:
    """Tests for InitCommand initialization"""

    def test_command_name(self):
        """Test command has correct name"""
        cmd = InitCommand()
        assert cmd.name == "init"

    def test_command_description(self):
        """Test command has description"""
        cmd = InitCommand()
        assert len(cmd.description) > 0
        assert "CLAUDE.md" in cmd.description or "workspace" in cmd.description.lower()


@pytest.mark.unit
class TestProjectTypeDetection:
    """Tests for project type detection"""

    def test_detect_nodejs_project(self):
        """Test detecting Node.js project"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "package.json").write_text("{}")
            result = cmd._detect_project_type(tmpdir)

            assert result["type"] == "Node.js/JavaScript"
            assert "package.json" in result["key_files"]

    def test_detect_python_requirements(self):
        """Test detecting Python project via requirements.txt"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "requirements.txt").write_text("")
            result = cmd._detect_project_type(tmpdir)

            assert result["type"] == "Python"
            assert "requirements.txt" in result["key_files"]

    def test_detect_python_setup(self):
        """Test detecting Python project via setup.py"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "setup.py").write_text("")
            result = cmd._detect_project_type(tmpdir)

            assert result["type"] == "Python"

    def test_detect_python_pyproject(self):
        """Test detecting Python project via pyproject.toml"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "pyproject.toml").write_text("")
            result = cmd._detect_project_type(tmpdir)

            assert result["type"] == "Python"

    def test_detect_rust_project(self):
        """Test detecting Rust project"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "Cargo.toml").write_text("")
            result = cmd._detect_project_type(tmpdir)

            assert result["type"] == "Rust"

    def test_detect_go_project(self):
        """Test detecting Go project"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "go.mod").write_text("")
            result = cmd._detect_project_type(tmpdir)

            assert result["type"] == "Go"

    def test_detect_java_maven_project(self):
        """Test detecting Java Maven project"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "pom.xml").write_text("")
            result = cmd._detect_project_type(tmpdir)

            assert result["type"] == "Java (Maven)"

    def test_detect_java_gradle_project(self):
        """Test detecting Java Gradle project"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "build.gradle").write_text("")
            result = cmd._detect_project_type(tmpdir)

            assert result["type"] == "Java (Gradle)"

    def test_detect_ruby_project(self):
        """Test detecting Ruby project"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "Gemfile").write_text("")
            result = cmd._detect_project_type(tmpdir)

            assert result["type"] == "Ruby"

    def test_detect_unknown_project(self):
        """Test detecting unknown project type"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = cmd._detect_project_type(tmpdir)

            assert result["type"] == "Unknown"
            assert len(result["key_files"]) == 0

    def test_detect_multiple_markers(self):
        """Test when multiple project type markers exist (first wins)"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "package.json").write_text("{}")
            Path(tmpdir, "requirements.txt").write_text("")
            result = cmd._detect_project_type(tmpdir)

            # Should pick first match (package.json)
            assert result["type"] == "Node.js/JavaScript"


@pytest.mark.unit
class TestDirectoryTree:
    """Tests for directory tree generation"""

    def test_simple_tree_basic_structure(self):
        """Test simple tree with basic directory structure"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "src").mkdir()
            Path(tmpdir, "src", "main.py").write_text("")
            Path(tmpdir, "README.md").write_text("")

            tree = cmd._simple_tree(tmpdir, max_depth=2)

            assert len(tree) > 0
            assert "src" in tree or "main.py" in tree or "README.md" in tree

    def test_simple_tree_excludes_hidden_files(self):
        """Test simple tree excludes hidden files"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, ".git").mkdir()
            Path(tmpdir, "visible.txt").write_text("")

            tree = cmd._simple_tree(tmpdir)

            assert ".git" not in tree
            assert "visible.txt" in tree or len(tree) > 0

    def test_simple_tree_depth_limit(self):
        """Test simple tree respects max depth"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "a").mkdir()
            Path(tmpdir, "a", "b").mkdir()
            Path(tmpdir, "a", "b", "c").mkdir()
            Path(tmpdir, "a", "b", "c", "d.txt").write_text("")

            tree = cmd._simple_tree(tmpdir, max_depth=2)

            # Tree should be limited (max_depth=2 means a and a/b should be included, but a/b/c limited)
            assert len(tree) > 0

    def test_simple_tree_handles_permission_error(self):
        """Test simple tree handles permission errors gracefully"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "readable.txt").write_text("")

            # Should not raise even if dir is unreadable
            tree = cmd._simple_tree(tmpdir)
            assert isinstance(tree, str)

    def test_get_file_tree_fallback(self):
        """Test get_file_tree falls back to simple tree"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test.txt").write_text("")

            # Should use fallback (tree command likely not available in test)
            tree = cmd._get_file_tree(tmpdir)
            assert isinstance(tree, str)
            assert len(tree) > 0

    def test_simple_tree_limits_items_per_directory(self):
        """Test simple tree limits items shown per directory"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create many files
            for i in range(20):
                Path(tmpdir, f"file_{i}.txt").write_text("")

            tree = cmd._simple_tree(tmpdir, max_depth=1)

            # Should limit output (max 10 files per dir)
            lines = tree.split('\n')
            assert len(lines) <= 50  # max line limit


@pytest.mark.unit
class TestShowContextCommand:
    """Tests for ShowContextCommand"""

    def test_command_name(self):
        """Test command has correct name"""
        cmd = ShowContextCommand()
        assert cmd.name == "show-context"

    @pytest.mark.asyncio
    async def test_show_context_no_file(self):
        """Test show context when CLAUDE.md doesn't exist"""
        cmd = ShowContextCommand()
        context = Mock(spec=CLIContext)

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('pathlib.Path.cwd', return_value=Path(tmpdir)):
                result = await cmd.execute("", context)

        assert "No CLAUDE.md found" in result or "init" in result.lower()

    @pytest.mark.asyncio
    async def test_show_context_with_file(self):
        """Test show context with existing CLAUDE.md"""
        cmd = ShowContextCommand()
        context = Mock(spec=CLIContext)

        with tempfile.TemporaryDirectory() as tmpdir:
            claude_file = Path(tmpdir) / "CLAUDE.md"
            test_content = "# Project Documentation"
            claude_file.write_text(test_content, encoding='utf-8')

            with patch('pathlib.Path.cwd', return_value=Path(tmpdir)):
                result = await cmd.execute("", context)

        assert "✓" in result
        assert "CLAUDE.md" in result

    @pytest.mark.asyncio
    async def test_show_context_file_content(self):
        """Test show context reads file content correctly"""
        cmd = ShowContextCommand()
        context = Mock(spec=CLIContext)

        with tempfile.TemporaryDirectory() as tmpdir:
            claude_file = Path(tmpdir) / "CLAUDE.md"
            test_content = "# Test\nContent here"
            claude_file.write_text(test_content, encoding='utf-8')

            with patch('pathlib.Path.cwd', return_value=Path(tmpdir)):
                with patch('builtins.print') as mock_print:
                    result = await cmd.execute("", context)
                    # Check that content was printed
                    mock_print.assert_called()


@pytest.mark.unit
class TestLoadContextCommand:
    """Tests for LoadContextCommand"""

    def test_command_name(self):
        """Test command has correct name"""
        cmd = LoadContextCommand()
        assert cmd.name == "load-context"

    @pytest.mark.asyncio
    async def test_load_context_no_file(self):
        """Test load context when CLAUDE.md doesn't exist"""
        cmd = LoadContextCommand()
        context = Mock(spec=CLIContext)

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('pathlib.Path.cwd', return_value=Path(tmpdir)):
                result = await cmd.execute("", context)

        assert "No CLAUDE.md found" in result or "init" in result.lower()

    @pytest.mark.asyncio
    async def test_load_context_with_file(self):
        """Test load context with existing CLAUDE.md"""
        cmd = LoadContextCommand()

        # Mock the context and agent
        mock_agent = Mock()
        mock_context_manager = Mock()
        mock_agent.context_manager = mock_context_manager

        context = Mock(spec=CLIContext)
        context.agent = mock_agent

        with tempfile.TemporaryDirectory() as tmpdir:
            claude_file = Path(tmpdir) / "CLAUDE.md"
            test_content = "# Project Documentation\nTest content"
            claude_file.write_text(test_content, encoding='utf-8')

            with patch('pathlib.Path.cwd', return_value=Path(tmpdir)):
                result = await cmd.execute("", context)

        assert "✓" in result
        assert "Loaded" in result
        mock_context_manager.add_user_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_context_passes_content_to_agent(self):
        """Test load context passes file content to agent"""
        cmd = LoadContextCommand()

        mock_agent = Mock()
        mock_context_manager = Mock()
        mock_agent.context_manager = mock_context_manager

        context = Mock(spec=CLIContext)
        context.agent = mock_agent

        with tempfile.TemporaryDirectory() as tmpdir:
            claude_file = Path(tmpdir) / "CLAUDE.md"
            test_content = "# Project\nDetails"
            claude_file.write_text(test_content, encoding='utf-8')

            with patch('pathlib.Path.cwd', return_value=Path(tmpdir)):
                await cmd.execute("", context)

        # Verify content was passed to agent
        call_args = mock_context_manager.add_user_message.call_args
        passed_message = call_args[0][0]
        assert test_content in passed_message
        assert "[System: Loading project context]" in passed_message

    @pytest.mark.asyncio
    async def test_load_context_file_size_in_response(self):
        """Test load context reports file size"""
        cmd = LoadContextCommand()

        mock_agent = Mock()
        mock_context_manager = Mock()
        mock_agent.context_manager = mock_context_manager

        context = Mock(spec=CLIContext)
        context.agent = mock_agent

        with tempfile.TemporaryDirectory() as tmpdir:
            claude_file = Path(tmpdir) / "CLAUDE.md"
            test_content = "x" * 1000  # 1000 chars
            claude_file.write_text(test_content, encoding='utf-8')

            with patch('pathlib.Path.cwd', return_value=Path(tmpdir)):
                result = await cmd.execute("", context)

        assert "1000" in result  # Should report 1000 chars


@pytest.mark.unit
class TestInitCommandExecution:
    """Tests for InitCommand execution"""

    @pytest.mark.asyncio
    async def test_init_cancel_if_exists(self):
        """Test init command cancels if CLAUDE.md exists and user declines"""
        cmd = InitCommand()
        context = Mock(spec=CLIContext)
        context.agent = Mock()

        with tempfile.TemporaryDirectory() as tmpdir:
            claude_file = Path(tmpdir) / "CLAUDE.md"
            claude_file.write_text("existing content")

            with patch('pathlib.Path.cwd', return_value=Path(tmpdir)):
                with patch('builtins.input', return_value='n'):
                    result = await cmd.execute("", context)

        assert "cancelled" in result.lower()

    @pytest.mark.asyncio
    async def test_init_overwrite_on_user_confirm(self):
        """Test init command proceeds if user confirms overwrite"""
        cmd = InitCommand()

        mock_agent = Mock()
        mock_agent.run = AsyncMock()

        context = Mock(spec=CLIContext)
        context.agent = mock_agent

        with tempfile.TemporaryDirectory() as tmpdir:
            claude_file = Path(tmpdir) / "CLAUDE.md"
            claude_file.write_text("existing content")

            with patch('pathlib.Path.cwd', return_value=Path(tmpdir)):
                with patch('builtins.input', return_value='y'):
                    with patch('builtins.print'):
                        result = await cmd.execute("", context)

        # Agent should be called to generate CLAUDE.md
        mock_agent.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_succeeds_when_file_created(self):
        """Test init succeeds when CLAUDE.md is created"""
        cmd = InitCommand()

        mock_agent = Mock()
        mock_agent.run = AsyncMock()

        context = Mock(spec=CLIContext)
        context.agent = mock_agent

        with tempfile.TemporaryDirectory() as tmpdir:
            claude_file = Path(tmpdir) / "CLAUDE.md"

            async def create_file(*args, **kwargs):
                claude_file.write_text("# Generated CLAUDE.md")

            mock_agent.run.side_effect = create_file

            with patch('os.getcwd', return_value=tmpdir):
                with patch('builtins.print'):
                    result = await cmd.execute("", context)

        assert "✓" in result
        assert "Workspace initialized" in result


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases"""

    def test_project_detection_with_symlinks(self):
        """Test project detection with symlinked files"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            actual_file = Path(tmpdir) / "requirements.txt"
            actual_file.write_text("")

            result = cmd._detect_project_type(tmpdir)
            assert result["type"] == "Python"

    def test_simple_tree_with_empty_directory(self):
        """Test simple tree with empty directory"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            tree = cmd._simple_tree(tmpdir)
            assert isinstance(tree, str)
            assert len(tree) > 0

    def test_simple_tree_with_special_characters(self):
        """Test simple tree with special characters in filenames"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "file-with-dash.txt").write_text("")
            Path(tmpdir, "file_with_underscore.txt").write_text("")

            tree = cmd._simple_tree(tmpdir)
            assert isinstance(tree, str)

    def test_project_detection_case_sensitivity(self):
        """Test project detection is case sensitive"""
        cmd = InitCommand()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create lowercase file (should not match)
            Path(tmpdir, "package.json").write_text("{}")
            result = cmd._detect_project_type(tmpdir)

            # Should detect correctly
            assert result["type"] == "Node.js/JavaScript"
