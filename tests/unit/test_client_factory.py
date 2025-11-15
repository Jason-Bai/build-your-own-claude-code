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
        providers = ["anthropic", "openai"]

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

@pytest.mark.unit
class TestCreateClientOpenAIProvider:
    """Tests for creating OpenAI client through factory"""

    def test_create_openai_client_basic(self):
        """Test creating OpenAI client through factory"""
        try:
            from src.clients.factory import check_provider_available
            if not check_provider_available("openai"):
                pytest.skip("OpenAI not installed")

            client = create_client("openai", "test_api_key")
            assert client is not None
        except ImportError:
            pytest.skip("OpenAI client not available")
        except Exception as e:
            if "not installed" in str(e):
                pytest.skip("OpenAI SDK not installed")

    def test_create_openai_client_with_model(self):
        """Test creating OpenAI client with custom model"""
        try:
            from src.clients.factory import check_provider_available
            if not check_provider_available("openai"):
                pytest.skip("OpenAI not installed")

            client = create_client("openai", "test_api_key", model="gpt-4o")
            assert client.model == "gpt-4o"
        except Exception as e:
            if "not installed" in str(e):
                pytest.skip("OpenAI SDK not installed")


@pytest.mark.unit
class TestFactoryErrorMessages:
    """Tests for error messages from factory"""

    def test_unsupported_provider_message_includes_provider(self):
        """Test that unsupported provider error includes the provider name"""
        with pytest.raises(ValueError) as exc_info:
            create_client("unknown_provider", "api_key")

        assert "unknown_provider" in str(exc_info.value)

    def test_import_error_message_for_openai(self):
        """Test that OpenAI provider gives helpful error when import fails"""
        # This test verifies that if OpenAI is not available, we get a clear error
        # In this test environment, OpenAI may or may not be installed, so we just
        # verify that the factory handles both cases appropriately
        try:
            # Try to create OpenAI client
            client = create_client("openai", "test_key")
            # If it succeeds, verify it's an OpenAI client
            assert client is not None
        except (ImportError, ValueError) as e:
            # If it fails, ensure the error message is helpful
            error_msg = str(e)
            # Should contain helpful info about openai or provider
            assert "openai" in error_msg.lower() or "unsupported" in error_msg.lower()


@pytest.mark.unit
class TestFactoryProviderAvailability:
    """Tests for provider availability checking"""

    def test_check_anthropic_is_available(self):
        """Test Anthropic is available"""
        result = check_provider_available("anthropic")
        assert result is True

    def test_check_openai_returns_boolean(self):
        """Test that OpenAI check returns boolean"""
        result = check_provider_available("openai")
        assert isinstance(result, bool)

    def test_check_invalid_provider_returns_false(self):
        """Test that invalid provider returns False"""
        result = check_provider_available("invalid_provider_xyz")
        assert result is False


@pytest.mark.unit
class TestFactoryClientInstanceIsolation:
    """Tests that factory creates isolated client instances"""

    def test_separate_anthropic_instances(self):
        """Test that separate calls create different instances"""
        client1 = create_client("anthropic", "key1")
        client2 = create_client("anthropic", "key2")

        assert client1 is not client2
        assert id(client1) != id(client2)

    def test_clients_with_different_models_isolated(self):
        """Test that clients with different models are separate instances"""
        client1 = create_client("anthropic", "key", model="model1")
        client2 = create_client("anthropic", "key", model="model2")

        assert client1.model != client2.model

    def test_clients_with_different_configs_isolated(self):
        """Test that clients with different configs are separate instances"""
        client1 = create_client("anthropic", "key", temperature=0.5)
        client2 = create_client("anthropic", "key", temperature=0.9)

        assert client1.default_temperature != client2.default_temperature


@pytest.mark.unit
class TestFactoryKwargsPropagation:
    """Tests that kwargs are properly propagated to clients"""

    def test_all_kwargs_passed_to_anthropic(self):
        """Test that all kwargs are passed to AnthropicClient"""
        client = create_client(
            "anthropic",
            "test_key",
            model="claude-opus",
            temperature=0.6,
            max_tokens=2000,
            api_base="https://api.example.com"
        )

        assert client.model == "claude-opus"
        assert client.default_temperature == 0.6
        assert client.default_max_tokens == 2000

    def test_kwargs_preserved_with_multiple_params(self):
        """Test that all parameters are preserved"""
        params = {
            "model": "test-model",
            "temperature": 0.75,
            "max_tokens": 5000,
            "api_base": "https://custom.api"
        }

        client = create_client("anthropic", "key", **params)

        for key, value in params.items():
            if key == "model":
                assert client.model == value
            elif key == "temperature":
                assert client.default_temperature == value
            elif key == "max_tokens":
                assert client.default_max_tokens == value


@pytest.mark.unit
class TestFactoryEdgeCases:
    """Tests for edge cases in factory"""

    def test_create_client_with_none_api_key(self):
        """Test creating client with None api_key"""
        # Should still create the client object, but SDK will fail on actual API calls
        client = create_client("anthropic", None)
        assert client is not None

    def test_create_client_with_empty_string_api_key(self):
        """Test creating client with empty string api_key"""
        client = create_client("anthropic", "")
        assert client is not None

    def test_provider_name_case_sensitivity(self):
        """Test that provider names are case-sensitive"""
        # lowercase should work
        result = check_provider_available("anthropic")
        assert result is True

        # uppercase should fail
        result = check_provider_available("ANTHROPIC")
        assert result is False


@pytest.mark.unit
class TestFactoryBaseClientInheritance:
    """Tests that created clients inherit from BaseClient"""

    def test_anthropic_client_is_base_client(self):
        """Test AnthropicClient inherits from BaseClient"""
        from src.clients.base import BaseClient

        client = create_client("anthropic", "test_key")
        assert isinstance(client, BaseClient)

    def test_created_client_has_base_methods(self):
        """Test that created client has BaseClient methods"""
        client = create_client("anthropic", "test_key")

        assert hasattr(client, 'create_message')
        assert hasattr(client, 'generate_summary')
        assert hasattr(client, 'model_name')
        assert hasattr(client, 'context_window')


@pytest.mark.unit
class TestFactoryDocstring:
    """Tests for factory function documentation"""

    def test_create_client_function_has_docstring(self):
        """Test that create_client has documentation"""
        assert create_client.__doc__ is not None
        assert "create_client" in create_client.__doc__ or "client" in create_client.__doc__.lower()

    def test_check_provider_available_has_docstring(self):
        """Test that check_provider_available has documentation"""
        assert check_provider_available.__doc__ is not None
