"""
Example User-Defined Hooks

This is an example file showing how to create custom hooks for tiny-claude.
Place this file or create your own hooks module and reference it in
.tiny-claude/settings.json

Example configuration:
{
  "hooks": {
    "custom_handlers": [
      {
        "event": "agent.start",
        "handler": "example_hooks:on_agent_start",
        "priority": 50,
        "enabled": true
      }
    ]
  }
}
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def on_agent_start(context):
    """Hook handler for agent startup

    This hook is called when the agent starts processing a request.

    Args:
        context: HookContext with event information
    """
    print(f"\n🚀 Agent started at {datetime.now().isoformat()}")
    print(f"   Request ID: {context.request_id}")
    print(f"   Agent ID: {context.agent_id}")
    print()


async def on_agent_end(context):
    """Hook handler for agent completion

    This hook is called when the agent finishes processing.

    Args:
        context: HookContext with event information
    """
    print(f"\n✅ Agent completed")
    print(f"   Request ID: {context.request_id}")
    print(f"   Success: {context.data.get('success', False)}")
    print()


async def on_tool_execute(context):
    """Hook handler for tool execution

    This hook is called when a tool is about to be executed.

    Args:
        context: HookContext with event information
    """
    tool_name = context.data.get('tool_name', 'unknown')
    print(f"\n🔧 Executing tool: {tool_name}")
    logger.debug(f"Tool input: {context.data.get('tool_input')}")


async def on_tool_result(context):
    """Hook handler for tool result

    This hook is called when a tool execution completes successfully.

    Args:
        context: HookContext with event information
    """
    tool_name = context.data.get('tool_name', 'unknown')
    print(f"\n📊 Tool result: {tool_name}")


async def on_tool_error(context):
    """Hook handler for tool error

    This hook is called when a tool execution fails.

    Args:
        context: HookContext with event information
    """
    tool_name = context.data.get('tool_name', 'unknown')
    error = context.data.get('error', 'unknown error')
    print(f"\n❌ Tool error: {tool_name}")
    print(f"   Error: {error}")
    logger.error(f"Tool {tool_name} failed: {error}")


async def on_error(context):
    """Hook handler for system errors

    This hook is called when an error occurs in the system.

    Args:
        context: HookContext with event information
    """
    error = context.data.get('error', 'unknown error')
    error_type = context.data.get('error_type', 'Exception')
    print(f"\n💥 System error occurred")
    print(f"   Type: {error_type}")
    print(f"   Message: {error}")
    logger.error(f"{error_type}: {error}")


async def on_permission_check(context):
    """Hook handler for permission checks

    This hook is called when a permission check is performed.

    Args:
        context: HookContext with event information
    """
    tool_name = context.data.get('tool_name', 'unknown')
    logger.info(f"Permission check for tool: {tool_name}")


async def on_user_input(context):
    """Hook handler for user input

    This hook is called when the user provides input.

    Args:
        context: HookContext with event information
    """
    user_input = context.data.get('input', '')
    logger.debug(f"User input received: {user_input[:100]}...")  # Log first 100 chars


# You can also create custom monitoring hooks
async def on_thinking(context):
    """Hook handler for agent thinking process

    This hook is called before the agent calls the LLM.

    Args:
        context: HookContext with event information
    """
    message_count = context.data.get('message_count', 0)
    tool_count = context.data.get('tool_count', 0)
    logger.debug(f"About to think with {message_count} messages and {tool_count} tools")


# Example: Custom metrics collection
class MetricsCollector:
    """Example custom metrics collector"""

    def __init__(self):
        self.start_time = None
        self.event_count = 0

    async def on_agent_start(self, context):
        """Start timing"""
        self.start_time = datetime.now()
        self.event_count = 0
        print("🎯 Starting metrics collection")

    async def on_agent_end(self, context):
        """Report metrics"""
        if self.start_time:
            duration = datetime.now() - self.start_time
            print(f"📈 Metrics Report:")
            print(f"   Duration: {duration.total_seconds():.2f}s")
            print(f"   Events processed: {self.event_count}")

    async def on_error(self, context):
        """Count errors"""
        self.event_count += 1


# Create instance if you want to use metrics collector
# metrics = MetricsCollector()
