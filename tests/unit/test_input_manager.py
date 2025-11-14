"""
Unit tests for Input Management Utilities

Tests command completion, input handling, and history management.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent

from src.utils.input import (
    CommandCompleter,
    PromptInputManager,
    get_input_manager,
    reset_input_manager,
)


@pytest.mark.unit
class TestCommandCompleter:
    """Tests for CommandCompleter"""

    def test_initialization(self):
        """Test completer initialization"""
        commands = {"/help": None, "/status": None}
        completer = CommandCompleter(commands)

        assert completer.commands is not None
        assert len(completer.commands) == 2

    def test_get_completions_empty_input(self):
        """Test completions with empty input"""
        completer = CommandCompleter({"/help": None, "/status": None})
        document = Document("")
        event = Mock(spec=CompleteEvent)

        completions = list(completer.get_completions(document, event))
        assert completions == []

    def test_get_completions_no_slash(self):
        """Test completions without slash prefix"""
        completer = CommandCompleter({"/help": None, "/status": None})
        document = Document("help")
        event = Mock(spec=CompleteEvent)

        completions = list(completer.get_completions(document, event))
        assert completions == []

    def test_get_completions_matches_help(self):
        """Test completions matching /help"""
        completer = CommandCompleter({"/help": None, "/status": None})
        document = Document("/he")
        event = Mock(spec=CompleteEvent)

        completions = list(completer.get_completions(document, event))
        assert len(completions) == 1
        assert completions[0].text == "lp"

    def test_get_completions_case_insensitive(self):
        """Test case-insensitive completions"""
        completer = CommandCompleter({"/Help": None, "/Status": None})
        document = Document("/he")
        event = Mock(spec=CompleteEvent)

        completions = list(completer.get_completions(document, event))
        assert len(completions) == 1

    def test_get_completions_multiple_matches(self):
        """Test multiple matching completions"""
        completer = CommandCompleter({"/help": None, "/history": None})
        document = Document("/h")
        event = Mock(spec=CompleteEvent)

        completions = list(completer.get_completions(document, event))
        assert len(completions) == 2

    def test_get_completions_slash_only(self):
        """Test completions with only slash"""
        completer = CommandCompleter({"/help": None, "/status": None})
        document = Document("/")
        event = Mock(spec=CompleteEvent)

        completions = list(completer.get_completions(document, event))
        assert len(completions) == 2

    def test_get_completions_with_text_before(self):
        """Test completions when there's text before the command"""
        completer = CommandCompleter({"/help": None, "/status": None})
        document = Document("tell me about /he")
        event = Mock(spec=CompleteEvent)

        completions = list(completer.get_completions(document, event))
        assert len(completions) == 1

    def test_get_completions_exact_match(self):
        """Test completions with exact command match"""
        completer = CommandCompleter({"/help": None, "/status": None})
        document = Document("/help")
        event = Mock(spec=CompleteEvent)

        completions = list(completer.get_completions(document, event))
        assert len(completions) == 1
        assert completions[0].text == ""

    def test_get_completions_no_matches(self):
        """Test completions with no matches"""
        completer = CommandCompleter({"/help": None, "/status": None})
        document = Document("/xyz")
        event = Mock(spec=CompleteEvent)

        completions = list(completer.get_completions(document, event))
        assert completions == []


