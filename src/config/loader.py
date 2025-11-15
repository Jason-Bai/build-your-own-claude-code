import json
import os
import shutil
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(**kwargs):
        pass

from ..utils.output import OutputFormatter


def load_config(config_path: str = "~/.tiny-claude-code/settings.json") -> dict:
    """加载配置文件，如果不存在则从模板创建"""
    resolved_config_path = Path(config_path).expanduser()

    # 如果配置文件不存在，从模板创建
    if not resolved_config_path.exists():
        try:
            # 确保目标目录存在
            resolved_config_path.parent.mkdir(parents=True, exist_ok=True)

            # 确定模板文件的路径
            template_path = Path(__file__).parent.parent.parent / \
                "templates" / "settings.json"

            if template_path.exists():
                shutil.copy(template_path, resolved_config_path)
                OutputFormatter.info(
                    f"Configuration file created at: {resolved_config_path}"
                )
                OutputFormatter.info(
                    "Please edit this file to add your API keys and customize settings."
                )
            else:
                OutputFormatter.warning(
                    f"Configuration template not found at: {template_path}"
                )
        except Exception as e:
            OutputFormatter.error(f"Failed to create configuration file: {e}")

    config = {}
    # 1. 先加载主配置文件
    if resolved_config_path.exists():
        with open(resolved_config_path, 'r') as f:
            config = json.load(f)

    # 2. 如果存在 .env 文件，加载环境变量
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(dotenv_path=env_file)

    # 3. 处理providers配置 - 从环境变量和配置文件合并
    providers = config.get("providers", {})

    # 设置默认providers（如果未在config中定义）
    if "openai" not in providers:
        providers["openai"] = {}
    if "anthropic" not in providers:
        providers["anthropic"] = {}

    # 从环境变量覆盖OpenAI配置
    providers["openai"]["api_key"] = os.environ.get(
        "OPENAI_API_KEY") or providers["openai"].get("api_key")
    providers["openai"]["model_name"] = os.environ.get(
        "OPENAI_MODEL") or providers["openai"].get("model_name", "gpt-4o")
    providers["openai"]["api_base"] = os.environ.get(
        "OPENAI_API_BASE") or providers["openai"].get("api_base", "https://api.openai.com/v1")

    # 从环境变量覆盖Anthropic配置
    providers["anthropic"]["api_key"] = os.environ.get(
        "ANTHROPIC_API_KEY") or providers["anthropic"].get("api_key")
    providers["anthropic"]["model_name"] = os.environ.get(
        "ANTHROPIC_MODEL") or providers["anthropic"].get("model_name", "claude-sonnet-4-5-20250929")
    providers["anthropic"]["api_base"] = os.environ.get(
        "ANTHROPIC_API_BASE") or providers["anthropic"].get("api_base", "https://api.anthropic.com/v1")

    config["providers"] = providers

    # 4. 处理model配置
    model_config = config.get("model", {})

    # 获取当前provider选择（默认为openai）
    current_provider = os.environ.get(
        "MODEL_PROVIDER") or model_config.get("provider", "openai")

    model_config["provider"] = current_provider
    model_config["temperature"] = float(os.environ.get(
        "TEMPERATURE") or model_config.get("temperature", 0.7))
    model_config["max_tokens"] = int(os.environ.get(
        "MAX_TOKENS") or model_config.get("max_tokens", 4000))

    config["model"] = model_config

    # 5. 验证provider选择有效
    if current_provider not in providers:
        OutputFormatter.warning(
            f"⚠️  Provider '{current_provider}' not found in configured providers. "
            f"Available: {list(providers.keys())}"
        )

    # 验证选定provider有有效的API Key
    selected_provider_config = providers.get(current_provider, {})
    if not selected_provider_config.get("api_key"):
        OutputFormatter.warning(
            f"⚠️  Provider '{current_provider}' has no valid API key configured."
        )

    # 6. 解析环境变量占位符（${VAR}格式）
    config = _resolve_env_vars(config)

    # 7. 打印加载后的配置（调试用）
    OutputFormatter.debug(f"Loaded config: {json.dumps(config, indent=2)}")

    return config


def _resolve_env_vars(obj):
    """递归替换环境变量"""
    if isinstance(obj, str):
        if obj.startswith("${") and obj.endswith("}"):
            var_name = obj[2:-1]
            return os.getenv(var_name, obj)
        return obj
    elif isinstance(obj, dict):
        return {k: _resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_resolve_env_vars(item) for item in obj]
    else:
        return obj
