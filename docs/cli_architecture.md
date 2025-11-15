# CLI Entry Point Consolidation

## Overview

The application now uses a clean, modular entry point architecture where `src/cli/main.py` is the single source of truth for the CLI application.

## Architecture

### Entry Point Flow

```
python -m src.main          → src/main.py → src/cli/main.py
python -m src               → src/__main__.py → src/cli/main.py
```

Both entry points delegate to `src/cli/main.py::cli()`.

### Module Structure

**`src/cli/main.py`** - Main CLI orchestrator
- Handles command-line argument parsing (via `src/config/args`)
- Loads configuration (via `src/config/loader`)
- Initializes agent (via `src/initialization/setup`)
- Manages main REPL loop
- Handles welcome message and CLAUDE.md loading
- Manages auto-save and event listeners

**`src/config/loader.py`** - Configuration loading
- `load_config()` - Load from settings.json, .env, environment variables
- Supports priority: environment > .env > ~/.tiny-claude-code/settings.json

**`src/config/args.py`** - Command-line argument parsing
- `parse_args()` - Parse CLI flags (--verbose, --quiet, --config, etc.)

**`src/initialization/setup.py`** - Agent initialization
- `initialize_agent()` - Create and configure EnhancedAgent
- `_setup_hooks()` - Configure hook system
- `_load_user_hooks()` - Load user-defined hooks
- `_setup_event_listeners()` - Register event subscriptions
- `create_storage_from_config()` - Create persistence storage

**`src/main.py`** - Legacy entry point (deprecated)
- Now just delegates to `src/cli/main.py`
- Kept for backward compatibility
- Contains historical implementation (can be removed in future)

## Why This Architecture?

1. **Single Responsibility** - Each module has one clear purpose
2. **Testability** - Functions can be tested independently
3. **Reusability** - Config loading and agent initialization can be used elsewhere
4. **Maintainability** - Changes to CLI logic don't affect other concerns
5. **Clarity** - Entry point is simple and easy to understand

## Running the Application

All these commands run the same code:

```bash
# Method 1: Using src.main (traditional)
python -m src.main

# Method 2: Using src package __main__ (modern Python)
python -m src

# Method 3: Direct CLI execution
python src/cli/main.py
```

With options:

```bash
python -m src --verbose              # Show detailed output
python -m src --quiet                # Minimal output
python -m src --config custom.json   # Use custom config file
python -m src --help                 # Show help
```

## Future Improvements

1. Could remove `src/main.py` once migration is complete
2. Could add additional entry points for different interfaces (API server, batch processing, etc.)
3. Could split `src/cli/main.py` further if it grows too large

## Testing

✅ All 1080 unit tests pass with this architecture
✅ No behavioral changes - pure refactoring
✅ Backward compatible with existing entry points

## Status

**Status:** Complete and tested
**Migration:** Soft migration - old entry point still works
**Recommendation:** Update documentation to prefer `python -m src` going forward
