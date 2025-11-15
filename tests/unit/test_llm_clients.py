"""
Unit tests for LLM Clients module

Tests the client implementations (Anthropic, OpenAI) and factory,
including message creation, streaming, and provider management.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from src.clients.base import BaseClient, ModelResponse, StreamChunk
from src.clients.anthropic import AnthropicClient
from src.clients.factory import create_client, check_provider_available


@pytest.mark.unit
class TestModelResponse:
    """Tests for ModelResponse dataclass"""

    def test_model_response_creation(self):
        """Test creating a ModelResponse"""
        response = ModelResponse(
            content=[{"type": "text", "text": "Hello"}],
            stop_reason="end_turn",
            usage={"input_tokens": 10, "output_tokens": 20},
            model="claude-3-sonnet"
        )
        assert response.content[0]["text"] == "Hello"
        assert response.stop_reason == "end_turn"
        assert response.usage["input_tokens"] == 10
        assert response.model == "claude-3-sonnet"

    def test_model_response_with_tool_use(self):
        """Test ModelResponse with tool use content"""
        response = ModelResponse(
            content=[
                {"type": "text", "text": "I'll use a tool"},
                {"type": "tool_use", "id": "123", "name": "read", "input": {"path": "/tmp/file"}}
            ],
            stop_reason="tool_use",
            usage={"input_tokens": 50, "output_tokens": 30},
            model="claude-3-sonnet"
        )
        assert len(response.content) == 2
        assert response.content[1]["type"] == "tool_use"
        assert response.stop_reason == "tool_use"

    def test_model_response_zero_tokens(self):
        """Test ModelResponse with zero tokens"""
        response = ModelResponse(
            content=[],
            stop_reason="max_tokens",
            usage={"input_tokens": 0, "output_tokens": 0},
            model="test"
        )
        assert response.usage["input_tokens"] == 0


@pytest.mark.unit
class TestStreamChunk:
    """Tests for StreamChunk dataclass"""

    def test_stream_chunk_text(self):
        """Test creating a text StreamChunk"""
        chunk = StreamChunk("text", "Hello world")
        assert chunk.type == "text"
        assert chunk.content == "Hello world"

    def test_stream_chunk_tool_use(self):
        """Test creating a tool_use StreamChunk"""
        tool_data = {"id": "123", "name": "read"}
        chunk = StreamChunk("tool_use", tool_data)
        assert chunk.type == "tool_use"
        assert chunk.content == tool_data


@pytest.mark.unit
class TestAnthropicClientInitialization:
    """Tests for AnthropicClient initialization"""

    def test_anthropic_initialization_with_api_key(self):
        """Test initializing Anthropic client with API key"""
        client = AnthropicClient(api_key="test-key")
        assert client.model == "claude-sonnet-4-5-20250929"
        assert client.default_temperature is None
        assert client.default_max_tokens is None

    def test_anthropic_initialization_with_custom_model(self):
        """Test initializing with custom model"""
        client = AnthropicClient(api_key="test-key", model="claude-opus")
        assert client.model == "claude-opus"

    def test_anthropic_initialization_with_temperature(self):
        """Test initializing with temperature"""
        client = AnthropicClient(api_key="test-key", temperature=0.5)
        assert client.default_temperature == 0.5

    def test_anthropic_initialization_with_max_tokens(self):
        """Test initializing with max_tokens"""
        client = AnthropicClient(api_key="test-key", max_tokens=4000)
        assert client.default_max_tokens == 4000

    def test_anthropic_initialization_with_api_base(self):
        """Test initializing with custom API base URL"""
        client = AnthropicClient(api_key="test-key", api_base="https://custom-api.example.com")
        assert client.client is not None

    def test_anthropic_full_initialization(self):
        """Test initializing with all parameters"""
        client = AnthropicClient(
            api_key="test-key",
            model="claude-opus",
            temperature=0.7,
            max_tokens=5000,
            api_base="https://api.example.com"
        )
        assert client.model == "claude-opus"
        assert client.default_temperature == 0.7
        assert client.default_max_tokens == 5000


@pytest.mark.unit
class TestAnthropicClientProperties:
    """Tests for AnthropicClient properties"""

    def test_model_name_property(self):
        """Test model_name property"""
        client = AnthropicClient(api_key="test-key", model="claude-opus")
        assert client.model_name == "claude-opus"

    def test_context_window_property(self):
        """Test context_window property"""
        client = AnthropicClient(api_key="test-key")
        assert client.context_window == 200000

    def test_model_name_with_default(self):
        """Test model_name with default model"""
        client = AnthropicClient(api_key="test-key")
        assert client.model_name == "claude-sonnet-4-5-20250929"


@pytest.mark.asyncio
@pytest.mark.unit
class TestAnthropicClientMessageCreation:
    """Tests for Anthropic message creation"""

    async def test_create_message_basic(self):
        """Test basic message creation"""
        with patch('src.clients.anthropic.anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_anthropic.return_value = mock_client

            # Setup mock response
            mock_response = Mock()
            mock_response.content = [Mock(type="text", text="Hello")]
            mock_response.stop_reason = "end_turn"
            mock_response.usage = Mock(input_tokens=10, output_tokens=5)
            mock_response.model = "claude-3-sonnet"
            mock_client.messages.create.return_value = mock_response

            client = AnthropicClient(api_key="test-key")
            response = await client.create_message(
                system="You are helpful",
                messages=[{"role": "user", "content": "Hi"}],
                tools=[],
                stream=False
            )

            assert isinstance(response, ModelResponse)
            assert response.stop_reason == "end_turn"
            assert response.usage["input_tokens"] == 10

    async def test_create_message_with_tool_use(self):
        """Test message creation with tool use"""
        with patch('src.clients.anthropic.anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_anthropic.return_value = mock_client

            # Setup mock response with tool_use
            mock_tool_block = Mock()
            mock_tool_block.type = "tool_use"
            mock_tool_block.id = "123"
            mock_tool_block.name = "read_file"
            mock_tool_block.input = {"path": "/tmp/file"}

            mock_text_block = Mock()
            mock_text_block.type = "text"
            mock_text_block.text = "I'll read the file"

            mock_response = Mock()
            mock_response.content = [mock_text_block, mock_tool_block]
            mock_response.stop_reason = "tool_use"
            mock_response.usage = Mock(input_tokens=20, output_tokens=15)
            mock_response.model = "claude-3-sonnet"
            mock_client.messages.create.return_value = mock_response

            client = AnthropicClient(api_key="test-key")
            response = await client.create_message(
                system="You are helpful",
                messages=[{"role": "user", "content": "Read a file"}],
                tools=[{"name": "read_file"}],
                stream=False
            )

            assert response.stop_reason == "tool_use"
            assert len(response.content) == 2
            assert response.content[1]["type"] == "tool_use"
            assert response.content[1]["name"] == "read_file"

    async def test_create_message_uses_default_temperature(self):
        """Test that default temperature is used if set"""
        with patch('src.clients.anthropic.anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_anthropic.return_value = mock_client

            mock_response = Mock()
            mock_response.content = [Mock(type="text", text="Response")]
            mock_response.stop_reason = "end_turn"
            mock_response.usage = Mock(input_tokens=5, output_tokens=5)
            mock_response.model = "claude-3-sonnet"
            mock_client.messages.create.return_value = mock_response

            client = AnthropicClient(api_key="test-key", temperature=0.3)
            await client.create_message(
                system="",
                messages=[],
                tools=[],
                temperature=1.0  # This should be overridden
            )

            # Check that the default temperature was used
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["temperature"] == 0.3

    async def test_create_message_uses_default_max_tokens(self):
        """Test that default max_tokens is used if set"""
        with patch('src.clients.anthropic.anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_anthropic.return_value = mock_client

            mock_response = Mock()
            mock_response.content = [Mock(type="text", text="Response")]
            mock_response.stop_reason = "end_turn"
            mock_response.usage = Mock(input_tokens=5, output_tokens=5)
            mock_response.model = "claude-3-sonnet"
            mock_client.messages.create.return_value = mock_response

            client = AnthropicClient(api_key="test-key", max_tokens=2000)
            await client.create_message(
                system="",
                messages=[],
                tools=[],
                max_tokens=8000  # This should be overridden
            )

            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["max_tokens"] == 2000


@pytest.mark.asyncio
@pytest.mark.unit
class TestAnthropicClientSummary:
    """Tests for Anthropic summary generation"""

    async def test_generate_summary(self):
        """Test generating a summary"""
        with patch('src.clients.anthropic.anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_anthropic.return_value = mock_client

            mock_response = Mock()
            mock_text_block = Mock()
            mock_text_block.text = "Summary of conversation"
            mock_response.content = [mock_text_block]
            mock_client.messages.create.return_value = mock_response

            client = AnthropicClient(api_key="test-key")
            summary = await client.generate_summary("Please summarize this text")

            assert summary == "Summary of conversation"
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["max_tokens"] == 500
            assert call_kwargs["temperature"] == 0.5


@pytest.mark.unit
class TestClientFactory:
    """Tests for client factory"""

    def test_create_anthropic_client(self):
        """Test creating an Anthropic client"""
        client = create_client("anthropic", api_key="test-key")
        assert isinstance(client, AnthropicClient)

    def test_create_anthropic_with_model(self):
        """Test creating Anthropic client with custom model"""
        client = create_client("anthropic", api_key="test-key", model="claude-opus")
        assert client.model == "claude-opus"

    def test_create_client_invalid_provider(self):
        """Test creating client with invalid provider"""
        with pytest.raises(ValueError, match="Unsupported provider"):
            create_client("invalid", api_key="test-key")

    def test_provider_error_messages(self):
        """Test that provider errors have helpful messages"""
        # Test that ValueError has good error message
        try:
            create_client("nonexistent_provider", api_key="key")
        except ValueError as e:
            assert "Unsupported provider" in str(e)


@pytest.mark.unit
class TestProviderAvailability:
    """Tests for provider availability checking"""

    def test_check_anthropic_available(self):
        """Test checking if Anthropic is available"""
        # Anthropic should be installed in test environment
        available = check_provider_available("anthropic")
        assert isinstance(available, bool)

    def test_check_unavailable_provider(self):
        """Test checking unavailable provider"""
        # Use a provider that won't be installed
        available = check_provider_available("nonexistent_provider")
        assert available is False

    def test_check_all_providers(self):
        """Test checking all provider types"""
        for provider in ["anthropic", "openai"]:
            result = check_provider_available(provider)
            assert isinstance(result, bool)


@pytest.mark.unit
class TestBaseClientNormalization:
    """Tests for BaseClient finish_reason normalization"""

    def test_finish_reason_mapping_exists(self):
        """Test that FINISH_REASON_MAPPING is defined"""
        assert hasattr(BaseClient, 'FINISH_REASON_MAPPING')
        assert isinstance(BaseClient.FINISH_REASON_MAPPING, dict)

    def test_finish_reason_values(self):
        """Test common finish reason mappings"""
        mapping = BaseClient.FINISH_REASON_MAPPING
        assert mapping.get("STOP") == "end_turn"
        assert mapping.get("MAX_TOKENS") == "max_tokens"
        assert mapping.get("TOOL_CALLS") == "tool_use"


@pytest.mark.unit
class TestClientConfigurationCombinations:
    """Tests for various client configuration combinations"""

    def test_anthropic_default_config(self):
        """Test Anthropic with all defaults"""
        client = AnthropicClient(api_key="test-key")
        assert client.model == "claude-sonnet-4-5-20250929"
        assert client.context_window == 200000

    def test_anthropic_aggressive_config(self):
        """Test Anthropic with aggressive settings"""
        client = AnthropicClient(
            api_key="test-key",
            model="claude-opus",
            temperature=1.5,
            max_tokens=100000
        )
        assert client.default_temperature == 1.5
        assert client.default_max_tokens == 100000

    def test_anthropic_conservative_config(self):
        """Test Anthropic with conservative settings"""
        client = AnthropicClient(
            api_key="test-key",
            temperature=0.1,
            max_tokens=500
        )
        assert client.default_temperature == 0.1
        assert client.default_max_tokens == 500


@pytest.mark.unit
class TestClientEdgeCases:
    """Tests for edge cases in client handling"""

    def test_empty_api_key_accepted(self):
        """Test that empty API key is accepted (validation is at runtime)"""
        client = AnthropicClient(api_key="")
        assert client.client is not None

    def test_special_characters_in_api_key(self):
        """Test API key with special characters"""
        special_key = "sk-test!@#$%^&*()"
        client = AnthropicClient(api_key=special_key)
        assert client.client is not None

    def test_very_long_model_name(self):
        """Test with very long model name"""
        long_model = "claude-" + "x" * 1000
        client = AnthropicClient(api_key="test-key", model=long_model)
        assert client.model == long_model

    def test_zero_temperature(self):
        """Test with zero temperature"""
        client = AnthropicClient(api_key="test-key", temperature=0.0)
        assert client.default_temperature == 0.0

    def test_very_high_temperature(self):
        """Test with very high temperature"""
        client = AnthropicClient(api_key="test-key", temperature=10.0)
        assert client.default_temperature == 10.0

    def test_very_small_max_tokens(self):
        """Test with very small max_tokens"""
        client = AnthropicClient(api_key="test-key", max_tokens=1)
        assert client.default_max_tokens == 1

    def test_very_large_max_tokens(self):
        """Test with very large max_tokens"""
        client = AnthropicClient(api_key="test-key", max_tokens=1000000)
        assert client.default_max_tokens == 1000000


@pytest.mark.unit
class TestClientInstanceIndependence:
    """Tests for client instance independence"""

    def test_multiple_anthropic_instances(self):
        """Test that multiple Anthropic clients are independent"""
        client1 = AnthropicClient(api_key="key1", model="model1", temperature=0.5)
        client2 = AnthropicClient(api_key="key2", model="model2", temperature=0.8)

        assert client1.model == "model1"
        assert client2.model == "model2"
        assert client1.default_temperature == 0.5
        assert client2.default_temperature == 0.8

    def test_client_attributes_preserved(self):
        """Test that client attributes are preserved"""
        client = AnthropicClient(
            api_key="test-key",
            model="claude-opus",
            temperature=0.7,
            max_tokens=4000
        )

        # All attributes should still be there
        assert client.model == "claude-opus"
        assert client.default_temperature == 0.7
        assert client.default_max_tokens == 4000
        assert client.model_name == "claude-opus"
        assert client.context_window == 200000


@pytest.mark.unit
class TestMessageResponseIntegration:
    """Tests for message response structure integration"""

    def test_anthropic_response_structure(self):
        """Test that Anthropic response converts to correct structure"""
        response = ModelResponse(
            content=[
                {"type": "text", "text": "Response text"},
                {"type": "tool_use", "id": "1", "name": "tool", "input": {"arg": "value"}}
            ],
            stop_reason="tool_use",
            usage={"input_tokens": 100, "output_tokens": 50},
            model="claude-3-sonnet"
        )

        # Verify response structure
        assert len(response.content) == 2
        assert response.content[0]["type"] == "text"
        assert response.content[1]["type"] == "tool_use"
        assert response.usage["input_tokens"] == 100
        assert response.model == "claude-3-sonnet"

    def test_multiple_text_blocks(self):
        """Test response with multiple text blocks"""
        response = ModelResponse(
            content=[
                {"type": "text", "text": "First part"},
                {"type": "text", "text": "Second part"}
            ],
            stop_reason="end_turn",
            usage={"input_tokens": 20, "output_tokens": 10},
            model="claude-3-sonnet"
        )

        assert len(response.content) == 2
        assert response.content[0]["text"] == "First part"
        assert response.content[1]["text"] == "Second part"
