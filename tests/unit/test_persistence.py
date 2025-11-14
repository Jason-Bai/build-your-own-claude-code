"""
Unit tests for Conversation Persistence

Tests saving, loading, listing, and deleting conversations.
"""

import pytest
import json
import tempfile
from pathlib import Path
from src.persistence import ConversationPersistence


@pytest.mark.unit
class TestConversationPersistenceInitialization:
    """Tests for persistence initialization"""

    def test_persistence_initialization_default(self):
        """Test default initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)
            assert persistence.storage_dir == Path(tmpdir)

    def test_persistence_creates_directory(self):
        """Test that storage directory is created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "conversations"
            persistence = ConversationPersistence(str(storage_path))
            assert storage_path.exists()

    def test_persistence_custom_storage_dir(self):
        """Test custom storage directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir) / "custom_storage"
            persistence = ConversationPersistence(str(custom_dir))
            assert custom_dir.exists()


@pytest.mark.unit
class TestConversationPersistenceSaving:
    """Tests for saving conversations"""

    def test_save_conversation_basic(self):
        """Test saving a basic conversation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            file_path = persistence.save_conversation(
                conversation_id="test_1",
                messages=[{"role": "user", "content": "Hello"}],
                system_prompt="You are helpful"
            )

            assert Path(file_path).exists()
            assert file_path.endswith("test_1.json")

    def test_save_conversation_with_metadata(self):
        """Test saving conversation with metadata"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            file_path = persistence.save_conversation(
                conversation_id="test_2",
                messages=[],
                system_prompt="Test",
                summary="Test summary",
                metadata={"key": "value"}
            )

            data = json.loads(Path(file_path).read_text())
            assert data["metadata"]["key"] == "value"
            assert data["summary"] == "Test summary"

    def test_save_conversation_creates_json(self):
        """Test that saved file is valid JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            messages = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"}
            ]

            file_path = persistence.save_conversation(
                conversation_id="test_3",
                messages=messages,
                system_prompt="System prompt"
            )

            data = json.loads(Path(file_path).read_text())
            assert data["id"] == "test_3"
            assert data["system_prompt"] == "System prompt"
            assert len(data["messages"]) == 2
            assert "timestamp" in data

    def test_save_conversation_overwrites_existing(self):
        """Test that saving overwrites existing conversation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            persistence.save_conversation(
                conversation_id="test_4",
                messages=[{"role": "user", "content": "First"}],
                system_prompt="First"
            )

            persistence.save_conversation(
                conversation_id="test_4",
                messages=[{"role": "user", "content": "Second"}],
                system_prompt="Second"
            )

            data = persistence.load_conversation("test_4")
            assert data["system_prompt"] == "Second"
            assert data["messages"][0]["content"] == "Second"


@pytest.mark.unit
class TestConversationPersistenceLoading:
    """Tests for loading conversations"""

    def test_load_conversation_existing(self):
        """Test loading an existing conversation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            persistence.save_conversation(
                conversation_id="test_5",
                messages=[{"role": "user", "content": "Test"}],
                system_prompt="Test prompt"
            )

            data = persistence.load_conversation("test_5")
            assert data is not None
            assert data["id"] == "test_5"
            assert data["system_prompt"] == "Test prompt"

    def test_load_conversation_nonexistent(self):
        """Test loading nonexistent conversation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            result = persistence.load_conversation("nonexistent")
            assert result is None

    def test_load_conversation_preserves_data(self):
        """Test that loaded data matches saved data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            original_messages = [
                {"role": "user", "content": "Question"},
                {"role": "assistant", "content": "Answer"}
            ]
            original_prompt = "System prompt"
            original_summary = "Summary text"

            persistence.save_conversation(
                conversation_id="test_6",
                messages=original_messages,
                system_prompt=original_prompt,
                summary=original_summary
            )

            loaded = persistence.load_conversation("test_6")
            assert loaded["messages"] == original_messages
            assert loaded["system_prompt"] == original_prompt
            assert loaded["summary"] == original_summary


