"""
Unit tests for Base Client utilities

Tests response normalization, text extraction, and safe response creation.
"""

import pytest
from unittest.mock import Mock
from src.clients.base import BaseClient, ModelResponse, StreamChunk


@pytest.mark.unit
class TestModelResponse:
    """Tests for ModelResponse dataclass"""

    def test_model_response_creation(self):
        """Test ModelResponse creation"""
        response = ModelResponse(
            content=[{"type": "text", "text": "Hello"}],
            stop_reason="end_turn",
            usage={"input_tokens": 10, "output_tokens": 5},
            model="claude-3.5-sonnet"
        )
        assert response.content == [{"type": "text", "text": "Hello"}]
        assert response.stop_reason == "end_turn"
        assert response.usage["input_tokens"] == 10
        assert response.model == "claude-3.5-sonnet"

    def test_model_response_with_tool_use(self):
        """Test ModelResponse with tool_use content"""
        response = ModelResponse(
            content=[
                {"type": "text", "text": "Using tool"},
                {"type": "tool_use", "id": "123", "name": "bash", "input": {}}
            ],
            stop_reason="tool_use",
            usage={"input_tokens": 20, "output_tokens": 10},
            model="claude"
        )
        assert len(response.content) == 2
        assert response.content[1]["type"] == "tool_use"

    def test_model_response_with_empty_content(self):
        """Test ModelResponse with empty content"""
        response = ModelResponse(
            content=[],
            stop_reason="end_turn",
            usage={"input_tokens": 5, "output_tokens": 0},
            model="claude"
        )
        assert response.content == []


@pytest.mark.unit
class TestStreamChunk:
    """Tests for StreamChunk dataclass"""

    def test_stream_chunk_text_creation(self):
        """Test StreamChunk for text"""
        chunk = StreamChunk(type="text", content="Hello")
        assert chunk.type == "text"
        assert chunk.content == "Hello"

    def test_stream_chunk_tool_use_creation(self):
        """Test StreamChunk for tool_use"""
        chunk = StreamChunk(type="tool_use_start", content=Mock())
        assert chunk.type == "tool_use_start"


@pytest.mark.unit
class TestNormalizeFinishReason:
    """Tests for finish_reason normalization"""

    def test_normalize_finish_reason_string(self):
        """Test normalizing string finish_reason"""
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

        client = TestClient()
        assert client._normalize_finish_reason("STOP") == "end_turn"
        assert client._normalize_finish_reason("END_TURN") == "end_turn"
        assert client._normalize_finish_reason("MAX_TOKENS") == "max_tokens"

    def test_normalize_finish_reason_case_insensitive(self):
        """Test case-insensitive normalization"""
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

        client = TestClient()
        assert client._normalize_finish_reason("stop") == "end_turn"
        assert client._normalize_finish_reason("max_tokens") == "max_tokens"

    def test_normalize_finish_reason_tool_calls(self):
        """Test TOOL_CALLS finish_reason"""
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

        client = TestClient()
        assert client._normalize_finish_reason("TOOL_CALLS") == "tool_use"

    def test_normalize_finish_reason_safety(self):
        """Test SAFETY finish_reason"""
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

        client = TestClient()
        assert client._normalize_finish_reason("SAFETY") == "stop_sequence"

    def test_normalize_finish_reason_unknown(self):
        """Test unknown finish_reason defaults to end_turn"""
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

        client = TestClient()
        assert client._normalize_finish_reason("UNKNOWN") == "end_turn"

    def test_normalize_finish_reason_none(self):
        """Test None finish_reason"""
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

        client = TestClient()
        assert client._normalize_finish_reason(None) == "end_turn"

    def test_normalize_finish_reason_enum_object(self):
        """Test finish_reason with enum-like object"""
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

        client = TestClient()
        mock_enum = Mock()
        mock_enum.name = "TOOL_CALLS"
        assert client._normalize_finish_reason(mock_enum) == "tool_use"


