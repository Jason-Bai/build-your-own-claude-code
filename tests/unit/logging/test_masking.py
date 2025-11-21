"""
单元测试：DataMasker

测试内容：
1. 敏感字段名脱敏
2. 正则模式脱敏（API密钥、Bearer token、文件路径）
3. 递归处理嵌套字典
4. 超长输出截断
5. 自定义敏感字段
"""
import pytest

from src.logging.masking import DataMasker


class TestSensitiveFieldMasking:
    """敏感字段名脱敏测试"""

    def test_mask_password_field(self):
        """测试密码字段脱敏"""
        masker = DataMasker(enabled=True)

        data = {
            "username": "alice",
            "password": "secret123",
            "email": "alice@example.com"
        }

        masked = masker.mask(data)

        assert masked["username"] == "alice"
        assert masked["password"] == "[MASKED]"
        assert masked["email"] == "alice@example.com"

    def test_mask_api_key_field(self):
        """测试API密钥字段脱敏"""
        masker = DataMasker(enabled=True)

        data = {
            "api_key": "sk-ant-api03-abcdefghijklmnopqrstuvwxyz",
            "model": "claude-3"
        }

        masked = masker.mask(data)

        assert masked["api_key"] == "[MASKED]"
        assert masked["model"] == "claude-3"

    def test_mask_multiple_sensitive_fields(self):
        """测试多个敏感字段"""
        masker = DataMasker(enabled=True)

        data = {
            "username": "bob",
            "password": "pass456",
            "api_key": "sk-xyz",
            "token": "bearer_token_123",
            "secret": "my_secret",
        }

        masked = masker.mask(data)

        assert masked["username"] == "bob"
        assert masked["password"] == "[MASKED]"
        assert masked["api_key"] == "[MASKED]"
        assert masked["token"] == "[MASKED]"
        assert masked["secret"] == "[MASKED]"

    def test_custom_sensitive_fields(self):
        """测试自定义敏感字段"""
        masker = DataMasker(
            enabled=True,
            custom_sensitive_fields=["internal_token", "ssh_key"]
        )

        data = {
            "username": "charlie",
            "internal_token": "internal_123",
            "ssh_key": "ssh-rsa AAAA...",
            "public_key": "public_data"
        }

        masked = masker.mask(data)

        assert masked["username"] == "charlie"
        assert masked["internal_token"] == "[MASKED]"
        assert masked["ssh_key"] == "[MASKED]"
        assert masked["public_key"] == "public_data"


class TestPatternMasking:
    """正则模式脱敏测试"""

    def test_mask_anthropic_api_key(self):
        """测试Anthropic API密钥脱敏"""
        masker = DataMasker(enabled=True)

        data = {
            "message": "Using API key sk-ant-api03-" + "a" * 48 + " for requests"
        }

        masked = masker.mask(data)

        assert "sk-***[MASKED]***" in masked["message"]
        assert "sk-ant-api03" not in masked["message"]

    def test_mask_openai_api_key(self):
        """测试OpenAI API密钥脱敏"""
        masker = DataMasker(enabled=True)

        data = {
            "config": "api_key: sk-" + "b" * 48
        }

        masked = masker.mask(data)

        assert "sk-***[MASKED]***" in masked["config"]

    def test_mask_bearer_token(self):
        """测试Bearer token脱敏"""
        masker = DataMasker(enabled=True)

        data = {
            "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        }

        masked = masker.mask(data)

        assert masked["authorization"] == "Bearer [MASKED]"

    def test_mask_user_directory_path_unix(self):
        """测试Unix用户目录路径脱敏"""
        masker = DataMasker(enabled=True)

        data = {
            "file_path": "/Users/baiyu/projects/myapp/config.json"
        }

        masked = masker.mask(data)

        assert "/Users/[USER]/" in masked["file_path"]
        assert "baiyu" not in masked["file_path"]

    def test_mask_user_directory_path_linux(self):
        """测试Linux用户目录路径脱敏"""
        masker = DataMasker(enabled=True)

        data = {
            "log_path": "/home/alice/.config/app/logs.txt"
        }

        masked = masker.mask(data)

        assert "/home/[USER]/" in masked["log_path"]
        assert "alice" not in masked["log_path"]

    def test_mask_user_directory_path_windows(self):
        """测试Windows用户目录路径脱敏"""
        masker = DataMasker(enabled=True)

        data = {
            "config_path": r"C:\Users\Bob\Documents\config.ini"
        }

        masked = masker.mask(data)

        assert r"C:\Users\[USER]" in masked["config_path"]
        assert "Bob" not in masked["config_path"]


class TestRecursiveMasking:
    """递归处理测试"""

    def test_mask_nested_dict(self):
        """测试嵌套字典脱敏"""
        masker = DataMasker(enabled=True)

        data = {
            "user": {
                "name": "dave",
                "credentials": {
                    "password": "secret789",
                    "api_key": "sk-xyz123"
                }
            },
            "config": {
                "timeout": 30
            }
        }

        masked = masker.mask(data)

        assert masked["user"]["name"] == "dave"
        assert masked["user"]["credentials"]["password"] == "[MASKED]"
        assert masked["user"]["credentials"]["api_key"] == "[MASKED]"
        assert masked["config"]["timeout"] == 30

    def test_mask_list_of_dicts(self):
        """测试字典列表脱敏"""
        masker = DataMasker(enabled=True)

        data = {
            "users": [
                {"name": "alice", "password": "pass1"},
                {"name": "bob", "password": "pass2"}
            ]
        }

        masked = masker.mask(data)

        assert masked["users"][0]["name"] == "alice"
        assert masked["users"][0]["password"] == "[MASKED]"
        assert masked["users"][1]["name"] == "bob"
        assert masked["users"][1]["password"] == "[MASKED]"

    def test_mask_deep_nesting(self):
        """测试深度嵌套脱敏"""
        masker = DataMasker(enabled=True)

        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "secret": "deep_secret"
                        }
                    }
                }
            }
        }

        masked = masker.mask(data)

        assert masked["level1"]["level2"]["level3"]["level4"]["secret"] == "[MASKED]"


