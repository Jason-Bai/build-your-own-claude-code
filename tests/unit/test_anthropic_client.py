"""
Unit tests for Anthropic Client

Tests client initialization, message creation, and streaming.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from src.clients.anthropic import AnthropicClient
from src.clients.base import ModelResponse


@pytest.mark.unit
class TestAnthropicClientInitialization:
    """Tests for Anthropic client initialization"""

    def test_initialization_default(self):
        """Test default initialization"""
        client = AnthropicClient("test_api_key")

        assert client.model == "claude-sonnet-4-5-20250929"
        assert client.default_temperature is None
        assert client.default_max_tokens is None

    def test_initialization_custom_model(self):
        """Test initialization with custom model"""
        client = AnthropicClient("test_api_key", model="claude-opus-4-1")

        assert client.model == "claude-opus-4-1"

    def test_initialization_with_temperature(self):
        """Test initialization with temperature"""
        client = AnthropicClient("test_api_key", temperature=0.7)

        assert client.default_temperature == 0.7

    def test_initialization_with_max_tokens(self):
        """Test initialization with max_tokens"""
        client = AnthropicClient("test_api_key", max_tokens=5000)

        assert client.default_max_tokens == 5000

    def test_initialization_with_api_base(self):
        """Test initialization with custom API base"""
        client = AnthropicClient("test_api_key", api_base="https://custom.api.com")

        assert client.client is not None

    def test_initialization_all_parameters(self):
        """Test initialization with all parameters"""
        client = AnthropicClient(
            "test_api_key",
            model="claude-custom",
            api_base="https://api.example.com",
            temperature=0.5,
            max_tokens=3000
        )

        assert client.model == "claude-custom"
        assert client.default_temperature == 0.5
        assert client.default_max_tokens == 3000


@pytest.mark.unit
class TestAnthropicClientProperties:
    """Tests for client properties"""

    def test_model_name_property(self):
        """Test model_name property"""
        client = AnthropicClient("test_key", model="test-model")

        assert client.model_name == "test-model"

    def test_context_window_property(self):
        """Test context_window property"""
        client = AnthropicClient("test_key")

        assert client.context_window == 200000

    def test_context_window_is_integer(self):
        """Test context_window returns integer"""
        client = AnthropicClient("test_key")

        assert isinstance(client.context_window, int)
        assert client.context_window > 0


@pytest.mark.unit
class TestAnthropicClientMessageCreation:
    """Tests for message creation"""

    @pytest.mark.asyncio
    async def test_create_message_basic(self):
        """Test basic message creation"""
        client = AnthropicClient("test_key")

        # Mock the async client
        mock_response = Mock()
        mock_response.content = [Mock(type="text", text="Hello")]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock(input_tokens=10, output_tokens=20)
        mock_response.model = "claude-test"

        client.client.messages.create = AsyncMock(return_value=mock_response)

        result = await client.create_message(
            system="You are helpful",
            messages=[{"role": "user", "content": "Hi"}],
            tools=[],
            max_tokens=1000
        )

        assert isinstance(result, ModelResponse)
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_create_message_with_temperature_override(self):
        """Test that default temperature is used when set"""
        client = AnthropicClient("test_key", temperature=0.5)

        mock_response = Mock()
        mock_response.content = []
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock(input_tokens=0, output_tokens=0)
        mock_response.model = "claude-test"

        client.client.messages.create = AsyncMock(return_value=mock_response)

        await client.create_message(
            system="",
            messages=[],
            tools=[],
            temperature=0.9
        )

        # Verify the client was called with the default temperature (takes precedence)
        client.client.messages.create.assert_called_once()
        call_kwargs = client.client.messages.create.call_args.kwargs
        assert call_kwargs['temperature'] == 0.5  # Default temperature takes precedence

    @pytest.mark.asyncio
    async def test_create_message_uses_default_temperature(self):
        """Test that default temperature is used when not passed"""
        client = AnthropicClient("test_key", temperature=0.3)

        mock_response = Mock()
        mock_response.content = []
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock(input_tokens=0, output_tokens=0)
        mock_response.model = "claude-test"

        client.client.messages.create = AsyncMock(return_value=mock_response)

        await client.create_message(
            system="",
            messages=[],
            tools=[]
        )

        call_kwargs = client.client.messages.create.call_args.kwargs
        assert call_kwargs['temperature'] == 0.3

    @pytest.mark.asyncio
    async def test_create_message_with_tools(self):
        """Test message creation with tools"""
        client = AnthropicClient("test_key")

        tools = [{"name": "bash", "description": "Execute shell commands"}]

        mock_response = Mock()
        mock_response.content = []
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock(input_tokens=0, output_tokens=0)
        mock_response.model = "claude-test"

        client.client.messages.create = AsyncMock(return_value=mock_response)

        await client.create_message(
            system="",
            messages=[],
            tools=tools
        )

        call_kwargs = client.client.messages.create.call_args.kwargs
        assert call_kwargs['tools'] == tools

    @pytest.mark.asyncio
    async def test_create_message_streaming_parameter(self):
        """Test that stream parameter is passed correctly"""
        client = AnthropicClient("test_key")

        mock_response = Mock()
        mock_response.content = []
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock(input_tokens=0, output_tokens=0)
        mock_response.model = "claude-test"

        client.client.messages.create = AsyncMock(return_value=mock_response)

        await client.create_message(
            system="",
            messages=[],
            tools=[],
            stream=False
        )

        call_kwargs = client.client.messages.create.call_args.kwargs
        assert call_kwargs['stream'] is False


@pytest.mark.unit
class TestAnthropicClientResponseParsing:
    """Tests for response parsing"""

    @pytest.mark.asyncio
    async def test_parse_text_content(self):
        """Test parsing text content from response"""
        client = AnthropicClient("test_key")

        text_block = Mock(type="text", text="Response text")
        mock_response = Mock()
        mock_response.content = [text_block]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock(input_tokens=5, output_tokens=10)
        mock_response.model = "claude-test"

        client.client.messages.create = AsyncMock(return_value=mock_response)

        result = await client.create_message(
            system="",
            messages=[],
            tools=[]
        )

        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        assert result.content[0]["text"] == "Response text"

    @pytest.mark.asyncio
    async def test_parse_tool_use_content(self):
        """Test parsing tool_use content from response"""
        client = AnthropicClient("test_key")

        # Create tool_use_block as a proper mock with attributes
        tool_use_block = Mock()
        tool_use_block.type = "tool_use"
        tool_use_block.id = "tool_123"
        tool_use_block.name = "bash"
        tool_use_block.input = {"command": "ls"}

        mock_response = Mock()
        mock_response.content = [tool_use_block]
        mock_response.stop_reason = "tool_use"
        mock_response.usage = Mock(input_tokens=5, output_tokens=10)
        mock_response.model = "claude-test"

        client.client.messages.create = AsyncMock(return_value=mock_response)

        result = await client.create_message(
            system="",
            messages=[],
            tools=[]
        )

        assert len(result.content) == 1
        assert result.content[0]["type"] == "tool_use"
        assert result.content[0]["id"] == "tool_123"
        assert result.content[0]["name"] == "bash"
        assert result.content[0]["input"] == {"command": "ls"}

    @pytest.mark.asyncio
    async def test_parse_usage_information(self):
        """Test parsing usage information"""
        client = AnthropicClient("test_key")

        mock_response = Mock()
        mock_response.content = []
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)
        mock_response.model = "claude-test"

        client.client.messages.create = AsyncMock(return_value=mock_response)

        result = await client.create_message(
            system="",
            messages=[],
            tools=[]
        )

        assert result.usage["input_tokens"] == 100
        assert result.usage["output_tokens"] == 50


@pytest.mark.unit
class TestAnthropicClientIntegration:
    """Integration tests for Anthropic client"""

    @pytest.mark.asyncio
    async def test_multiple_sequential_messages(self):
        """Test sending multiple messages sequentially"""
        client = AnthropicClient("test_key")

        mock_response = Mock()
        mock_response.content = [Mock(type="text", text="Response")]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock(input_tokens=10, output_tokens=20)
        mock_response.model = "claude-test"

        client.client.messages.create = AsyncMock(return_value=mock_response)

        for i in range(3):
            result = await client.create_message(
                system="",
                messages=[{"role": "user", "content": f"Message {i}"}],
                tools=[]
            )

            assert isinstance(result, ModelResponse)

        assert client.client.messages.create.call_count == 3

    def test_client_initialization_creates_async_client(self):
        """Test that initialization creates AsyncAnthropic client"""
        client = AnthropicClient("test_key")

        assert client.client is not None
        assert hasattr(client.client, 'messages')
