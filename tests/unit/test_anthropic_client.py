"""
Unit tests for Anthropic Client

Tests client initialization, message creation, streaming, and error handling.
"""

import pytest
from unittest.mock import Mock, AsyncMock
import anthropic
import httpx
from src.clients.anthropic import AnthropicClient
from src.clients.base import ModelResponse


@pytest.fixture
def mock_anthropic_client():
    """Fixture to mock the underlying anthropic.AsyncAnthropic client."""
    mock_client = Mock()
    mock_client.messages = Mock()
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="Hello")]
    mock_response.stop_reason = "end_turn"
    mock_response.usage = Mock(input_tokens=10, output_tokens=20)
    mock_response.model = "claude-test"
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.mark.unit
class TestAnthropicClientInitialization:
    """Tests for Anthropic client initialization."""

    @pytest.mark.parametrize("params, expected", [
        ({}, {"model": "claude-sonnet-4-5-20250929", "temp": None, "tokens": None}),
        ({"model": "claude-opus-4-1"}, {"model": "claude-opus-4-1", "temp": None, "tokens": None}),
        ({"temperature": 0.7}, {"model": "claude-sonnet-4-5-20250929", "temp": 0.7, "tokens": None}),
        ({"max_tokens": 5000}, {"model": "claude-sonnet-4-5-20250929", "temp": None, "tokens": 5000}),
        ({"api_base": "https://custom.api.com"}, {"model": "claude-sonnet-4-5-20250929", "temp": None, "tokens": None}),
        (
            {"model": "claude-custom", "temperature": 0.5, "max_tokens": 3000},
            {"model": "claude-custom", "temp": 0.5, "tokens": 3000}
        ),
    ])
    def test_initialization(self, params, expected):
        """Test initialization with various parameters."""
        client = AnthropicClient("test_api_key", **params)
        assert client.model == expected["model"]
        assert client.default_temperature == expected["temp"]
        assert client.default_max_tokens == expected["tokens"]


@pytest.mark.unit
class TestAnthropicClientProperties:
    """Tests for client properties."""

    def test_client_properties(self):
        """Test model_name, context_window, and provider_name properties."""
        client = AnthropicClient("test_key", model="test-model")
        assert client.model_name == "test-model"
        assert client.context_window == 200000
        assert isinstance(client.context_window, int)
        assert client.provider_name == "anthropic"


@pytest.mark.unit
class TestAnthropicClientMessageCreation:
    """Tests for message creation call construction."""

    @pytest.mark.asyncio
    async def test_create_message_basic(self, mock_anthropic_client):
        """Test basic message creation parameters."""
        client = AnthropicClient("test_key")
        client.client = mock_anthropic_client

        result = await client.create_message(
            system="You are helpful",
            messages=[{"role": "user", "content": "Hi"}],
            tools=[],
            max_tokens=1000,
            temperature=0.8
        )

        assert isinstance(result, ModelResponse)
        mock_anthropic_client.messages.create.assert_called_once()
        call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
        assert call_kwargs['system'] == "You are helpful"
        assert call_kwargs['max_tokens'] == 1000
        assert call_kwargs['temperature'] == 0.8

    @pytest.mark.asyncio
    async def test_create_message_uses_default_params(self, mock_anthropic_client):
        """Test that default temperature and max_tokens are used."""
        client = AnthropicClient("test_key", temperature=0.5, max_tokens=2000)
        client.client = mock_anthropic_client

        await client.create_message(system="", messages=[], tools=[], temperature=0.9, max_tokens=4000)

        mock_anthropic_client.messages.create.assert_called_once()
        call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
        assert call_kwargs['temperature'] == 0.5  # Default temperature takes precedence
        assert call_kwargs['max_tokens'] == 2000   # Default max_tokens takes precedence

    @pytest.mark.asyncio
    async def test_create_message_with_tools_and_streaming(self, mock_anthropic_client):
        """Test message creation with tools and streaming enabled."""
        client = AnthropicClient("test_key")
        client.client = mock_anthropic_client
        tools = [{"name": "bash", "description": "Execute shell commands"}]

        await client.create_message(system="", messages=[], tools=tools, stream=True)

        mock_anthropic_client.messages.create.assert_called_once()
        call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
        assert call_kwargs['tools'] == tools
        assert call_kwargs['stream'] is True


@pytest.mark.unit
class TestAnthropicClientResponseParsing:
    """Tests for response parsing."""

    @pytest.mark.asyncio
    async def test_parse_text_and_tool_use_content(self, mock_anthropic_client):
        """Test parsing of mixed text and tool_use content from response."""
        client = AnthropicClient("test_key")
        client.client = mock_anthropic_client

        text_block = Mock(type="text", text="Response text")
        tool_use_block = Mock()
        tool_use_block.type = "tool_use"
        tool_use_block.id = "tool_123"
        tool_use_block.name = "bash"
        tool_use_block.input = {"command": "ls"}
        mock_anthropic_client.messages.create.return_value.content = [text_block, tool_use_block]

        result = await client.create_message(system="", messages=[], tools=[])

        assert len(result.content) == 2
        assert result.content[0] == {"type": "text", "text": "Response text"}
        assert result.content[1] == {"type": "tool_use", "id": "tool_123", "name": "bash", "input": {"command": "ls"}}

    @pytest.mark.asyncio
    async def test_parse_usage_information(self, mock_anthropic_client):
        """Test parsing of usage information."""
        client = AnthropicClient("test_key")
        client.client = mock_anthropic_client
        mock_anthropic_client.messages.create.return_value.usage = Mock(input_tokens=100, output_tokens=50)

        result = await client.create_message(system="", messages=[], tools=[])

        assert result.usage["input_tokens"] == 100
        assert result.usage["output_tokens"] == 50


@pytest.mark.unit
class TestAnthropicClientErrorHandling:
    """Tests for handling API errors."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("error_name, status_code", [
        ("api_error", 500),
        ("auth_error", 401),
        ("rate_limit_error", 429),
        ("bad_request_error", 400),
    ])
    async def test_api_errors_are_propagated(self, error_name, status_code, mock_anthropic_client):
        """Test that various API errors from the underlying client are propagated."""
        mock_request = Mock(spec=httpx.Request)
        mock_response = Mock(spec=httpx.Response)
        mock_response.request = mock_request
        mock_response.headers = {}  # for request_id
        mock_response.status_code = status_code

        error_map = {
            "api_error": anthropic.APIError(message="API Error", request=mock_request, body={}),
            "auth_error": anthropic.AuthenticationError(message="Auth Error", response=mock_response, body={}),
            "rate_limit_error": anthropic.RateLimitError(message="Rate Limit Error", response=mock_response, body={}),
            "bad_request_error": anthropic.BadRequestError(message="Bad Request Error", response=mock_response, body={}),
        }
        error = error_map[error_name]

        client = AnthropicClient("test_key")
        client.client = mock_anthropic_client
        mock_anthropic_client.messages.create.side_effect = error

        with pytest.raises(type(error)):
            await client.create_message(system="", messages=[], tools=[])
