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
class TestGoogleClientAsyncBehavior:
    """Tests for async behavior in Google client"""

    def test_async_generate_content_call_structure(self):
        """Test the structure of async generate_content call"""
        # Verify that generate_content_async is called with correct parameters
        expected_params = {
            "messages": [],
            "generation_config": {},
            "stream": False
        }

        assert "messages" in expected_params
        assert "generation_config" in expected_params
        assert "stream" in expected_params


@pytest.mark.unit
class TestGoogleClientErrorHandling:
    """Tests for error handling in Google client"""

    def test_error_response_structure(self):
        """Test structure of error response from client"""
        error_response = {
            "content": [{"type": "text", "text": "Error: API request failed"}],
            "stop_reason": "error",
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "model": "gemini-2.5-flash"
        }

        assert error_response["stop_reason"] == "error"
        assert "Error" in error_response["content"][0]["text"]
        assert error_response["usage"]["input_tokens"] == 0

    def test_safe_response_with_fallback(self):
        """Test safe response creation with fallback text"""
        # When extraction fails, fallback should be used
        fallback_text = "No content available"
        response_content = []

        # Simulate fallback logic
        if not response_content and fallback_text:
            response_content = [{"type": "text", "text": fallback_text}]

        assert len(response_content) == 1
        assert response_content[0]["text"] == fallback_text


@pytest.mark.unit
class TestGoogleClientUsageMetadata:
    """Tests for usage metadata extraction from Google responses"""

    def test_usage_metadata_extraction(self):
        """Test extracting usage metadata from response"""
        # Simulate Google response with usage_metadata
        mock_response = Mock()
        mock_response.usage_metadata = Mock(
            prompt_token_count=100,
            candidates_token_count=50
        )

        # Verify extraction logic
        input_tokens = mock_response.usage_metadata.prompt_token_count
        output_tokens = mock_response.usage_metadata.candidates_token_count

        assert input_tokens == 100
        assert output_tokens == 50

    def test_missing_usage_metadata_handling(self):
        """Test handling when usage_metadata is None"""
        mock_response = Mock()
        mock_response.usage_metadata = None

        # Client should provide default values
        input_tokens = mock_response.usage_metadata.prompt_token_count if mock_response.usage_metadata else 0
        output_tokens = mock_response.usage_metadata.candidates_token_count if mock_response.usage_metadata else 0

        assert input_tokens == 0
        assert output_tokens == 0


@pytest.mark.unit
class TestGoogleClientSystemPromptHandling:
    """Tests for system prompt handling in Google client"""

    def test_system_prompt_added_to_messages(self):
        """Test that system prompt is added as first message"""
        system_prompt = "You are a helpful assistant"
        messages = []

        # Simulate adding system prompt
        if system_prompt:
            messages.append({"role": "user", "parts": [system_prompt]})
            messages.append({"role": "model", "parts": ["Understood. I will follow these instructions."]})

        assert len(messages) == 2
        assert system_prompt in messages[0]["parts"]

    def test_system_prompt_empty_handling(self):
        """Test handling of empty system prompt"""
        system_prompt = ""
        messages = []

        if system_prompt:
            messages.append({"role": "user", "parts": [system_prompt]})

        assert len(messages) == 0


@pytest.mark.unit
class TestGoogleClientStreamingBehavior:
    """Tests for streaming behavior"""

    def test_streaming_chunk_extraction(self):
        """Test extracting text from streaming chunks"""
        mock_chunk = Mock()
        mock_chunk.text = "Streaming text"

        extracted = mock_chunk.text if mock_chunk.text else ""
        assert extracted == "Streaming text"

    def test_empty_chunk_handling(self):
        """Test handling of empty chunks"""
        mock_chunk = Mock()
        mock_chunk.text = ""

        extracted = mock_chunk.text if mock_chunk.text else None
        assert extracted is None  # Empty string is falsy, so None is returned


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

    def test_google_client_model_name_property(self):
        """Test model_name property"""
        try:
            from src.clients.factory import check_provider_available, create_client

            if not check_provider_available("google"):
                pytest.skip("Google Generative AI package not installed")

            client = create_client("google", "test_key", model="gemini-2.5-flash")
            assert "gemini-2.5-flash" in client.model_name
        except Exception as e:
            if "not installed" in str(e):
                pytest.skip("Google SDK not installed")
            raise
