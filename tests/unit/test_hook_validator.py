"""
Unit tests for Hook Configuration Validator

Tests validation of hook configurations for security and correctness.
"""

import pytest
from src.hooks.validator import HookConfigValidator, SecurityError


@pytest.mark.unit
class TestHookConfigValidatorInitialization:
    """Tests for validator initialization"""

    def test_initialization_default(self):
        """Test default initialization"""
        validator = HookConfigValidator()
        assert validator.strict_mode is False

    def test_initialization_strict_mode(self):
        """Test initialization with strict mode"""
        validator = HookConfigValidator(strict_mode=True)
        assert validator.strict_mode is True

    def test_forbidden_modules_set(self):
        """Test forbidden modules are defined"""
        validator = HookConfigValidator()
        assert len(validator.FORBIDDEN_MODULES) > 0
        assert "os" in validator.FORBIDDEN_MODULES
        assert "subprocess" in validator.FORBIDDEN_MODULES

    def test_forbidden_functions_set(self):
        """Test forbidden functions are defined"""
        validator = HookConfigValidator()
        assert len(validator.FORBIDDEN_FUNCTIONS) > 0
        assert "exec" in validator.FORBIDDEN_FUNCTIONS
        assert "eval" in validator.FORBIDDEN_FUNCTIONS


@pytest.mark.unit
class TestValidateHandlerPath:
    """Tests for handler path validation"""

    def test_valid_handler_path(self):
        """Test valid handler path"""
        validator = HookConfigValidator()
        assert validator.validate_handler_path("my_module:my_handler") is True

    def test_valid_handler_path_with_dots(self):
        """Test valid handler path with package hierarchy"""
        validator = HookConfigValidator()
        assert validator.validate_handler_path("my_package.my_module:my_handler") is True

    def test_missing_colon_raises_error(self):
        """Test missing colon raises ValueError"""
        validator = HookConfigValidator()
        with pytest.raises(ValueError, match="Invalid handler path format"):
            validator.validate_handler_path("my_module_my_handler")

    def test_multiple_colons_raises_error(self):
        """Test multiple colons raise ValueError"""
        validator = HookConfigValidator()
        with pytest.raises(ValueError, match="Expected single colon separator"):
            validator.validate_handler_path("module:handler:extra")

    def test_empty_module_name_raises_error(self):
        """Test empty module name raises ValueError"""
        validator = HookConfigValidator()
        with pytest.raises(ValueError, match="Module name cannot be empty"):
            validator.validate_handler_path(":handler")

    def test_empty_function_name_raises_error(self):
        """Test empty function name raises ValueError"""
        validator = HookConfigValidator()
        with pytest.raises(ValueError, match="Function name cannot be empty"):
            validator.validate_handler_path("module:")

    def test_forbidden_module_raises_security_error(self):
        """Test forbidden module raises SecurityError"""
        validator = HookConfigValidator()
        with pytest.raises(SecurityError, match="Forbidden module"):
            validator.validate_handler_path("os:system")

    def test_forbidden_module_subprocess(self):
        """Test subprocess module is forbidden"""
        validator = HookConfigValidator()
        with pytest.raises(SecurityError, match="Forbidden module"):
            validator.validate_handler_path("subprocess:call")

    def test_forbidden_module_sys(self):
        """Test sys module is forbidden"""
        validator = HookConfigValidator()
        with pytest.raises(SecurityError, match="Forbidden module"):
            validator.validate_handler_path("sys:exit")

    def test_private_function_raises_security_error(self):
        """Test private function raises SecurityError"""
        validator = HookConfigValidator()
        with pytest.raises(SecurityError, match="Cannot load private function"):
            validator.validate_handler_path("module:_private_handler")

    def test_forbidden_function_exec_raises_error(self):
        """Test forbidden function 'exec' raises SecurityError"""
        validator = HookConfigValidator()
        with pytest.raises(SecurityError, match="Forbidden function"):
            validator.validate_handler_path("module:exec")

    def test_forbidden_function_eval_raises_error(self):
        """Test forbidden function 'eval' raises SecurityError"""
        validator = HookConfigValidator()
        with pytest.raises(SecurityError, match="Forbidden function"):
            validator.validate_handler_path("module:eval")

    def test_forbidden_function_open_raises_error(self):
        """Test forbidden function 'open' raises SecurityError"""
        validator = HookConfigValidator()
        with pytest.raises(SecurityError, match="Forbidden function"):
            validator.validate_handler_path("module:open")

    def test_strict_mode_relative_import_raises_error(self):
        """Test relative imports not allowed in strict mode"""
        validator = HookConfigValidator(strict_mode=True)
        with pytest.raises(SecurityError, match="Relative imports not allowed"):
            validator.validate_handler_path(".relative_module:handler")

    def test_strict_mode_backslash_in_module_raises_error(self):
        """Test backslash in module name raises error in strict mode"""
        validator = HookConfigValidator(strict_mode=True)
        with pytest.raises(SecurityError, match="Invalid characters"):
            validator.validate_handler_path("module\\submodule:handler")

    def test_strict_mode_forward_slash_raises_error(self):
        """Test forward slash in module name raises error in strict mode"""
        validator = HookConfigValidator(strict_mode=True)
        with pytest.raises(SecurityError, match="Invalid characters"):
            validator.validate_handler_path("module/submodule:handler")

    def test_strict_mode_semicolon_raises_error(self):
        """Test semicolon in module name raises error in strict mode"""
        validator = HookConfigValidator(strict_mode=True)
        with pytest.raises(SecurityError, match="Invalid characters"):
            validator.validate_handler_path("module;submodule:handler")

    def test_non_strict_mode_relative_import_allowed(self):
        """Test relative imports allowed in non-strict mode"""
        validator = HookConfigValidator(strict_mode=False)
        # Should not raise error
        assert validator.validate_handler_path(".relative_module:handler") is True


