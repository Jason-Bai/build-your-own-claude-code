"""Main CLI application with EnhancedAgent"""

import asyncio
import os
import sys
import json
import argparse
from pathlib import Path
# Optional dependency for .env file support
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    def load_dotenv():
        # Fallback: do nothing if dotenv not available
        pass

from .agents import EnhancedAgent, PermissionMode
from .clients import create_client
from .tools import (
    ReadTool, WriteTool, EditTool,
    BashTool, GlobTool, GrepTool,
    TodoWriteTool, TodoManager
)
from .commands import CLIContext, command_registry, register_builtin_commands
from .prompts import get_system_prompt
from .mcps import MCPClient, MCPServerConfig
from .persistence import ConversationPersistence
from .utils import OutputFormatter, OutputLevel


def load_config(config_path: str = "config.json") -> dict:
    """加载配置文件，优先级：config.json -> .env -> 环境变量"""
    config = {}

    # 1. 先加载 config.json 作为默认配置
    if Path(config_path).exists():
        with open(config_path, 'r') as f:
            config = json.load(f)

    # 2. 如果存在 .env 文件，用 .env 覆盖 config.json
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)

        # 从 .env 文件读取配置并覆盖 config.json
        # 注意：这里用 os.environ.get() 而不是 os.getenv() 来获取 .env 文件中的值
        model_config = config.get("model", {})
        model_config["ANTHROPIC_API_KEY"] = os.environ.get("ANTHROPIC_API_KEY") or model_config.get("ANTHROPIC_API_KEY")
        model_config["ANTHROPIC_MODEL"] = os.environ.get("ANTHROPIC_MODEL") or model_config.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
        model_config["ANTHROPIC_API_BASE"] = os.environ.get("ANTHROPIC_API_BASE") or model_config.get("ANTHROPIC_API_BASE", "https://api.anthropic.com/v1")

        model_config["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY") or model_config.get("OPENAI_API_KEY")
        model_config["OPENAI_MODEL"] = os.environ.get("OPENAI_MODEL") or model_config.get("OPENAI_MODEL", "gpt-4o")
        model_config["OPENAI_API_BASE"] = os.environ.get("OPENAI_API_BASE") or model_config.get("OPENAI_API_BASE", "https://api.openai.com/v1")

        model_config["GOOGLE_API_KEY"] = os.environ.get("GOOGLE_API_KEY") or model_config.get("GOOGLE_API_KEY")
        model_config["GOOGLE_MODEL"] = os.environ.get("GOOGLE_MODEL") or model_config.get("GOOGLE_MODEL", "gemini-1.5-flash")
        model_config["GOOGLE_API_BASE"] = os.environ.get("GOOGLE_API_BASE") or model_config.get("GOOGLE_API_BASE", "https://generativelanguage.googleapis.com/v1beta")

        model_config["temperature"] = float(os.environ.get("TEMPERATURE") or model_config.get("temperature", 0.7))
        model_config["max_tokens"] = int(os.environ.get("MAX_TOKENS") or model_config.get("max_tokens", 4000))

        config["model"] = model_config

    # 3. 最后用环境变量覆盖（如果用户 export 了）
    # 递归替换 ${VAR_NAME} 格式的环境变量
    config = _resolve_env_vars(config)

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


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Build Your Own Claude Code - Enhanced Edition"
    )

    # 权限控制参数（互斥）
    permission_group = parser.add_mutually_exclusive_group()
    permission_group.add_argument(
        "--dangerously-skip-permissions",
        action="store_true",
        help="Skip all permission checks (DANGEROUS)"
    )
    permission_group.add_argument(
        "--auto-approve-all",
        action="store_true",
        help="Automatically approve all tools (dangerous)"
    )
    permission_group.add_argument(
        "--always-ask",
        action="store_true",
        help="Always ask for permission, even for safe tools"
    )

    # 输出级别参数（互斥）
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output (show tool details, thinking process)"
    )
    output_group.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode (only show errors and agent responses)"
    )

    # 其他参数
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config file (default: config.json)"
    )

    return parser.parse_args()