class TestOutputTruncation:
    """超长输出截断测试"""

    def test_truncate_long_string(self):
        """测试超长字符串截断"""
        masker = DataMasker(
            enabled=True,
            truncate_large_output=True,
            max_output_chars=100
        )

        long_text = "a" * 500
        data = {"output": long_text}

        masked = masker.mask(data)

        assert len(masked["output"]) < len(long_text)
        assert "[TRUNCATED" in masked["output"]
        assert "400 chars]" in masked["output"]

    def test_no_truncation_for_short_string(self):
        """测试短字符串不截断"""
        masker = DataMasker(
            enabled=True,
            truncate_large_output=True,
            max_output_chars=100
        )

        short_text = "Short text"
        data = {"output": short_text}

        masked = masker.mask(data)

        assert masked["output"] == short_text
        assert "[TRUNCATED" not in masked["output"]

    def test_truncation_disabled(self):
        """测试禁用截断"""
        masker = DataMasker(
            enabled=True,
            truncate_large_output=False
        )

        long_text = "b" * 10000
        data = {"output": long_text}

        masked = masker.mask(data)

        assert masked["output"] == long_text
        assert "[TRUNCATED" not in masked["output"]


class TestDisabledMasker:
    """禁用脱敏器测试"""

    def test_disabled_masker_returns_original(self):
        """测试禁用脱敏器返回原始数据"""
        masker = DataMasker(enabled=False)

        data = {
            "password": "secret123",
            "api_key": "sk-ant-api03-xyz",
            "output": "a" * 10000
        }

        masked = masker.mask(data)

        # 应该返回原始数据，不做任何修改
        assert masked == data


class TestCombinedMasking:
    """综合脱敏测试"""

    def test_field_and_pattern_masking_combined(self):
        """测试字段名和模式脱敏组合"""
        masker = DataMasker(enabled=True)

        data = {
            "api_key": "sk-ant-api03-" + "x" * 48,  # 字段名敏感
            "message": "API key is sk-" + "y" * 48  # 模式匹配
        }

        masked = masker.mask(data)

        # 字段名脱敏
        assert masked["api_key"] == "[MASKED]"

        # 模式脱敏
        assert "sk-***[MASKED]***" in masked["message"]

    def test_real_world_log_data(self):
        """测试真实日志数据脱敏"""
        masker = DataMasker(enabled=True, max_output_chars=200)

        data = {
            "action_type": "llm_request",
            "provider": "anthropic",
            "model": "claude-3",
            "api_key": "sk-ant-api03-abcdefg123456",
            "request_headers": {
                "Authorization": "Bearer secret_token_xyz"
            },
            "config_path": "/Users/alice/.config/app/settings.json",
            "response": "a" * 500,  # 超长输出
            "timestamp": "2025-01-01T10:00:00"
        }

        masked = masker.mask(data)

        # 敏感字段被脱敏
        assert masked["api_key"] == "[MASKED]"
        assert masked["request_headers"]["Authorization"] == "Bearer [MASKED]"

        # 路径被脱敏
        assert "/Users/[USER]/" in masked["config_path"]

        # 超长输出被截断
        assert len(masked["response"]) < 500
        assert "[TRUNCATED" in masked["response"]

        # 非敏感字段保持不变
        assert masked["action_type"] == "llm_request"
        assert masked["timestamp"] == "2025-01-01T10:00:00"
