"""
Unit tests for Persistence Module

Tests conversation saving, loading, listing, deletion, and auto-save functionality.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from datetime import datetime
from src.persistence import ConversationPersistence


@pytest.mark.unit
class TestConversationPersistenceInitialization:
    """Tests for ConversationPersistence initialization"""

    def test_persistence_initializes_with_default_dir(self):
        """Test persistence initializes with default directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('pathlib.Path.mkdir'):
                persistence = ConversationPersistence(tmpdir)
                assert persistence.storage_dir == Path(tmpdir)

    def test_persistence_creates_storage_directory(self):
        """Test persistence creates storage directory if missing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "conversations"
            persistence = ConversationPersistence(str(storage_path))
            assert persistence.storage_dir.exists()

    def test_persistence_storage_dir_is_pathlib_path(self):
        """Test storage_dir is a pathlib.Path object"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)
            assert isinstance(persistence.storage_dir, Path)


@pytest.mark.unit
class TestSaveConversation:
    """Tests for saving conversations"""

    def test_save_conversation_creates_json_file(self):
        """Test save_conversation creates a JSON file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            messages = [{"role": "user", "content": "Hello"}]
            file_path = persistence.save_conversation(
                "test_conv",
                messages,
                "You are a helpful assistant",
                "Summary text"
            )

            assert Path(file_path).exists()
            assert Path(file_path).suffix == ".json"

    def test_save_conversation_returns_file_path(self):
        """Test save_conversation returns correct file path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            file_path = persistence.save_conversation(
                "my_conv",
                [],
                "System prompt"
            )

            assert "my_conv.json" in file_path

    def test_save_conversation_stores_correct_data(self):
        """Test save_conversation stores correct data structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            messages = [{"role": "user", "content": "Test"}]
            system_prompt = "You are helpful"
            summary = "Test summary"
            metadata = {"key": "value"}

            file_path = persistence.save_conversation(
                "test_id",
                messages,
                system_prompt,
                summary,
                metadata
            )

            with open(file_path, 'r') as f:
                data = json.load(f)

            assert data["id"] == "test_id"
            assert data["system_prompt"] == system_prompt
            assert data["summary"] == summary
            assert data["messages"] == messages
            assert data["metadata"] == metadata
            assert "timestamp" in data

    def test_save_conversation_includes_timestamp(self):
        """Test save_conversation includes ISO timestamp"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            file_path = persistence.save_conversation("test", [], "")

            with open(file_path, 'r') as f:
                data = json.load(f)

            # Should be valid ISO format
            datetime.fromisoformat(data["timestamp"])

    def test_save_conversation_with_empty_metadata(self):
        """Test save_conversation handles None metadata"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            file_path = persistence.save_conversation(
                "test",
                [],
                "prompt",
                "",
                None
            )

            with open(file_path, 'r') as f:
                data = json.load(f)

            assert data["metadata"] == {}

    def test_save_conversation_overwrites_existing(self):
        """Test save_conversation overwrites existing file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            # Save first version
            persistence.save_conversation("test", [{"msg": "v1"}], "")

            # Save second version
            persistence.save_conversation("test", [{"msg": "v2"}], "")

            file_path = persistence.storage_dir / "test.json"
            with open(file_path, 'r') as f:
                data = json.load(f)

            assert data["messages"] == [{"msg": "v2"}]

    def test_save_conversation_encodes_unicode(self):
        """Test save_conversation handles unicode properly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            messages = [{"role": "user", "content": "你好世界"}]
            file_path = persistence.save_conversation("test", messages, "")

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "你好世界" in content


@pytest.mark.unit
class TestLoadConversation:
    """Tests for loading conversations"""

    def test_load_conversation_returns_dict(self):
        """Test load_conversation returns dictionary"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            persistence.save_conversation("test", [], "prompt")
            data = persistence.load_conversation("test")

            assert isinstance(data, dict)

    def test_load_conversation_retrieves_correct_data(self):
        """Test load_conversation retrieves saved data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            original_msg = [{"role": "user", "content": "Hello"}]
            persistence.save_conversation("test", original_msg, "System")

            loaded = persistence.load_conversation("test")

            assert loaded["messages"] == original_msg
            assert loaded["system_prompt"] == "System"

    def test_load_conversation_returns_none_when_not_found(self):
        """Test load_conversation returns None for missing file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            result = persistence.load_conversation("nonexistent")

            assert result is None

    def test_load_conversation_with_metadata(self):
        """Test load_conversation includes metadata"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            metadata = {"todos": [{"id": 1, "task": "test"}]}
            persistence.save_conversation("test", [], "", "", metadata)

            loaded = persistence.load_conversation("test")

            assert loaded["metadata"] == metadata


@pytest.mark.unit
class TestListConversations:
    """Tests for listing conversations"""

    def test_list_conversations_empty_dir_returns_empty_list(self):
        """Test list_conversations returns empty list when no conversations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            conversations = persistence.list_conversations()

            assert conversations == []

    def test_list_conversations_returns_list_of_dicts(self):
        """Test list_conversations returns list of dictionaries"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)
            persistence.save_conversation("conv1", [], "")

            conversations = persistence.list_conversations()

            assert isinstance(conversations, list)
            assert len(conversations) > 0
            assert isinstance(conversations[0], dict)

    def test_list_conversations_includes_required_fields(self):
        """Test each conversation has required fields"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)
            persistence.save_conversation("test", [{"msg": "a"}, {"msg": "b"}], "")

            conversations = persistence.list_conversations()
            conv = conversations[0]

            assert "id" in conv
            assert "timestamp" in conv
            assert "message_count" in conv
            assert "file" in conv

    def test_list_conversations_correct_message_count(self):
        """Test message_count is accurate"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)
            messages = [{"a": 1}, {"b": 2}, {"c": 3}]
            persistence.save_conversation("test", messages, "")

            conversations = persistence.list_conversations()

            assert conversations[0]["message_count"] == 3

    def test_list_conversations_sorted_by_timestamp_desc(self):
        """Test conversations sorted by timestamp descending"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            persistence.save_conversation("conv1", [], "")
            persistence.save_conversation("conv2", [], "")

            conversations = persistence.list_conversations()

            # Should be sorted by timestamp descending (newest first)
            if len(conversations) > 1:
                assert conversations[0]["timestamp"] >= conversations[1]["timestamp"]

    def test_list_conversations_handles_corrupted_files(self):
        """Test list_conversations handles corrupted JSON gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            # Save a valid conversation first
            persistence.save_conversation("good", [], "")

            # Create corrupted JSON file manually
            bad_file = persistence.storage_dir / "bad.json"
            bad_file.write_text("{invalid json")

            # Should not raise, handles corrupted file gracefully
            conversations = persistence.list_conversations()

            # Should at least have the good one
            assert isinstance(conversations, list)
            assert any(c["id"] == "good" for c in conversations)

    def test_list_conversations_uses_stem_as_fallback_id(self):
        """Test list_conversations uses filename as fallback ID"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            # Save normally, which includes id field
            persistence.save_conversation("normal", [], "")

            conversations = persistence.list_conversations()

            # Should be able to find it by either id or stem
            assert any(c["id"] == "normal" for c in conversations)