@pytest.mark.unit
class TestExtractTextContent:
    """Tests for text content extraction"""

    def test_extract_text_from_text_attribute(self):
        """Test extracting text from .text attribute"""
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

        client = TestClient()
        mock_obj = Mock()
        mock_obj.text = "Hello world"

        result = client._extract_text_content(mock_obj)
        assert result == "Hello world"

    def test_extract_text_from_candidates(self):
        """Test extracting text from candidates structure"""
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

        client = TestClient()

        # Create mock structure: candidates[0].content.parts[0].text
        mock_part = Mock()
        mock_part.text = "Content from candidate"

        mock_content = Mock()
        mock_content.parts = [mock_part]

        mock_candidate = Mock()
        mock_candidate.content = mock_content

        mock_obj = Mock()
        mock_obj.candidates = [mock_candidate]
        mock_obj.text = None  # No direct text attribute

        result = client._extract_text_content(mock_obj)
        assert result == "Content from candidate"

    def test_extract_text_multiple_parts(self):
        """Test extracting text from multiple parts"""
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

        client = TestClient()

        mock_part1 = Mock()
        mock_part1.text = "Part 1"

        mock_part2 = Mock()
        mock_part2.text = "Part 2"

        mock_content = Mock()
        mock_content.parts = [mock_part1, mock_part2]

        mock_candidate = Mock()
        mock_candidate.content = mock_content

        mock_obj = Mock()
        mock_obj.candidates = [mock_candidate]
        mock_obj.text = None

        result = client._extract_text_content(mock_obj)
        assert result == "Part 1 Part 2"

    def test_extract_text_no_content(self):
        """Test when no content available"""
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

        client = TestClient()

        mock_obj = Mock()
        mock_obj.text = None
        mock_obj.candidates = None

        result = client._extract_text_content(mock_obj)
        assert result is None

    def test_extract_text_empty_text(self):
        """Test with empty text attribute"""
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

        client = TestClient()

        mock_obj = Mock()
        mock_obj.text = ""

        result = client._extract_text_content(mock_obj)
        assert result is None


@pytest.mark.unit
class TestSafeCreateResponse:
    """Tests for safe response creation"""

    def test_safe_create_response_with_content(self):
        """Test creating response with content"""
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

        client = TestClient()

        content = [{"type": "text", "text": "Response"}]
        response = client._safe_create_response(
            content=content,
            stop_reason="end_turn",
            usage={"input_tokens": 10, "output_tokens": 5},
            model="claude"
        )

        assert response.content == content
        assert response.stop_reason == "end_turn"

    def test_safe_create_response_with_fallback(self):
        """Test creating response with fallback text"""
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

        client = TestClient()

        response = client._safe_create_response(
            content=[],
            stop_reason="end_turn",
            usage={"input_tokens": 0, "output_tokens": 0},
            model="claude",
            fallback_text="Fallback response"
        )

        assert len(response.content) == 1
        assert response.content[0]["text"] == "Fallback response"

    def test_safe_create_response_empty_content_no_fallback(self):
        """Test creating response with empty content and no fallback"""
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

        client = TestClient()

        response = client._safe_create_response(
            content=[],
            stop_reason="end_turn",
            usage={"input_tokens": 0, "output_tokens": 0},
            model="claude"
        )

        assert len(response.content) == 1
        assert response.content[0]["text"] == ""

    def test_safe_create_response_none_usage(self):
        """Test creating response with None usage"""
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

        client = TestClient()

        response = client._safe_create_response(
            content=[{"type": "text", "text": "Response"}],
            stop_reason="end_turn",
            usage=None,
            model="claude"
        )

        assert response.usage == {"input_tokens": 0, "output_tokens": 0}


@pytest.mark.unit
class TestFinishReasonMapping:
    """Tests for finish_reason mapping"""

    def test_finish_reason_mapping_coverage(self):
        """Test all mappings in FINISH_REASON_MAPPING"""
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

        client = TestClient()

        # Test all mappings
        assert client._normalize_finish_reason("STOP") == "end_turn"
        assert client._normalize_finish_reason("END_TURN") == "end_turn"
        assert client._normalize_finish_reason("MAX_TOKENS") == "max_tokens"
        assert client._normalize_finish_reason("SAFETY") == "stop_sequence"
        assert client._normalize_finish_reason("RECITATION") == "stop_sequence"
        assert client._normalize_finish_reason("OTHER") == "stop_sequence"
        assert client._normalize_finish_reason("TOOL_CALLS") == "tool_use"
        assert client._normalize_finish_reason("UNSPECIFIED") == "end_turn"
