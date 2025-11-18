import sys
from pathlib import Path

from ..agents import EnhancedAgent, PermissionMode
from ..clients import create_client, check_provider_available
from ..tools import (
    ReadTool, WriteTool, EditTool,
    BashTool, GlobTool, GrepTool,
    TodoWriteTool, WebSearchTool
)
from ..prompts import get_system_prompt
from ..mcps import MCPClient, MCPServerConfig
from ..utils import OutputFormatter
from ..hooks import HookManager, HookEvent, HookConfigLoader
from ..events import EventBus, EventType, Event
from ..persistence.manager import PersistenceManager
from ..persistence.storage import JSONStorage, SQLiteStorage, BaseStorage
from ..sessions.manager import SessionManager


def create_storage_from_config(config: dict) -> BaseStorage:
    storage_config = config.get("persistence", {})
    storage_type = storage_config.get("storage_type", "json")
    base_dir = storage_config.get("base_dir", "~/.cache/tiny-claude-code")

    project_name = Path.cwd().name

    if storage_type == "sqlite":
        return SQLiteStorage(project_name, base_dir)
    else:
        return JSONStorage(project_name, base_dir)


async def initialize_agent(config: dict = None, args=None) -> EnhancedAgent:
    """初始化 EnhancedAgent"""
    config = config or {}
    model_config = config.get("model", {})
    providers_config = config.get("providers", {})

    # 获取当前选择的provider
    selected_provider = model_config.get("provider", "openai")

    # 获取选定provider的配置
    provider_settings = providers_config.get(selected_provider, {})
    api_key = provider_settings.get("api_key")
    model_name = provider_settings.get("model_name")
    api_base = provider_settings.get("api_base")

    # 验证provider是否可用
    if not check_provider_available(selected_provider):
        OutputFormatter.error(
            f"Provider '{selected_provider}' is not available. "
            f"Please install the required package for {selected_provider}."
        )
        sys.exit(1)

    # 验证API Key是否存在
    if not api_key:
        OutputFormatter.error(
            f"No API key configured for provider '{selected_provider}'"
        )
        sys.exit(1)

    client = create_client(
        provider=selected_provider,
        api_key=api_key,
        model=model_name,
        api_base=api_base,
        temperature=model_config.get("temperature"),
        max_tokens=model_config.get("max_tokens")
    )

    permission_mode = PermissionMode.AUTO_APPROVE_SAFE
    if args:
        if args.dangerously_skip_permissions:
            permission_mode = PermissionMode.SKIP_ALL
        elif args.auto_approve_all:
            permission_mode = PermissionMode.AUTO_APPROVE_ALL
        elif args.always_ask:
            permission_mode = PermissionMode.ALWAYS_ASK

    mcp_client = None
    if config.get("mcp_servers"):
        mcp_client = MCPClient()
        if mcp_client.is_available():
            for server_config in config["mcp_servers"]:
                try:
                    mcp_config = MCPServerConfig(**server_config)
                    if mcp_config.enabled:
                        await mcp_client.connect_server(mcp_config)
                except Exception as e:
                    OutputFormatter.warning(f"Failed to load MCP server: {e}")
        else:
            mcp_client = None

    hook_manager = HookManager()
    persistence_manager = PersistenceManager(
        create_storage_from_config(config))

    agent = EnhancedAgent(
        client=client,
        system_prompt=get_system_prompt(),
        max_turns=config.get("max_turns", 20),
        max_context_tokens=int(client.context_window * 0.8),
        mcp_client=mcp_client,
        permission_mode=permission_mode,
        hook_manager=hook_manager,
        persistence_manager=persistence_manager
    )

    _setup_hooks(hook_manager, config, verbose=args.verbose if args else False)
    await _load_user_hooks(hook_manager, verbose=args.verbose if args else False)

    # Initialize web search tool
    web_search_config = config.get("web_search", {})
    print(web_search_config)
    web_search_tool = WebSearchTool(
        api_key=web_search_config.get("api_key"),
        search_engine_id=web_search_config.get("search_engine_id"),
        provider=web_search_config.get("provider", "duckduckgo"),
        max_results=web_search_config.get("max_results", 5),
        timeout=web_search_config.get("timeout", 20)
    )

    agent.tool_manager.register_tools([
        ReadTool(), WriteTool(), EditTool(), BashTool(), GlobTool(), GrepTool(),
        TodoWriteTool(agent.todo_manager), web_search_tool
    ])

    # Initialize SessionManager for session management
    session_manager = SessionManager(persistence_manager)
    agent.session_manager = session_manager

    return agent


def _setup_hooks(hook_manager: HookManager, config: dict, verbose: bool = False) -> None:
    if verbose:
        async def log_hook(context):
            OutputFormatter.info(
                f"📍 Hook: {context.event.value} | "
                f"request_id={context.request_id[:8]} | "
                f"data_keys={list(context.data.keys())}"
            )
        for event in [HookEvent.ON_USER_INPUT, HookEvent.ON_AGENT_START, HookEvent.ON_AGENT_END,
                      HookEvent.ON_ERROR, HookEvent.ON_TOOL_SELECT, HookEvent.ON_TOOL_EXECUTE]:
            hook_manager.register(event, log_hook, priority=1)

    async def error_handler(event, error, context):
        OutputFormatter.error(
            f"Hook error in {event.value}: {error.__class__.__name__}: {str(error)}"
        )
    hook_manager.register_error_handler(error_handler)


async def _load_user_hooks(hook_manager: HookManager, verbose: bool = False) -> None:
    loader = HookConfigLoader()
    try:
        stats = await loader.load_hooks(hook_manager, skip_errors=True)
        if stats["loaded_files"] > 0:
            OutputFormatter.success(
                f"Loaded {stats['registered_handlers']} user hooks from "
                f"{stats['loaded_files']} config file(s)"
            )
    except Exception as e:
        OutputFormatter.warning(f"Error loading user hooks: {e}")


async def _setup_event_listeners(event_bus: EventBus):
    async def on_tool_selected(event: Event):
        tool_name = event.data.get("tool_name", "Unknown")
        brief_description = event.data.get("brief_description", "")
        OutputFormatter.info(f"🔧 Using {tool_name}: {brief_description}")

    async def on_tool_completed(event: Event):
        tool_name = event.data.get("tool_name", "Unknown")
        OutputFormatter.success(f"✓ {tool_name} completed")

    async def on_tool_error(event: Event):
        tool_name = event.data.get("tool_name", "Unknown")
        error = event.data.get("error", "Unknown error")
        error_type = event.data.get("error_type", "")
        if error_type == "permission_denied":
            OutputFormatter.warning(f"⛔ Permission denied: {error}")
        else:
            OutputFormatter.error(f"❌ {tool_name} failed: {error}")

    async def on_agent_thinking(event: Event):
        if event.data.get("turn", 1) == 1:
            OutputFormatter.info("💭 Thinking...")

    async def on_agent_error(event: Event):
        error = event.data.get("error", "Unknown error")
        OutputFormatter.error(f"❌ Agent error: {error}")

    event_bus.subscribe(EventType.TOOL_SELECTED, on_tool_selected)
    event_bus.subscribe(EventType.TOOL_COMPLETED, on_tool_completed)
    event_bus.subscribe(EventType.TOOL_ERROR, on_tool_error)
    event_bus.subscribe(EventType.AGENT_THINKING, on_agent_thinking)
    event_bus.subscribe(EventType.AGENT_ERROR, on_agent_error)
