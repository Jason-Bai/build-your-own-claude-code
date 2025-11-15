# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Phase 4: Advanced Agent Capabilities (In Progress)
- Performance Optimization and Token Compression
- Additional MCP Server Integration

---

## [1.1.0] - 2025-01-15

### Added
- **Moonshot Kimi Provider Support** ✅
  - Full Kimi API integration with tool calling support
  - Custom message formatting for Kimi's OpenAI-compatible API
  - Provider-specific tool result handling
  - Multi-turn conversation support verified

### Fixed
- **Kimi Tool Calling Issue** ✅
  - Fixed `tool_call_id is not found` error in multi-turn conversations
  - Implemented provider-aware message formatting in context manager
  - Added custom Kimi client with proper tool_use_id to tool_call_id conversion
  - 1055+ tests passing with Kimi integration

**Commits:**
- `ee668e7` - fix: Resolve Kimi tool calling failure by implementing provider-specific message handling

---

## [1.0.0] - 2025-01-13

### Added

#### Phase 1: Prompt-Toolkit Input Enhancement ✅
See: [docs/features/v0.0.1/p1-input-enhancement.md](./features/v0.0.1/p1-input-enhancement.md)

- **Intelligent Command Autocomplete**
  - CommandCompleter custom completer with "/" prefix support
  - Case-insensitive matching
  - Multi-line input support
  - Completion shortcut: Tab triggers autocomplete

- **History Management**
  - Persistent history to `~/.cache/tiny_claude_code/`
  - Up/Down keys for history navigation
  - Ctrl+R for history search
  - Cross-session history retention

- **Keyboard Shortcuts Support**
  - Ctrl+A/E: Start/End of line
  - Ctrl+K/U: Delete to end/start of line
  - Ctrl+W: Delete previous word
  - Alt+Enter: Multi-line editing
  - Mouse support: Selection, copy, paste

- **Asynchronous Compatibility**
  - async_get_input() method supports asyncio event loop
  - Seamless integration with main application event loop
  - Non-blocking user input

**Commits:**
- `1a81d61` - P1: Implement Prompt-Toolkit input enhancement
- `ff3f221` - Refactor: Rename src/utils/prompt_input.py to src/utils/input.py
- `0370ab7` - Fix: Add async support to PromptInputManager
- `2c8e340` - Fix: Implement smart command autocomplete

#### Phase 2: Rich Output Enhancement ✅
See: [docs/features/v0.0.1/p2-output-enhancement.md](./features/v0.0.1/p2-output-enhancement.md)

- **Colored Styled Output**
  - 6 predefined styles: Success (green), Error (red), Info (cyan), Warning (yellow), Thinking (dark magenta), Debug (dark gray)
  - Consistent style theme
  - Easily extensible style system

- **Markdown Auto-Rendering**
  - Automatic Markdown element detection
  - Intelligent rendering in Panels
  - Support for headings, lists, blockquotes, code blocks
  - Fallback output preserving original format

- **Code Syntax Highlighting**
  - Monokai theme
  - Line numbers and indentation guides
  - Multi-language support (Python, JavaScript, SQL, Bash, etc.)
  - Automatic language detection

- **Table and Panel Support**
  - Formatted table display
  - Styled Panel wrapping
  - Extensible layout
  - Border and title customization

**Commit:**
- `e697509` - P2: Enhance output with Rich library

#### Phase 3: Event-Driven Real-Time Feedback ✅
See: [docs/features/v0.0.1/p3-event-driven-feedback.md](./features/v0.0.1/p3-event-driven-feedback.md)

- **EventBus (Event Bus)**
  - Central event dispatcher
  - Publish-subscribe messaging
  - Asynchronous event handling
  - Event priority management
  - Event deduplication mechanism

- **Hook System**
  - Event-driven extensibility
  - Pre/Post tool execution hooks
  - Agent state change hooks
  - Message send/receive hooks
  - Secure Python code loading
  - AST validation and execution sandbox