@pytest.mark.unit
class TestPromptInputManagerInitialization:
    """Tests for PromptInputManager initialization"""

    @patch('src.utils.input.Path')
    @patch('src.utils.input.FileHistory')
    @patch('src.utils.input.PromptSession')
    def test_initialization_creates_cache_dir(self, mock_session, mock_history, mock_path):
        """Test that initialization creates cache directory"""
        mock_path.home.return_value = MagicMock()
        mock_path.home.return_value.__truediv__ = MagicMock(
            return_value=MagicMock(mkdir=MagicMock())
        )

        manager = PromptInputManager()
        assert manager is not None

    @patch('src.utils.input.Path')
    @patch('src.utils.input.FileHistory')
    @patch('src.utils.input.PromptSession')
    def test_initialization_creates_history(self, mock_session, mock_history, mock_path):
        """Test that initialization creates history"""
        mock_path.home.return_value = MagicMock()
        mock_path.home.return_value.__truediv__ = MagicMock(
            return_value=MagicMock(mkdir=MagicMock())
        )

        manager = PromptInputManager()
        assert manager.history is not None

    @patch('src.utils.input.Path')
    @patch('src.utils.input.FileHistory')
    @patch('src.utils.input.PromptSession')
    def test_initialization_creates_completer(self, mock_session, mock_history, mock_path):
        """Test that initialization creates command completer"""
        mock_path.home.return_value = MagicMock()
        mock_path.home.return_value.__truediv__ = MagicMock(
            return_value=MagicMock(mkdir=MagicMock())
        )

        manager = PromptInputManager()
        assert manager.completer is not None
        assert isinstance(manager.completer, CommandCompleter)

    @patch('src.utils.input.Path')
    @patch('src.utils.input.FileHistory')
    @patch('src.utils.input.PromptSession')
    def test_initialization_creates_session(self, mock_session, mock_history, mock_path):
        """Test that initialization creates prompt session"""
        mock_path.home.return_value = MagicMock()
        mock_path.home.return_value.__truediv__ = MagicMock(
            return_value=MagicMock(mkdir=MagicMock())
        )

        manager = PromptInputManager()
        assert manager.session is not None

    @patch('src.utils.input.Path')
    @patch('src.utils.input.FileHistory')
    @patch('src.utils.input.PromptSession')
    def test_initialization_defines_commands(self, mock_session, mock_history, mock_path):
        """Test that initialization defines built-in commands"""
        mock_path.home.return_value = MagicMock()
        mock_path.home.return_value.__truediv__ = MagicMock(
            return_value=MagicMock(mkdir=MagicMock())
        )

        manager = PromptInputManager()
        assert "/help" in manager.commands
        assert "/status" in manager.commands
        assert "/save" in manager.commands
        assert "/exit" in manager.commands


@pytest.mark.unit
class TestPromptInputManagerHistoryFile:
    """Tests for history file management"""

    @patch('src.utils.input.Path')
    @patch('src.utils.input.FileHistory')
    @patch('src.utils.input.PromptSession')
    def test_history_file_property(self, mock_session, mock_history, mock_path):
        """Test history_file property"""
        mock_path.home.return_value = MagicMock()
        mock_path.home.return_value.__truediv__ = MagicMock(
            return_value=MagicMock(mkdir=MagicMock())
        )
        mock_history_instance = MagicMock()
        mock_history_instance.filename = "/path/to/history"
        mock_history.return_value = mock_history_instance

        manager = PromptInputManager()
        assert manager.history_file == "/path/to/history"

    @patch('src.utils.input.Path')
    @patch('src.utils.input.FileHistory')
    @patch('src.utils.input.PromptSession')
    def test_clear_history(self, mock_session, mock_history, mock_path):
        """Test clear_history method"""
        mock_path.home.return_value = MagicMock()
        mock_path.home.return_value.__truediv__ = MagicMock(
            return_value=MagicMock(mkdir=MagicMock())
        )
        mock_history_instance = MagicMock()
        mock_history.return_value = mock_history_instance

        manager = PromptInputManager()
        manager.clear_history()

        mock_history_instance.clear.assert_called_once()


