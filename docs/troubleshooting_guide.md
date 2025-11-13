# Troubleshooting Guide

This document contains diagnostics and solutions for common issues.

## Table of Contents

- [Installation and Configuration](#installation-and-configuration)
- [API and Network](#api-and-network)
- [Input and Output](#input-and-output)
- [Tool Execution](#tool-execution)
- [MCP and Hooks](#mcp-and-hooks)
- [Asynchronous and Concurrency](#asynchronous-and-concurrency)
- [Files and Permissions](#files-and-permissions)
- [Performance Issues](#performance-issues)

---

## Installation and Configuration

### Issue: ImportError - Module Not Found

**Symptoms**:
```
ModuleNotFoundError: No module named 'anthropic'
```

**Cause**: Dependencies are not installed or Python path is misconfigured

**Solution**:
1. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure you are running in a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Check Python version (requires 3.10+):
   ```bash
   python --version
   ```

---

### Issue: Configuration File Loading Failure

**Symptoms**:
```
Error loading config file: config.json not found
```

**Cause**: Configuration file path is incorrect or file format is invalid

**Solution**:
1. Ensure `config.json` is in the project root directory
2. Validate JSON format:
   ```bash
   python -m json.tool config.json
   ```

3. Use a valid configuration template:
   ```json
   {
     "model": {
       "provider": "anthropic",
       "ANTHROPIC_API_KEY": "your-key",
       "ANTHROPIC_MODEL": "claude-sonnet-4-5-20250929"
     },
     "ui": {
       "output_level": "normal"
     }
   }
   ```

---

## API and Network

### Issue: No API Provider Configured

**Symptoms**:
```
RuntimeError: No API provider configured
```

**Cause**: API key is not set or provider configuration is incorrect

**Solution**:

Configure the API key using one of the following methods (in order of priority):

**Method 1: Environment Variables (Recommended)**
```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
export ANTHROPIC_MODEL="claude-sonnet-4-5-20250929"  # Optional

python -m src.main
```

**Method 2: .env File**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add:
ANTHROPIC_API_KEY=your-key
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

**Method 3: config.json**
```json
{
  "model": {
    "provider": "anthropic",
    "ANTHROPIC_API_KEY": "your-key"
  }
}
```

**Verify Configuration**:
```bash
python -m src.main --verbose
# Output should display "Model loaded: claude-sonnet-4-5-20250929"
```

---

### Issue: API Connection Timeout

**Symptoms**:
```
TimeoutError: Request to API timed out after 30 seconds
```

**Cause**: Slow network connection or slow API service response

**Solution**:
1. Check network connectivity:
   ```bash
   ping api.anthropic.com
   ```

2. Check your API quota in the Anthropic dashboard

3. Retry the request (the system will automatically retry)

4. Increase timeout duration in `config.json` (if supported):
   ```json
   {
     "timeout_seconds": 60
   }
   ```

---

### Issue: API Returns 401 Unauthorized

**Symptoms**:
```
APIError: 401 Unauthorized - Invalid API key
```

**Cause**: Incorrect or expired API key

**Solution**:
1. Verify that the API key is copied correctly (check for extra spaces)
2. Regenerate the API key from the Anthropic dashboard
3. Update environment variables or configuration file
4. Restart the application

---

## Input and Output

### Issue: Command Autocomplete Not Working

**Symptoms**:
- Tab key does not respond
- Autocomplete displays incorrect commands
- "/" prefix is removed

**Cause**: Prompt-Toolkit configuration or CommandCompleter issue

**Solution**:
1. Ensure input starts with "/" (for example, `/he<TAB>` rather than `he<TAB>`)

2. Check details using verbose mode:
   ```bash
   python -m src.main --verbose
   # Look for information related to "CommandCompleter"
   ```

3. Try restarting the application

4. Check the fix record: [hotfixes/v2025.01.13/2-fix-tab-autocomplete.md](./hotfixes/v2025.01.13/2-fix-tab-autocomplete.md)

---

### Issue: Markdown Not Rendering

**Symptoms**:
- Output displays raw Markdown syntax
- Code blocks are not highlighted
- Tables display as text

**Cause**: Rich library configuration or output level is not suitable

**Solution**:
1. Check the output level:
   ```bash
   # In the application, run:
   /status  # Check "Output level"
   ```

2. Ensure output level is set to "normal" (not "quiet"):
   ```bash
   /quiet off
   ```

3. Verify that the Rich library is installed correctly:
   ```bash
   pip show rich
   ```

4. Try restarting the application

---

### Issue: Colors and Styles Display Incorrectly

**Symptoms**:
- Output displays only color codes
- Terminal shows strange characters
- Styling is inconsistent

**Cause**: Terminal does not support ANSI colors or environment variable configuration issue

**Solution**:
1. Check if your terminal supports colors (most modern terminals do)

2. Disable colors in `config.json` (if needed):
   ```json
   {
     "ui": {
       "no_color": true
     }
   }
   ```

3. For Windows, use Windows Terminal or enable ANSI support

4. For SSH sessions, ensure you are using the `-X` or `-Y` flag (if needed)

---

## Tool Execution

### Issue: Tool Execution Permission Denied

**Symptoms**:
```
PermissionError: Operation not permitted
```

**Cause**: Tool is rejected by the permission system or insufficient file/directory permissions

**Solution**:
1. Check the permission level:
   ```bash
   /status  # Check permission settings
   ```

2. For tools with NORMAL permissions, confirm the confirmation prompt in the conversation

3. Check file/directory permissions:
   ```bash
   # For file operation tools
   ls -la /path/to/file
   chmod 644 /path/to/file  # If needed
   ```

4. Run the application with the appropriate flag:
   ```bash
   # For testing or trusted environments only
   python -m src.main --auto-approve-all
   ```

---

### Issue: Tool Execution Timeout

**Symptoms**:
```
TimeoutError: Tool execution timed out after 30 seconds
```

**Cause**: Tool execution takes too long or program is hung

**Solution**:
1. Check for background processes consuming resources

2. Try restarting the application

3. For long-running commands, increase timeout duration (configure in `config.json` if supported)

4. Try simplifying the command or breaking it into multiple steps

---

### Issue: File Operation Tool Cannot Find File

**Symptoms**:
```
FileNotFoundError: [Errno 2] No such file or directory
```

**Cause**: File path is incorrect or file does not exist

**Solution**:
1. Verify the file path is correct (using absolute paths is more reliable)

2. Use the Glob tool to find files:
   ```bash
   # Ask the Agent in the conversation
   # "find all .py files in src/"
   ```

3. Check the current working directory:
   ```bash
   # The Agent will display the working directory
   /status
   ```

4. Ensure file permissions allow reading:
   ```bash
   ls -la /path/to/file
   ```

---

### Issue: Bash Tool Returns Error Exit Code

**Symptoms**:
```
Command failed with exit code 1
```

**Cause**: The executed command encountered an error

**Solution**:
1. Check the complete error message (use the `--verbose` flag)

2. Run the command directly in terminal to verify:
   ```bash
   # Copy the command and run it in the terminal
   your-command-here
   ```

3. Check if command dependencies are installed

4. Verify command permissions and ownership

---

## MCP and Hooks

### Issue: MCP Server Cannot Load

**Symptoms**:
```
Error loading MCP servers
RuntimeError: Failed to start MCP server: filesystem
```

**Cause**: MCP server configuration is incorrect or dependencies are missing

**Solution**:
1. Check if MCP is installed:
   ```bash
   pip install mcp
   ```

2. Verify MCP configuration in `config.json`:
   ```json
   {
     "mcp_servers": [
       {
         "name": "filesystem",
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
         "enabled": true
       }
     ]
   }
   ```

3. Check if Node.js is installed (for npx):
   ```bash
   node --version
   npm --version
   ```

4. Test the MCP server manually:
   ```bash
   npx @modelcontextprotocol/server-filesystem .
   ```

5. Use the `--verbose` flag to see detailed errors:
   ```bash
   python -m src.main --verbose
   ```

---

### Issue: Hook Not Executing

**Symptoms**:
- Hook is configured in settings.json but not executing
- Specific event does not trigger the hook

**Cause**: Hook configuration is incorrect or event name does not match

**Solution**:
1. Verify the hook configuration file location:
   - Global: `~/.tiny-claude/settings.json`
   - Project: `.tiny-claude/settings.json`
   - Local: `.tiny-claude/settings.local.json` (gitignored)

2. Check JSON format of hook configuration:
   ```bash
   python -m json.tool ~/.tiny-claude/settings.json
   ```

3. Verify event name is correct (e.g., `on_tool_execute`, `on_message_received`)

4. Check if hook command is executable:
   ```bash
   # If it is a shell command
   bash -c "your-command"

   # If it is Python code
   python -c "your-code"
   ```

5. Check logs or use `--verbose` mode for debugging

---

### Issue: Hook Loading Exception

**Symptoms**:
```
Error loading hooks: Invalid hook configuration
SyntaxError: invalid syntax in hook code
```

**Cause**: Hook configuration or code has syntax error

**Solution**:
1. Check JSON format of hook configuration

2. If using Python code, verify the syntax:
   ```bash
   python -m py_compile your-hook-code.py
   ```

3. Use a JSON validation tool to check configuration

4. Start with a simple hook for testing:
   ```json
   {
     "hooks": [
       {
         "event": "on_tool_execute",
         "type": "command",
         "command": "echo 'Test Hook'",
         "priority": 10
       }
     ]
   }
   ```

---

## Asynchronous and Concurrency

### Issue: asyncio Event Loop Conflict

**Symptoms**:
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**Cause**: Attempting to create a new event loop while another is already running

**Solution**:
1. Ensure you are using the async method `async_get_input()` instead of the synchronous `get_input()`

2. Check the fix record: [hotfixes/v2025.01.13/1-fix-asyncio-loop.md](./hotfixes/v2025.01.13/1-fix-asyncio-loop.md)

3. If encountering this error in your own code, check if an event loop is already running:
   ```python
   import asyncio

   # Do not use:
   # asyncio.run(your_async_function())

   # Should use:
   try:
       loop = asyncio.get_running_loop()
   except RuntimeError:
       loop = asyncio.new_event_loop()
       asyncio.set_event_loop(loop)

   loop.run_until_complete(your_async_function())
   ```

---

## Files and Permissions

### Issue: Cannot Create History File

**Symptoms**:
```
PermissionError: [Errno 13] Permission denied: '~/.cache/tiny_claude_code/'
```

**Cause**: Missing directory permissions or parent directory does not exist

**Solution**:
1. Create the cache directory:
   ```bash
   mkdir -p ~/.cache/tiny_claude_code/
   ```

2. Check permissions:
   ```bash
   ls -ld ~/.cache/tiny_claude_code/
   chmod 755 ~/.cache/tiny_claude_code/
   ```

3. Ensure write permissions:
   ```bash
   touch ~/.cache/tiny_claude_code/.tiny_claude_code_history
   chmod 644 ~/.cache/tiny_claude_code/.tiny_claude_code_history
   ```

---

### Issue: CLAUDE.md Initialization Failure

**Symptoms**:
```
Error initializing CLAUDE.md
FileExistsError: CLAUDE.md already exists
```

**Cause**: CLAUDE.md file already exists

**Solution**:
1. If you want to update the existing CLAUDE.md, edit it manually or delete it and reinitialize:
   ```bash
   # Delete existing file
   rm CLAUDE.md

   # In the application, run:
   /init
   ```

2. If you want to keep the existing file, skip initialization

---

## Performance Issues

### Issue: Application Response Slow

**Symptoms**:
- Input lag
- Slow output rendering
- High CPU usage

**Cause**: Context window is too large, tool output is huge, or insufficient system resources

**Solution**:
1. Check context window size:
   ```bash
   /status  # Check "Context: XXXX/8000 tokens"
   ```

2. Clear old conversations:
   ```bash
   /clear  # Clear current conversation
   ```

3. Check the task list:
   ```bash
   /todos
   ```

4. Disable unnecessary MCP servers (set `"enabled": false` in `config.json`)

5. Reduce history line count (adjust in configuration if supported)

---

### Issue: High Memory Usage

**Symptoms**:
- Memory usage continues to increase
- Application becomes unresponsive
- Overall system becomes slow

**Cause**: Memory leak or large message history

**Solution**:
1. Restart the application (fully clears memory)

2. Use `/clear` to clear conversation history

3. Save current session and then restart:
   ```bash
   /save important-session
   /exit
   python -m src.main
   ```

4. Check for infinite loop hooks (if custom hooks are defined)

---

## Still Having Issues?

If the above solutions do not resolve your issue:

1. Check detailed logs:
   ```bash
   python -m src.main --verbose
   ```

2. Check related documentation:
   - [README.md](../README.md) - Project overview
   - [architecture_guide.md](./architecture_guide.md) - System architecture
   - [development_guide.md](./development_guide.md) - Development guide

3. Check [GitHub Issues](https://github.com/your-username/build-your-own-claude-code/issues)

4. Create a new issue and include:
   - Python version and operating system
   - Complete error message and stack trace
   - Steps to reproduce the issue

---

**Last Updated**: 2025-01-13