async def initialize_agent(config: dict = None, args=None) -> EnhancedAgent:
    """初始化 EnhancedAgent"""

    config = config or {}

    # 获取模型配置（此时 config 已经按优先级加载好了）
    model_config = config.get("model", {})

    # 直接从 model_config 中获取值（已经按优先级处理过了）
    anthropic_api_key = model_config.get("ANTHROPIC_API_KEY")
    anthropic_model = model_config.get(
        "ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

    openai_api_key = model_config.get("OPENAI_API_KEY")
    openai_model = model_config.get("OPENAI_MODEL", "gpt-4o")

    google_api_key = model_config.get("GOOGLE_API_KEY")
    google_model = model_config.get("GOOGLE_MODEL", "gemini-1.5-flash")

    # 检测可用的 API provider（按优先级检查 API_KEY 是否存在）
    selected_provider = None
    api_key = None
    model_name = None

    if anthropic_api_key:
        selected_provider = "anthropic"
        api_key = anthropic_api_key
        model_name = anthropic_model

    elif openai_api_key:
        selected_provider = "openai"
        api_key = openai_api_key
        model_name = openai_model

    elif google_api_key:
        selected_provider = "gemini"
        api_key = google_api_key
        model_name = google_model

    # 如果还是没找到，报错并显示配置指南
    if not selected_provider or not api_key:
        OutputFormatter.error("No API provider configuration found")
        print("\nPlease configure using one of the following methods:")
        print("\nMethod 1 - Environment Variables (Highest Priority):")
        print("  export ANTHROPIC_API_KEY='your-key'")
        print("  export ANTHROPIC_MODEL='claude-sonnet-4-5-20250929'  # optional")
        print("\nMethod 2 - .env file (copy .env.example to .env):")
        print("  ANTHROPIC_API_KEY=your-key")
        print("  ANTHROPIC_MODEL=claude-sonnet-4-5-20250929")
        print("\nMethod 3 - config.json (fallback):")
        print("  {")
        print("    \"model\": {")
        print("      \"ANTHROPIC_API_KEY\": \"your-key\",")
        print("      \"ANTHROPIC_MODEL\": \"claude-sonnet-4-5-20250929\"")
        print("    }")
        print("  }")
        sys.exit(1)

    # 创建客户端
    client = create_client(
        provider=selected_provider,
        api_key=api_key,
        model=model_name,
        api_base=model_config.get(
            "ANTHROPIC_API_BASE", "https://api.anthropic.com/v1"),
        temperature=model_config.get("temperature"),
        max_tokens=model_config.get("max_tokens")
    )

    OutputFormatter.success(f"Using model: {client.model_name} (provider: {selected_provider})")

    # 确定权限模式
    permission_mode = PermissionMode.AUTO_APPROVE_SAFE  # 默认
    if args:
        if args.dangerously_skip_permissions:
            permission_mode = PermissionMode.SKIP_ALL
            OutputFormatter.warning("Running with --dangerously-skip-permissions")
        elif args.auto_approve_all:
            permission_mode = PermissionMode.AUTO_APPROVE_ALL
            OutputFormatter.warning("Auto-approving all tools")
        elif args.always_ask:
            permission_mode = PermissionMode.ALWAYS_ASK
            OutputFormatter.info("Will ask permission for all tools")

    # 初始化 MCP（如果配置了）
    mcp_client = None
    mcp_configs = config.get("mcp_servers", [])

    if mcp_configs:
        mcp_client = MCPClient()

        if mcp_client.is_available():
            print("\n🔌 Loading MCP servers...")
            for server_config in mcp_configs:
                try:
                    mcp_config = MCPServerConfig(**server_config)
                    if mcp_config.enabled:
                        await mcp_client.connect_server(mcp_config)
                except Exception as e:
                    OutputFormatter.warning(f"Failed to load MCP server: {e}")
        else:
            OutputFormatter.info("MCP not installed. Install with: pip install mcp")
            mcp_client = None

    # 创建 EnhancedAgent
    agent = EnhancedAgent(
        client=client,
        system_prompt=get_system_prompt(),
        max_turns=config.get("max_turns", 20),
        max_context_tokens=int(client.context_window * 0.8),
        mcp_client=mcp_client,
        permission_mode=permission_mode
    )

    # 注册内置工具
    agent.tool_manager.register_tools([
        ReadTool(),
        WriteTool(),
        EditTool(),
        BashTool(),
        GlobTool(),
        GrepTool(),
        TodoWriteTool(agent.todo_manager)
    ])

    return agent


async def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()

    # 设置输出级别
    if args.verbose:
        OutputFormatter.set_level(OutputLevel.VERBOSE)
    elif args.quiet:
        OutputFormatter.set_level(OutputLevel.QUIET)
    else:
        OutputFormatter.set_level(OutputLevel.NORMAL)

    OutputFormatter.info("🤖 Build Your Own Claude Code - Enhanced Edition")
    print("=" * 50)

    # 加载配置
    config = load_config(args.config)

    # 初始化 Agent
    agent = await initialize_agent(config, args)

    # 注册内置命令
    register_builtin_commands()

    # 初始化持久化
    persistence = ConversationPersistence()

    # 创建 CLI 上下文
    cli_context = CLIContext(agent, config={"persistence": persistence})

    # 显示欢迎信息
    builtin_tools = len(agent.tool_manager.tools)
    mcp_tools = len(agent.mcp_client.tools) if agent.mcp_client else 0
    total_tools = builtin_tools + mcp_tools

    OutputFormatter.success(f"Loaded {total_tools} tools")
    print(f"  - Built-in: {builtin_tools}")
    if mcp_tools > 0:
        print(f"  - MCP: {mcp_tools}")

    # 🆕 自动加载 CLAUDE.md（如果存在且配置启用）
    if config.get("auto_load_context", True):
        claude_md_path = Path.cwd() / "CLAUDE.md"
        if claude_md_path.exists():
            try:
                with open(claude_md_path, 'r', encoding='utf-8') as f:
                    context_content = f.read()

                agent.context_manager.add_user_message(
                    f"[System: Project Context]\n\n{context_content}"
                )

                OutputFormatter.success(f"Auto-loaded CLAUDE.md ({len(context_content)} chars)")
            except Exception as e:
                OutputFormatter.warning(f"Failed to load CLAUDE.md: {e}")
        else:
            OutputFormatter.info("No CLAUDE.md found. Use /init to create one.")

    print("\n💡 Type /help to see available commands")
    print("💡 Type /exit to quit\n")

    # 主循环
    try:
        while True:
            try:
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                # 检查是否是命令
                if command_registry.is_command(user_input):
                    result = await command_registry.execute(user_input, cli_context)
                    if result:
                        print(result)
                    print()
                    continue

                # 普通对话
                print()
                stats = await agent.run(user_input, verbose=True)

                # 自动保存（可选）
                if config.get("auto_save", False):
                    conversation_id = persistence.auto_save_id()
                    persistence.save_conversation(
                        conversation_id,
                        [msg.model_dump()
                         for msg in agent.context_manager.messages],
                        agent.context_manager.system_prompt,
                        agent.context_manager.summary,
                        {"stats": stats}
                    )

            except KeyboardInterrupt:
                print("\n\n💡 Use /exit to quit properly")
                continue
            except EOFError:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
                print("💡 Type /clear to reset if needed\n")

    finally:
        # 清理 MCP 连接
        if agent.mcp_client:
            print("\n🔌 Disconnecting MCP servers...")
            await agent.mcp_client.disconnect_all()
        print()


def cli():
    """CLI 入口点"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    cli()