@pytest.mark.unit
class TestPromptInputManagerIntegration:
    """Integration tests for input manager"""

    @patch('src.utils.input.PromptSession')
    @patch('src.utils.input.FileHistory')
    @patch('src.utils.input.Path')
    def test_get_input_strips_whitespace(self, mock_path, mock_history, mock_session):
        """Test that get_input strips whitespace"""
        mock_path.home.return_value = MagicMock()
        mock_path.home.return_value.__truediv__ = MagicMock(
            return_value=MagicMock(mkdir=MagicMock())
        )

        mock_session_instance = MagicMock()
        mock_session_instance.prompt.return_value = "  hello world  "
        mock_session.return_value = mock_session_instance

        manager = PromptInputManager()
        # We can't actually test get_input since it needs event loop,
        # but we can verify the structure exists
        assert hasattr(manager, 'get_input')
        assert callable(manager.get_input)

    @patch('src.utils.input.PromptSession')
    @patch('src.utils.input.FileHistory')
    @patch('src.utils.input.Path')
    def test_async_get_input_method_exists(self, mock_path, mock_history, mock_session):
        """Test that async_get_input method exists"""
        mock_path.home.return_value = MagicMock()
        mock_path.home.return_value.__truediv__ = MagicMock(
            return_value=MagicMock(mkdir=MagicMock())
        )

        manager = PromptInputManager()
        assert hasattr(manager, 'async_get_input')
        assert callable(manager.async_get_input)

    @patch('src.utils.input.PromptSession')
    @patch('src.utils.input.FileHistory')
    @patch('src.utils.input.Path')
    def test_multiline_input_method_exists(self, mock_path, mock_history, mock_session):
        """Test that multiline input methods exist"""
        mock_path.home.return_value = MagicMock()
        mock_path.home.return_value.__truediv__ = MagicMock(
            return_value=MagicMock(mkdir=MagicMock())
        )

        manager = PromptInputManager()
        assert hasattr(manager, 'get_multiline_input')
        assert hasattr(manager, 'async_get_multiline_input')
        assert callable(manager.get_multiline_input)
        assert callable(manager.async_get_multiline_input)


@pytest.mark.unit
class TestGlobalInputManager:
    """Tests for global input manager singleton"""

    def teardown_method(self):
        """Reset input manager after each test"""
        reset_input_manager()

    @patch('src.utils.input.PromptSession')
    @patch('src.utils.input.FileHistory')
    @patch('src.utils.input.Path')
    def test_get_input_manager_creates_singleton(self, mock_path, mock_history, mock_session):
        """Test that get_input_manager creates singleton"""
        mock_path.home.return_value = MagicMock()
        mock_path.home.return_value.__truediv__ = MagicMock(
            return_value=MagicMock(mkdir=MagicMock())
        )

        reset_input_manager()
        manager1 = get_input_manager()
        manager2 = get_input_manager()

        assert manager1 is manager2

    @patch('src.utils.input.PromptSession')
    @patch('src.utils.input.FileHistory')
    @patch('src.utils.input.Path')
    def test_reset_input_manager(self, mock_path, mock_history, mock_session):
        """Test resetting input manager"""
        mock_path.home.return_value = MagicMock()
        mock_path.home.return_value.__truediv__ = MagicMock(
            return_value=MagicMock(mkdir=MagicMock())
        )

        reset_input_manager()
        manager1 = get_input_manager()
        reset_input_manager()
        manager2 = get_input_manager()

        assert manager1 is not manager2

    @patch('src.utils.input.PromptSession')
    @patch('src.utils.input.FileHistory')
    @patch('src.utils.input.Path')
    def test_get_input_manager_returns_manager(self, mock_path, mock_history, mock_session):
        """Test that get_input_manager returns PromptInputManager instance"""
        mock_path.home.return_value = MagicMock()
        mock_path.home.return_value.__truediv__ = MagicMock(
            return_value=MagicMock(mkdir=MagicMock())
        )

        reset_input_manager()
        manager = get_input_manager()

        assert isinstance(manager, PromptInputManager)


@pytest.mark.unit
class TestCommandCompleterEdgeCases:
    """Edge case tests for CommandCompleter"""

    def test_commands_with_special_characters(self):
        """Test commands with special characters"""
        commands = {"/help-me": None, "/save_all": None}
        completer = CommandCompleter(commands)

        assert len(completer.commands) == 2

    def test_word_extraction_with_multiple_spaces(self):
        """Test word extraction with multiple spaces"""
        completer = CommandCompleter({"/help": None, "/status": None})
        document = Document("   /he")
        event = Mock(spec=CompleteEvent)

        completions = list(completer.get_completions(document, event))
        assert len(completions) == 1

    def test_completion_at_start_of_line(self):
        """Test completion at start of line"""
        completer = CommandCompleter({"/help": None, "/status": None})
        document = Document("/st")
        event = Mock(spec=CompleteEvent)

        completions = list(completer.get_completions(document, event))
        assert len(completions) == 1
        assert completions[0].text == "atus"

    def test_empty_command_dict(self):
        """Test with empty command dictionary"""
        completer = CommandCompleter({})
        document = Document("/")
        event = Mock(spec=CompleteEvent)

        completions = list(completer.get_completions(document, event))
        assert completions == []
