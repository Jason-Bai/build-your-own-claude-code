"""
Unit tests for the LLM Client Factory and Provider Utilities.

Tests the `create_client` factory function and the `check_provider_available` utility.
"""

import pytest
from src.clients.anthropic import AnthropicClient
from src.clients.factory import create_client, check_provider_available


@pytest.mark.unit
class TestClientFactory:
    """Tests for the client factory."""

    def test_create_anthropic_client(self):
        """Test creating an Anthropic client."""
        # This test assumes ANTHROPIC_API_KEY is available in the environment
        # or the test runner is configured to handle it.
        client = create_client("anthropic", api_key="test-key")
        assert isinstance(client, AnthropicClient)

    def test_create_anthropic_with_model(self):
        """Test creating an Anthropic client with a custom model."""
        client = create_client("anthropic", api_key="test-key", model="claude-opus")
        assert client.model == "claude-opus"

    def test_create_client_invalid_provider(self):
        """Test that creating a client with an unsupported provider raises a ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider: invalid"):
            create_client("invalid", api_key="test-key")


@pytest.mark.unit
class TestProviderAvailability:
    """Tests for the provider availability check."""

    def test_check_anthropic_available(self):
        """Test that the check for 'anthropic' returns a boolean."""
        # This depends on whether 'anthropic' is installed in the test environment.
        available = check_provider_available("anthropic")
        assert isinstance(available, bool)

    def test_check_unavailable_provider(self):
        """Test that a non-existent provider is reported as unavailable."""
        available = check_provider_available("nonexistent_provider")
        assert not available