@pytest.mark.unit
class TestValidatePriority:
    """Tests for priority validation"""

    def test_valid_priority_zero(self):
        """Test priority 0 is valid"""
        validator = HookConfigValidator()
        assert validator.validate_priority(0) is True

    def test_valid_priority_positive(self):
        """Test positive priority is valid"""
        validator = HookConfigValidator()
        assert validator.validate_priority(100) is True

    def test_valid_priority_negative(self):
        """Test negative priority is valid"""
        validator = HookConfigValidator()
        assert validator.validate_priority(-100) is True

    def test_valid_priority_max(self):
        """Test maximum priority is valid"""
        validator = HookConfigValidator()
        assert validator.validate_priority(1000) is True

    def test_valid_priority_min(self):
        """Test minimum priority is valid"""
        validator = HookConfigValidator()
        assert validator.validate_priority(-1000) is True

    def test_priority_above_max_raises_error(self):
        """Test priority above max raises ValueError"""
        validator = HookConfigValidator()
        with pytest.raises(ValueError, match="Priority must be between"):
            validator.validate_priority(1001)

    def test_priority_below_min_raises_error(self):
        """Test priority below min raises ValueError"""
        validator = HookConfigValidator()
        with pytest.raises(ValueError, match="Priority must be between"):
            validator.validate_priority(-1001)

    def test_priority_non_integer_raises_error(self):
        """Test non-integer priority raises TypeError"""
        validator = HookConfigValidator()
        with pytest.raises(TypeError, match="Priority must be an integer"):
            validator.validate_priority(1.5)

    def test_priority_string_raises_error(self):
        """Test string priority raises TypeError"""
        validator = HookConfigValidator()
        with pytest.raises(TypeError, match="Priority must be an integer"):
            validator.validate_priority("100")

    def test_priority_none_raises_error(self):
        """Test None priority raises TypeError"""
        validator = HookConfigValidator()
        with pytest.raises(TypeError, match="Priority must be an integer"):
            validator.validate_priority(None)


@pytest.mark.unit
class TestValidateEventName:
    """Tests for event name validation"""

    def test_valid_event_name(self):
        """Test valid event name"""
        validator = HookConfigValidator()
        assert validator.validate_event_name("tool.execute") is True

    def test_valid_event_name_category_event(self):
        """Test event name with category.event format"""
        validator = HookConfigValidator()
        assert validator.validate_event_name("hook.before_execute") is True

    def test_empty_event_name_raises_error(self):
        """Test empty event name raises ValueError"""
        validator = HookConfigValidator()
        with pytest.raises(ValueError, match="Event name cannot be empty"):
            validator.validate_event_name("")

    def test_event_name_non_string_raises_error(self):
        """Test non-string event name raises TypeError"""
        validator = HookConfigValidator()
        with pytest.raises(TypeError, match="Event name must be a string"):
            validator.validate_event_name(123)

    def test_event_name_none_raises_error(self):
        """Test None event name raises ValueError (checks for empty first)"""
        validator = HookConfigValidator()
        # None is falsy, so it triggers "cannot be empty" error before type check
        with pytest.raises(ValueError, match="Event name cannot be empty"):
            validator.validate_event_name(None)

    def test_event_name_without_dot_logs_warning(self, caplog):
        """Test event name without dot logs warning"""
        validator = HookConfigValidator()
        # This should log a warning but still return True
        result = validator.validate_event_name("simple_event")
        assert result is True
        # Warning is logged but doesn't raise exception