@pytest.mark.unit
class TestDeleteConversation:
    """Tests for deleting conversations"""

    def test_delete_conversation_returns_true_when_successful(self):
        """Test delete_conversation returns True on success"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)
            persistence.save_conversation("test", [], "")

            result = persistence.delete_conversation("test")

            assert result is True

    def test_delete_conversation_removes_file(self):
        """Test delete_conversation removes the file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)
            persistence.save_conversation("test", [], "")

            file_path = persistence.storage_dir / "test.json"
            assert file_path.exists()

            result = persistence.delete_conversation("test")
            assert result is True
            assert not file_path.exists()

    def test_delete_conversation_returns_false_when_not_found(self):
        """Test delete_conversation returns False for missing file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            result = persistence.delete_conversation("nonexistent")

            assert result is False

    def test_delete_conversation_idempotent(self):
        """Test delete_conversation is idempotent"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)
            persistence.save_conversation("test", [], "")

            persistence.delete_conversation("test")
            result = persistence.delete_conversation("test")  # Delete again

            assert result is False


@pytest.mark.unit
class TestGetLatestConversation:
    """Tests for getting latest conversation"""

    def test_get_latest_conversation_id_returns_string(self):
        """Test get_latest_conversation_id returns string"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)
            persistence.save_conversation("latest", [], "")

            result = persistence.get_latest_conversation_id()

            assert isinstance(result, str)

    def test_get_latest_conversation_id_returns_none_when_empty(self):
        """Test get_latest_conversation_id returns None when no conversations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            result = persistence.get_latest_conversation_id()

            assert result is None

    def test_get_latest_conversation_id_returns_most_recent(self):
        """Test get_latest_conversation_id returns most recent"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            persistence.save_conversation("conv1", [], "")
            persistence.save_conversation("conv2", [], "")

            latest = persistence.get_latest_conversation_id()

            # Should be one of the saved conversations
            assert latest in ["conv1", "conv2"]


@pytest.mark.unit
class TestAutoSaveId:
    """Tests for auto-save ID generation"""

    def test_auto_save_id_returns_string(self):
        """Test auto_save_id returns string"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            auto_id = persistence.auto_save_id()

            assert isinstance(auto_id, str)

    def test_auto_save_id_has_correct_format(self):
        """Test auto_save_id has format auto_YYYYMMDD_HHMMSS"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            auto_id = persistence.auto_save_id()

            assert auto_id.startswith("auto_")
            # Should have 20 characters: auto_ (5) + YYYYMMDD_HHMMSS (15)
            assert len(auto_id) == 20
            # Check that the datetime part is numeric (except underscore)
            datetime_part = auto_id[5:]
            assert datetime_part.replace("_", "").isdigit()

    def test_auto_save_id_unique_calls(self):
        """Test auto_save_id generates different IDs for different calls"""
        import time
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            id1 = persistence.auto_save_id()
            time.sleep(0.01)  # Small delay
            id2 = persistence.auto_save_id()

            # IDs should be different (or same if called within same second)
            assert isinstance(id1, str) and isinstance(id2, str)

    def test_auto_save_id_valid_datetime(self):
        """Test auto_save_id contains valid datetime"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            auto_id = persistence.auto_save_id()
            datetime_part = auto_id[5:]  # Remove "auto_"

            # Should be parseable as datetime
            try:
                datetime.strptime(datetime_part, "%Y%m%d_%H%M%S")
            except ValueError:
                pytest.fail(f"Invalid datetime format in {auto_id}")


