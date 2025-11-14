"""
Unit tests for Client Factory

Tests client creation and provider availability checking.
"""

import pytest
from unittest.mock import Mock, patch
from src.clients.factory import create_client, check_provider_available


@pytest.mark.unit
class TestCreateClientAnthropicProvider:
    """Tests for creating Anthropic client"""

    def test_create_anthropic_client_basic(self):
        """Test creating Anthropic client with basic parameters"""
        client = create_client("anthropic", "test_api_key")

        assert client is not None
        from src.clients.anthropic import AnthropicClient
        assert isinstance(client, AnthropicClient)

    def test_create_anthropic_client_with_model(self):
        """Test creating Anthropic client with custom model"""
        client = create_client("anthropic", "test_api_key", model="claude-opus-4-1")

        assert client.model == "claude-opus-4-1"

    def test_create_anthropic_client_with_temperature(self):
        """Test creating Anthropic client with temperature"""
        client = create_client(
            "anthropic",
            "test_api_key",
            temperature=0.5
        )

        assert client.default_temperature == 0.5

    def test_create_anthropic_client_with_max_tokens(self):
        """Test creating Anthropic client with max_tokens"""
        client = create_client(
            "anthropic",
            "test_api_key",
            max_tokens=4000
        )

        assert client.default_max_tokens == 4000

    def test_create_anthropic_client_with_api_base(self):
        """Test creating Anthropic client with custom API base"""
        client = create_client(
            "anthropic",
            "test_api_key",
            api_base="https://custom.api.com"
        )

        assert client is not None


@pytest.mark.unit
class TestCreateClientErrors:
    """Tests for error handling in create_client"""

    def test_create_client_unsupported_provider(self):
        """Test creating client with unsupported provider"""
        with pytest.raises(ValueError, match="Unsupported provider"):
            create_client("unsupported_provider", "api_key")

    def test_create_client_unsupported_provider_custom_message(self):
        """Test error message contains provider name"""
        with pytest.raises(ValueError, match="invalid_provider"):
            create_client("invalid_provider", "api_key")

    def test_create_client_empty_provider(self):
        """Test creating client with empty provider"""
        with pytest.raises(ValueError):
            create_client("", "api_key")


@pytest.mark.unit
class TestCheckProviderAvailable:
    """Tests for checking provider availability"""

    def test_check_anthropic_available(self):
        """Test checking Anthropic provider"""
        result = check_provider_available("anthropic")
        assert isinstance(result, bool)
        assert result is True  # Should be installed

    def test_check_unsupported_provider(self):
        """Test checking unsupported provider"""
        result = check_provider_available("unsupported")
        assert result is False

    def test_check_empty_provider(self):
        """Test checking empty provider"""
        result = check_provider_available("")
        assert result is False

    def test_check_provider_case_sensitivity(self):
        """Test that provider check is case-sensitive"""
        result = check_provider_available("ANTHROPIC")
        assert result is False  # Should be lowercase

    def test_check_openai_availability(self):
        """Test checking OpenAI provider"""
        result = check_provider_available("openai")
        assert isinstance(result, bool)

    def test_check_google_availability(self):
        """Test checking Google provider"""
        result = check_provider_available("google")
        assert isinstance(result, bool)


@pytest.mark.unit
class TestFactoryIntegration:
    """Integration tests for factory"""

    def test_create_client_returns_base_client(self):
        """Test that created client is BaseClient instance"""
        from src.clients.base import BaseClient

        client = create_client("anthropic", "test_key")
        assert isinstance(client, BaseClient)

    def test_multiple_client_creation(self):
        """Test creating multiple client instances"""
        client1 = create_client("anthropic", "key1")
        client2 = create_client("anthropic", "key2")

        assert client1 is not client2
        assert client1 is not None
        assert client2 is not None

    def test_create_with_all_parameters(self):
        """Test creating client with all possible parameters"""
        client = create_client(
            "anthropic",
            "test_api_key",
            model="claude-opus-4-1",
            temperature=0.7,
            max_tokens=5000,
            api_base="https://api.anthropic.com"
        )

        assert client is not None
        assert client.model == "claude-opus-4-1"
        assert client.default_temperature == 0.7
        assert client.default_max_tokens == 5000

    def test_check_all_providers(self):
        """Test checking all provider types"""
        providers = ["anthropic", "openai", "google"]

        for provider in providers:
            result = check_provider_available(provider)
            assert isinstance(result, bool)

    def test_create_client_properties(self):
        """Test created client has required properties"""
        client = create_client("anthropic", "test_key", model="claude-test")

        assert hasattr(client, 'client')
        assert hasattr(client, 'model')
        assert hasattr(client, 'default_temperature')
        assert hasattr(client, 'default_max_tokens')

    def test_create_client_kwargs_passed(self):
        """Test that kwargs are passed to client initialization"""
        client = create_client(
            "anthropic",
            "test_key",
            model="custom-model",
            temperature=0.3,
            max_tokens=2000
        )

        assert client.model == "custom-model"
        assert client.default_temperature == 0.3
        assert client.default_max_tokens == 2000