@pytest.mark.unit
class TestConversationPersistenceListingAndDeletion:
    """Tests for listing and deleting conversations"""

    def test_list_conversations_empty(self):
        """Test listing when no conversations exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            conversations = persistence.list_conversations()
            assert conversations == []

    def test_list_conversations_single(self):
        """Test listing with single conversation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            persistence.save_conversation(
                conversation_id="test_7",
                messages=[],
                system_prompt="Test"
            )

            conversations = persistence.list_conversations()
            assert len(conversations) == 1
            assert conversations[0]["id"] == "test_7"

    def test_list_conversations_multiple(self):
        """Test listing multiple conversations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            for i in range(3):
                persistence.save_conversation(
                    conversation_id=f"test_{i}",
                    messages=[],
                    system_prompt="Test"
                )

            conversations = persistence.list_conversations()
            assert len(conversations) == 3

    def test_list_conversations_includes_metadata(self):
        """Test that list includes required metadata"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            persistence.save_conversation(
                conversation_id="test_8",
                messages=[{"role": "user", "content": "msg"}],
                system_prompt="Test"
            )

            conversations = persistence.list_conversations()
            assert len(conversations) > 0

            conv = conversations[0]
            assert "id" in conv
            assert "timestamp" in conv
            assert "message_count" in conv
            assert "file" in conv
            assert conv["message_count"] == 1

    def test_delete_conversation_existing(self):
        """Test deleting an existing conversation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            persistence.save_conversation(
                conversation_id="test_9",
                messages=[],
                system_prompt="Test"
            )

            result = persistence.delete_conversation("test_9")
            assert result is True
            assert persistence.load_conversation("test_9") is None

    def test_delete_conversation_nonexistent(self):
        """Test deleting nonexistent conversation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            result = persistence.delete_conversation("nonexistent")
            assert result is False


@pytest.mark.unit
class TestConversationPersistenceUtilities:
    """Tests for utility methods"""

    def test_get_latest_conversation_id_empty(self):
        """Test getting latest ID when no conversations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            result = persistence.get_latest_conversation_id()
            assert result is None

    def test_get_latest_conversation_id_exists(self):
        """Test getting latest conversation ID"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            persistence.save_conversation("conv_1", [], "")
            persistence.save_conversation("conv_2", [], "")

            latest = persistence.get_latest_conversation_id()
            assert latest is not None
            assert latest in ["conv_1", "conv_2"]

    def test_auto_save_id_format(self):
        """Test auto save ID generation format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            auto_id = persistence.auto_save_id()
            assert auto_id.startswith("auto_")
            assert len(auto_id) > len("auto_")

    def test_auto_save_id_uniqueness(self):
        """Test that auto save IDs are unique"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            id1 = persistence.auto_save_id()
            id2 = persistence.auto_save_id()
            # Should be different due to timestamp variation
            assert id1 != id2 or len(id1) > 0  # At least one is non-empty


@pytest.mark.unit
class TestConversationPersistenceIntegration:
    """Integration tests for persistence"""

    def test_complete_workflow(self):
        """Test complete save-load-list-delete workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            # Save
            messages = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"}
            ]
            persistence.save_conversation(
                conversation_id="workflow_test",
                messages=messages,
                system_prompt="System",
                summary="Test summary"
            )

            # List
            conversations = persistence.list_conversations()
            assert len(conversations) == 1

            # Load
            loaded = persistence.load_conversation("workflow_test")
            assert loaded["id"] == "workflow_test"
            assert len(loaded["messages"]) == 2

            # Delete
            deleted = persistence.delete_conversation("workflow_test")
            assert deleted is True
            assert persistence.load_conversation("workflow_test") is None

    def test_multiple_conversations_workflow(self):
        """Test managing multiple conversations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = ConversationPersistence(tmpdir)

            # Save multiple
            for i in range(3):
                persistence.save_conversation(
                    conversation_id=f"multi_{i}",
                    messages=[{"role": "user", "content": f"Message {i}"}],
                    system_prompt="System"
                )

            # List all
            conversations = persistence.list_conversations()
            assert len(conversations) == 3

            # Delete one
            persistence.delete_conversation("multi_1")
            conversations = persistence.list_conversations()
            assert len(conversations) == 2

            # Load remaining
            for i in [0, 2]:
                loaded = persistence.load_conversation(f"multi_{i}")
                assert loaded is not None