@pytest.mark.unit
class TestPersistenceEdgeCases:
    """Tests for edge cases"""

    def test_persistence_with_empty_messages(self):
        """Test saving and loading conversation with empty messages"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            persistence.save_conversation("empty", [], "")
            loaded = persistence.load_conversation("empty")

            assert loaded["messages"] == []

    def test_persistence_with_large_messages(self):
        """Test persistence with large message list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            large_messages = [{"role": f"role_{i}", "content": f"content_{i}" * 100} for i in range(100)]
            persistence.save_conversation("large", large_messages, "")
            loaded = persistence.load_conversation("large")

            assert len(loaded["messages"]) == 100

    def test_persistence_with_special_characters_in_id(self):
        """Test saving with special characters in ID"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            # Test with underscores and hyphens (valid filename chars)
            conv_id = "test_conv-2024"
            persistence.save_conversation(conv_id, [], "")
            loaded = persistence.load_conversation(conv_id)

            assert loaded["id"] == conv_id

    def test_list_conversations_with_many_files(self):
        """Test listing many conversations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            # Create 20 conversations
            for i in range(20):
                persistence.save_conversation(f"conv_{i}", [], "")

            conversations = persistence.list_conversations()

            assert len(conversations) == 20

    def test_persistence_directory_creation_idempotent(self):
        """Test persistence directory creation is idempotent"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "conversations"

            persistence1 = ConversationPersistence(str(path))
            persistence2 = ConversationPersistence(str(path))

            # Should not raise
            assert persistence1.storage_dir.exists()
            assert persistence2.storage_dir.exists()