- **Complete Event Flow**
  - Tool execution logging
  - Token usage tracking
  - State change notifications
  - Asynchronous event processing

- **Persistent Configuration**
  - Global configuration: `~/.tiny-claude/settings.json`
  - Project configuration: `.tiny-claude/settings.json`
  - Local configuration: `.tiny-claude/settings.local.json` (gitignored)

**Commit:**
- `1a17886` - P3: Implement Event-Driven Real-Time Feedback System

#### Project Documentation and Context
- **CLAUDE.md** - Detailed project technical background and structure
- **README.md** - Comprehensive project overview and quick start guide
- **docs/architecture_guide.md** - Detailed system architecture design
- **docs/development_guide.md** - Development workflow and contribution guidelines
- **docs/troubleshooting_guide.md** - Troubleshooting guide

### Fixed

#### asyncio Event Loop Conflict Resolution ✅
See: [hotfixes/v2025.01.13/1-fix-asyncio-loop.md](./hotfixes/v2025.01.13/1-fix-asyncio-loop.md)

- **Issue**: `asyncio.run() cannot be called from a running event loop`
- **Root Cause**: Prompt-Toolkit synchronous method creates new event loop in async context causing conflict
- **Resolution**: Implemented `async_get_input()` method using `session.prompt_async()`
- **Impact**: Phase 1 input enhancement features now function correctly in asynchronous context
- **Related Commit**: `0370ab7`

#### Tab Autocomplete "/" Prefix Issue Resolution ✅
See: [hotfixes/v2025.01.13/2-fix-tab-autocomplete.md](./hotfixes/v2025.01.13/2-fix-tab-autocomplete.md)

- **Issue**: NestedCompleter removes "/" prefix causing autocomplete failure
- **Symptoms**: Typing `/h<TAB>` completes to `help` instead of `/help`
- **Root Cause**: NestedCompleter assumes completions vocabulary does not contain prefix characters
- **Resolution**: Created custom CommandCompleter class that preserves "/" prefix
- **Impact**: All command autocompletions now correctly preserve "/" prefix
- **Related Commit**: `2c8e340`

### Changed

- Optimized input responsiveness, reduced latency
- Improved output formatting, enhanced readability
- Enhanced error message clarity
- Improved code comments and docstrings

### Known Issues

- OpenAI client integration in progress
- Certain terminals (such as IDLE) may not support full color and style support

---

## [0.9.0] - 2024-12-XX

### Added
- Initial project framework
- Base Agent implementation
- Anthropic Claude client integration
- Base tool system
- Conversation persistence

---

## Version Notes

### Version Numbering Scheme

- **Major Version**: Significant feature or API changes
- **Minor Version**: New features, backward compatible
- **Patch Version**: Bug fixes

### Release Cycle

- Regular updates with new features
- Timely release of critical fixes
- Maintain synchronized documentation

---

## Version History

For detailed information on specific versions, see:

- **Phase 1 Documentation**: [docs/features/v0.0.1/p1-input-enhancement.md](./features/v0.0.1/p1-input-enhancement.md)
- **Phase 2 Documentation**: [docs/features/v0.0.1/p2-output-enhancement.md](./features/v0.0.1/p2-output-enhancement.md)
- **Phase 3 Documentation**: [docs/features/v0.0.1/p3-event-driven-feedback.md](./features/v0.0.1/p3-event-driven-feedback.md)

---

## Fixes and Hotpatches

### 2025-01-13
- [v2025.01.13.1](./hotfixes/v2025.01.13/1-fix-asyncio-loop.md) - asyncio event loop conflict resolution
- [v2025.01.13.2](./hotfixes/v2025.01.13/2-fix-tab-autocomplete.md) - Tab autocomplete fix

For additional fixes, see: [docs/hotfixes/README.md](./hotfixes/README.md)

---

## Contributors

Thanks to all who have contributed to this project!

---

**Last Updated**: 2025-01-13

Have questions or suggestions? See [README.md](../README.md) or submit an Issue.