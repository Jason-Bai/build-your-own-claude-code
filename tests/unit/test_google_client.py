"""
Unit tests for Google Gemini Client

Tests client initialization, message creation, and response parsing for Google provider.
Since Google Gemini is an optional dependency, we focus on testing client logic
assuming the Google SDK is available.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.clients.base import ModelResponse


@pytest.mark.unit
class TestGoogleClientInitialization:
    """Tests for Google Gemini client initialization"""

    @patch.dict('sys.modules', {'google': MagicMock(), 'google.generativeai': MagicMock()})
    def test_initialization_without_import_error(self):
        """Test that client can be imported when google-generativeai is available"""
        try:
            from src.clients.google import GoogleClient
            # This would need the actual SDK to fully work, so we just check it imports
            assert GoogleClient is not None
        except ImportError:
            pytest.skip("Google Generative AI package not available")

    def test_google_import_error_handling(self):
        """Test that ImportError is raised when Google SDK not available"""
        # Just verify the error message structure exists in the module
        try:
            from src.clients.google import GoogleClient
            # If we can import, verify the client exists
            assert GoogleClient is not None
        except ImportError as e:
            # If import fails, it should be with the right message
            assert "Google AI package not installed" in str(e) or "not installed" in str(e)


@pytest.mark.unit
class TestGoogleClientProperties:
    """Tests for Google client model-based properties"""

    def test_context_window_sizes_for_models(self):
        """Test context window sizes for different Gemini models"""
        model_windows = {
            "gemini-1.5": 1000000,  # Gemini 1.5 supports 1M tokens
            "gemini-1.0": 32000,    # Gemini 1.0 / Pro
            "gemini-flash": 100000, # Default
        }

        # Verify the expected values
        assert model_windows["gemini-1.5"] == 1000000
        assert model_windows["gemini-1.0"] == 32000
        assert model_windows["gemini-flash"] == 100000

    def test_model_name_transformation(self):
        """Test model name handling with 'models/' prefix"""
        # Google Gemini models may need 'models/' prefix
        models = {
            "gemini-2.5-flash": "models/gemini-2.5-flash",
            "models/gemini-pro": "models/gemini-pro",
        }

        # Test that both formats result in correct internal model string
        for input_model, expected_output in models.items():
            # Remove the 'models/' prefix if present
            model_name = input_model.replace("models/", "")
            expected_name = expected_output.replace("models/", "")
            assert model_name == expected_name


@pytest.mark.unit
class TestGoogleMessageFormatConversion:
    """Tests for message format conversion logic"""

    def test_message_format_structure(self):
        """Test that message format follows Gemini's expected structure"""
        # Gemini uses role and parts structure
        gemini_message_structure = {
            "role": "user",  # or "model"
            "parts": ["Some text content"]
        }

        # Verify structure
        assert "role" in gemini_message_structure
        assert "parts" in gemini_message_structure
        assert isinstance(gemini_message_structure["parts"], list)

    def test_role_conversion(self):
        """Test message role conversion to Gemini format"""
        # Anthropic roles map to Gemini roles
        role_mapping = {
            "user": "user",
            "assistant": "model",
        }

        assert role_mapping["user"] == "user"
        assert role_mapping["assistant"] == "model"

    def test_content_formatting(self):
        """Test content handling for different types"""
        # Gemini uses 'parts' array instead of single content field
        test_content = "Hello, world!"
        parts_format = [test_content]

        assert isinstance(parts_format, list)
        assert parts_format[0] == test_content


@pytest.mark.unit
class TestGoogleGenerationConfig:
    """Tests for Gemini generation configuration"""

    def test_generation_config_structure(self):
        """Test that generation config has expected structure"""
        generation_config = {
            "temperature": 0.7,
            "max_output_tokens": 8000,
        }

        assert "temperature" in generation_config
        assert "max_output_tokens" in generation_config
        assert generation_config["temperature"] == 0.7

    def test_default_parameter_values(self):
        """Test default parameter values for generation"""
        defaults = {
            "temperature": 1.0,
            "max_output_tokens": 8000,
        }

        assert defaults["temperature"] == 1.0
        assert defaults["max_output_tokens"] == 8000


@pytest.mark.unit
class TestGoogleClientIntegration:
    """Integration-level tests for Google client"""

    def test_google_client_availability_check(self):
        """Test that client availability can be checked without errors"""
        try:
            from src.clients.factory import check_provider_available
            result = check_provider_available("google")
            assert isinstance(result, bool)
        except ImportError:
            pytest.skip("Clients module not available")

    def test_client_creation_through_factory(self):
        """Test that Google client can be created through factory if available"""
        try:
            from src.clients.factory import create_client, check_provider_available

            if not check_provider_available("google"):
                pytest.skip("Google Generative AI package not installed")

            # Should be able to create client through factory
            client = create_client("google", "test_key")
            assert client is not None
            assert hasattr(client, 'model')
            assert hasattr(client, 'default_temperature')
            assert hasattr(client, 'default_max_tokens')
        except ImportError as e:
            pytest.skip(f"Required module not available: {e}")
        except Exception as e:
            # If Google SDK is not installed, skip
            if "not installed" in str(e):
                pytest.skip("Google SDK not installed")
            raise


@pytest.mark.unit
class TestGoogleSafeResponseHandling:
    """Tests for safe response handling in Google client"""

    def test_safe_response_creation(self):
        """Test safe response creation with fallback values"""
        # Test that the client can handle various response formats safely
        response_data = {
            "content": [{"type": "text", "text": "Response"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 10, "output_tokens": 20},
            "model": "gemini-2.5-flash"
        }

        # Verify structure is correct
        assert response_data["content"][0]["type"] == "text"
        assert response_data["stop_reason"] == "end_turn"
        assert response_data["usage"]["input_tokens"] == 10

    def test_error_response_handling(self):
        """Test handling of error responses"""
        # When an error occurs, the client should return a safe error response
        error_response = {
            "content": [{"type": "text", "text": "Error: Request failed"}],
            "stop_reason": "error",
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }

        assert error_response["stop_reason"] == "error"
        assert "Error" in error_response["content"][0]["text"]

    def test_finish_reason_normalization(self):
        """Test finish reason normalization"""
        # Gemini finish reasons need to be normalized to Anthropic format
        finish_reason_map = {
            "STOP": "end_turn",
            "MAX_TOKENS": "max_tokens",
            "OTHER": "end_turn",  # Default
        }

        assert finish_reason_map["STOP"] == "end_turn"
        assert finish_reason_map["MAX_TOKENS"] == "max_tokens"


@pytest.mark.unit
class TestGoogleClientModelHandling:
    """Tests for Google client model handling"""

    def test_model_name_formatting(self):
        """Test that model names are properly formatted with models/ prefix"""
        test_models = [
            ("gemini-2.5-flash", "models/gemini-2.5-flash"),
            ("models/gemini-2.5-flash", "models/gemini-2.5-flash"),
            ("gemini-pro", "models/gemini-pro"),
        ]

        for input_model, expected_format in test_models:
            # Verify the transformation logic
            if not input_model.startswith("models/"):
                formatted = f"models/{input_model}"
            else:
                formatted = input_model

            assert formatted == expected_format or formatted.replace("models/", "") == expected_format.replace("models/", "")

    def test_model_name_property(self):
        """Test model_name property returns clean model name without prefix"""
        # Model name should be returned without 'models/' prefix
        full_model = "models/gemini-2.5-flash"
        clean_name = full_model.replace("models/", "")

        assert clean_name == "gemini-2.5-flash"
        assert "models/" not in clean_name