@pytest.mark.unit
class TestValidateHandlerConfig:
    """Tests for complete handler configuration validation"""

    def test_valid_handler_config(self):
        """Test valid handler configuration"""
        validator = HookConfigValidator()
        config = {
            "handler": "module:handler",
            "event": "hook.execute",
            "priority": 0,
            "enabled": True
        }
        assert validator.validate_handler_config(config) is True

    def test_handler_config_minimal(self):
        """Test handler config with only required fields"""
        validator = HookConfigValidator()
        config = {
            "handler": "module:handler",
            "event": "hook.execute"
        }
        assert validator.validate_handler_config(config) is True

    def test_handler_config_missing_handler_raises_error(self):
        """Test missing 'handler' field raises ValueError"""
        validator = HookConfigValidator()
        config = {
            "event": "hook.execute"
        }
        with pytest.raises(ValueError, match="missing 'handler'"):
            validator.validate_handler_config(config)

    def test_handler_config_missing_event_raises_error(self):
        """Test missing 'event' field raises ValueError"""
        validator = HookConfigValidator()
        config = {
            "handler": "module:handler"
        }
        with pytest.raises(ValueError, match="missing 'event'"):
            validator.validate_handler_config(config)

    def test_handler_config_invalid_handler_type(self):
        """Test invalid handler type raises TypeError"""
        validator = HookConfigValidator()
        config = {
            "handler": 123,
            "event": "hook.execute"
        }
        with pytest.raises(TypeError, match="'handler' must be a string"):
            validator.validate_handler_config(config)

    def test_handler_config_invalid_event_type(self):
        """Test invalid event type raises TypeError"""
        validator = HookConfigValidator()
        config = {
            "handler": "module:handler",
            "event": 123
        }
        with pytest.raises(TypeError, match="'event' must be a string"):
            validator.validate_handler_config(config)

    def test_handler_config_invalid_priority_type(self):
        """Test invalid priority type raises TypeError"""
        validator = HookConfigValidator()
        config = {
            "handler": "module:handler",
            "event": "hook.execute",
            "priority": "high"
        }
        with pytest.raises(TypeError, match="'priority' must be an integer"):
            validator.validate_handler_config(config)

    def test_handler_config_invalid_enabled_type(self):
        """Test invalid enabled type raises TypeError"""
        validator = HookConfigValidator()
        config = {
            "handler": "module:handler",
            "event": "hook.execute",
            "enabled": "yes"
        }
        with pytest.raises(TypeError, match="'enabled' must be a boolean"):
            validator.validate_handler_config(config)

    def test_handler_config_with_forbidden_module(self):
        """Test handler config with forbidden module raises SecurityError"""
        validator = HookConfigValidator()
        config = {
            "handler": "os:system",
            "event": "hook.execute"
        }
        with pytest.raises(SecurityError, match="Forbidden module"):
            validator.validate_handler_config(config)

    def test_handler_config_with_private_function(self):
        """Test handler config with private function raises SecurityError"""
        validator = HookConfigValidator()
        config = {
            "handler": "module:_private",
            "event": "hook.execute"
        }
        with pytest.raises(SecurityError, match="Cannot load private function"):
            validator.validate_handler_config(config)

    def test_handler_config_with_invalid_priority(self):
        """Test handler config with out-of-range priority raises ValueError"""
        validator = HookConfigValidator()
        config = {
            "handler": "module:handler",
            "event": "hook.execute",
            "priority": 5000
        }
        with pytest.raises(ValueError, match="Priority must be between"):
            validator.validate_handler_config(config)

    def test_handler_config_defaults_priority(self):
        """Test handler config uses default priority 0"""
        validator = HookConfigValidator()
        config = {
            "handler": "module:handler",
            "event": "hook.execute"
            # priority not specified, should default to 0
        }
        assert validator.validate_handler_config(config) is True

    def test_handler_config_defaults_enabled(self):
        """Test handler config uses default enabled True"""
        validator = HookConfigValidator()
        config = {
            "handler": "module:handler",
            "event": "hook.execute"
            # enabled not specified, should default to True
        }
        assert validator.validate_handler_config(config) is True


@pytest.mark.unit
class TestValidatorIntegration:
    """Integration tests for validator"""

    def test_strict_mode_vs_non_strict(self):
        """Test differences between strict and non-strict mode"""
        strict_validator = HookConfigValidator(strict_mode=True)
        non_strict_validator = HookConfigValidator(strict_mode=False)

        # Relative import should fail in strict mode
        with pytest.raises(SecurityError):
            strict_validator.validate_handler_path(".relative:handler")

        # But pass in non-strict mode
        assert non_strict_validator.validate_handler_path(".relative:handler") is True

    def test_multiple_validations_on_config(self):
        """Test multiple validations on the same config"""
        validator = HookConfigValidator()

        # Valid config passes all checks
        config = {
            "handler": "my_handlers:on_tool_execute",
            "event": "tool.before_execute",
            "priority": 50,
            "enabled": True
        }

        assert validator.validate_handler_path(config["handler"]) is True
        assert validator.validate_event_name(config["event"]) is True
        assert validator.validate_priority(config["priority"]) is True
        assert validator.validate_handler_config(config) is True

    def test_security_boundaries(self):
        """Test all security boundaries are enforced"""
        validator = HookConfigValidator()

        # All forbidden modules should raise SecurityError
        for module in ["os", "sys", "subprocess", "socket"]:
            with pytest.raises(SecurityError):
                validator.validate_handler_path(f"{module}:any_func")

        # All forbidden functions should raise SecurityError
        for func in ["exec", "eval", "compile", "open", "__import__"]:
            with pytest.raises(SecurityError):
                validator.validate_handler_path(f"module:{func}")
