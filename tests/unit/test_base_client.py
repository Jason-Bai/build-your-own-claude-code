"""
Unit tests for Base Client utilities

Tests response normalization, text extraction, and safe response creation.
"""

import pytest
from unittest.mock import Mock
from src.clients.base import BaseClient, ModelResponse


# Helper client for testing abstract methods
class TestClient(BaseClient):
    async def create_message(self, **kwargs):
        pass
    async def generate_summary(self, prompt):
        pass
    @property
    def model_name(self):
        return "test"
    @property
    def context_window(self):
        return 8000
    @property
    def provider_name(self):
        return "test"


@pytest.fixture
def client():
    """Provides a TestClient instance for tests."""
    return TestClient()


@pytest.mark.unit
class TestNormalizeFinishReason:
    """Tests for finish_reason normalization"""

    @pytest.mark.parametrize("raw_reason, normalized_reason", [
        # Standard cases from mapping
        ("STOP", "end_turn"),
        ("END_TURN", "end_turn"),
        ("MAX_TOKENS", "max_tokens"),
        ("SAFETY", "stop_sequence"),
        ("RECITATION", "stop_sequence"),
        ("OTHER", "stop_sequence"),
        ("TOOL_CALLS", "tool_use"),
        ("UNSPECIFIED", "end_turn"),
        # Case-insensitivity
        ("stop", "end_turn"),
        ("max_tokens", "max_tokens"),
        # Unknown reason
        ("UNKNOWN_REASON", "end_turn"),
        # None reason
        (None, "end_turn"),
    ])
    def test_normalize_finish_reason(self, client, raw_reason, normalized_reason):
        """Test various finish_reason normalizations"""
        assert client._normalize_finish_reason(raw_reason) == normalized_reason

    def test_normalize_finish_reason_enum_object(self, client):
        """Test finish_reason with enum-like object"""
        mock_enum = Mock()
        mock_enum.name = "TOOL_CALLS"
        assert client._normalize_finish_reason(mock_enum) == "tool_use"


@pytest.mark.unit
class TestExtractTextContent:
    """Tests for text content extraction"""

    def test_extract_text_from_text_attribute(self, client):
        """Test extracting text from .text attribute"""
        mock_obj = Mock()
        mock_obj.text = "Hello world"
        result = client._extract_text_content(mock_obj)
        assert result == "Hello world"

    def test_extract_text_from_candidates(self, client):
        """Test extracting text from candidates structure"""
        mock_part = Mock(text="Content from candidate")
        mock_content = Mock(parts=[mock_part])
        mock_candidate = Mock(content=mock_content)
        mock_obj = Mock(candidates=[mock_candidate], text=None)
        result = client._extract_text_content(mock_obj)
        assert result == "Content from candidate"

    def test_extract_text_multiple_parts(self, client):
        """Test extracting text from multiple parts"""
        mock_part1 = Mock(text="Part 1")
        mock_part2 = Mock(text="Part 2")
        mock_content = Mock(parts=[mock_part1, mock_part2])
        mock_candidate = Mock(content=mock_content)
        mock_obj = Mock(candidates=[mock_candidate], text=None)
        result = client._extract_text_content(mock_obj)
        assert result == "Part 1 Part 2"

    def test_extract_text_no_content(self, client):
        """Test when no content available"""
        mock_obj = Mock(text=None, candidates=None)
        result = client._extract_text_content(mock_obj)
        assert result is None

    def test_extract_text_empty_text(self, client):
        """Test with empty text attribute"""
        mock_obj = Mock(text="")
        result = client._extract_text_content(mock_obj)
        assert result is None


@pytest.mark.unit
class TestSafeCreateResponse:
    """Tests for safe response creation"""

    def test_safe_create_response_with_content(self, client):
        """Test creating response with content"""
        content = [{"type": "text", "text": "Response"}]
        response = client._safe_create_response(
            content=content,
            stop_reason="end_turn",
            usage={"input_tokens": 10, "output_tokens": 5},
            model="claude"
        )
        assert response.content == content
        assert response.stop_reason == "end_turn"

    def test_safe_create_response_with_fallback(self, client):
        """Test creating response with fallback text"""
        response = client._safe_create_response(
            content=[],
            stop_reason="end_turn",
            usage={"input_tokens": 0, "output_tokens": 0},
            model="claude",
            fallback_text="Fallback response"
        )
        assert len(response.content) == 1
        assert response.content[0]["text"] == "Fallback response"

    def test_safe_create_response_empty_content_no_fallback(self, client):
        """Test creating response with empty content and no fallback"""
        response = client._safe_create_response(
            content=[],
            stop_reason="end_turn",
            usage={"input_tokens": 0, "output_tokens": 0},
            model="claude"
        )
        assert len(response.content) == 1
        assert response.content[0]["text"] == ""

    def test_safe_create_response_none_usage(self, client):
        """Test creating response with None usage"""
        response = client._safe_create_response(
            content=[{"type": "text", "text": "Response"}],
            stop_reason="end_turn",
            usage=None,
            model="claude"
        )
        assert response.usage == {"input_tokens": 0, "output_tokens": 0}
