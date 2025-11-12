# User Hook Configuration Guide

This directory contains user-defined hook configurations for tiny-claude.

## Configuration Files

The system loads hook configurations from multiple locations in the following priority order:

1. **User Global** (highest priority): `~/.tiny-claude/settings.json`
   - Hooks apply to all tiny-claude projects on this machine
   - Recommended for personal/system-wide hooks

2. **Project Level**: `.tiny-claude/settings.json`
   - Hooks apply only to this project
   - Checked into version control

3. **Local Level** (lowest priority): `.tiny-claude/settings.local.json`
   - Hooks apply only to this machine for this project
   - NOT checked into version control (add to .gitignore)

## Quick Start

### Step 1: Create Your Hook Module

Create a Python file with your hook handlers:

```python
# my_hooks.py
async def on_tool_execute(context):
    print(f"Tool: {context.data['tool_name']}")
```

### Step 2: Create Configuration File

Create `.tiny-claude/settings.json`:

```json
{
  "hooks": {
    "custom_handlers": [
      {
        "event": "tool.execute",
        "handler": "my_hooks:on_tool_execute",
        "priority": 50,
        "enabled": true
      }
    ]
  }
}
```

### Step 3: Run tiny-claude

Your hooks will be automatically loaded when the application starts!

```bash
python -m src.main --verbose
```

## Configuration Format

Each handler configuration requires:

- **event** (required): Hook event name (e.g., `"tool.execute"`)
- **handler** (required): Module and function path (e.g., `"my_hooks:on_tool_execute"`)
- **priority** (optional): Execution priority (default: 0, higher = earlier)
  - Range: -1000 to 1000
  - System hooks typically use priority 1
  - User hooks should use priority 50-100+

- **enabled** (optional): Whether to load this handler (default: true)

## Available Hook Events

See [Phase 1 Documentation](../../docs/evolution/phase-1-hooks.md) for complete list:

- `user.input` - User provides input
- `agent.start` - Agent starts processing
- `agent.thinking` - Before LLM call
- `tool.select` - Tool is selected
- `permission.check` - Permission check
- `tool.execute` - Tool execution starts
- `tool.result` - Tool succeeds
- `tool.error` - Tool fails
- `agent.end` - Agent completes
- `system.error` - System error occurs
- `system.shutdown` - Application shutting down

## Example: Logging Hook

```python
# my_logging_hooks.py
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def log_tool_execution(context):
    """Log tool executions"""
    tool_name = context.data['tool_name']
    logger.info(f"Tool executed: {tool_name} at {datetime.now()}")
```

Configuration:
```json
{
  "hooks": {
    "custom_handlers": [
      {
        "event": "tool.execute",
        "handler": "my_logging_hooks:log_tool_execution",
        "priority": 50,
        "enabled": true
      }
    ]
  }
}
```

## Security Considerations

The hook loading system includes security measures:

### Forbidden Modules
Cannot import from: `os`, `sys`, `subprocess`, `socket`, `threading`, `__import__`, etc.

### Forbidden Functions
Cannot call: `eval`, `exec`, `compile`, `open`, etc.

### Validation
- Handler paths are validated (format: `module:function`)
- Private functions (starting with `_`) are blocked
- Code is audited using AST parsing
- Handler caching prevents repeated loading

### Best Practices
1. Keep hooks simple and focused
2. Use async functions (though sync functions work too)
3. Handle exceptions gracefully
4. Don't access files directly (use tools instead)
5. Log important information, not everything

## Troubleshooting

### Hook Not Loading

Check the application output for loading messages:

```bash
python -m src.main --verbose
```

Look for lines like:
- `✅ Loaded N user hooks from X config file(s)` - Success
- `⚠️ Failed to load hooks from...` - Load error

### Handler Function Not Found

Make sure:
- Module is in Python path (current directory works)
- Function name matches exactly (case-sensitive)
- Format is `module:function` with colon separator

### Module Not Allowed

If you get "Forbidden module" error:
- Hook system blocks dangerous modules by design
- Use safe alternatives instead
- Use built-in tiny-claude tools for file operations

### Async/Await Issues

All hooks should be `async` functions:

```python
# ✅ Correct
async def my_hook(context):
    pass

# ❌ Wrong (will cause error)
def my_hook(context):
    pass
```

## Examples

See:
- `example_hooks.py` - Complete example with many hook types
- `settings.example.json` - Example configuration file

## Testing Your Hooks

To verify hooks are loaded:

```bash
# Verbose mode shows loaded hooks
python -m src.main --verbose
```

Look for:
- "Loaded N user hooks"
- "Hook:" messages showing active hooks

## Further Reading

- [Phase 1: Global Hooks System](../../docs/evolution/phase-1-hooks.md)
- [Hook Event Types](../../docs/evolution/phase-1-hooks.md#hook-event-types)
- [Hook API Reference](../../docs/api.md)
