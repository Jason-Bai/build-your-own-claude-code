# Feature: Extensible Custom Commands Framework

**Version**: `v0.0.1`
**Feature ID**: `p9-extensible-commands`
**Author**: Gemini

## 1. Overview

This document describes an extensible command framework that allows users to add custom commands by creating simple Markdown (`.md`) files in a designated directory. These custom commands will seamlessly integrate with existing built-in Python commands, providing a unified, powerful, and highly customizable interactive experience.

## 2. Core Goals

*   **Extensibility**: Users should be able to easily create and share their own commands without modifying core application code.
*   **Ease of Use**: Utilizing simple Markdown files as the command definition format lowers the barrier to entry for creating new commands.
*   **Uniformity**: Custom commands and built-in commands should be indistinguishable to the user in terms of discovery (autocomplete) and execution.
*   **Power**: Custom commands should leverage the underlying LLM's reasoning capabilities and existing core tools (e.g., `shell` tool) to execute complex tasks.

## 3. Detailed Design

### 3.1. Command Specification

All custom commands must be Markdown files located in the `~/.tiny-claude-code/commands/` directory.

*   **Command Name**: The callable name of the command is derived directly from its filename (without the `.md` extension), prefixed with a `/`.
    *   `commit.md` -> `/commit`
    *   `run-tests.md` -> `/run-tests`
*   **File Structure**: The `.md` file should contain the following sections to guide the LLM's behavior and provide user information.
    *   **`# Claude Command: <DisplayName>` (Required)**: Defines the human-readable display name for the command.
    *   **`## Usage` (Required)**: Describes how the command is invoked and any parameters it accepts. This serves as a quick reference for both the user and the LLM.
    *   **`## What This Command Does` (Required)**: A detailed description of the command's functionality. This is the core content used to construct the LLM's "meta-task" instruction.
    *   **`## Best Practices / Guidelines` (Optional)**: Provides additional context, rules, or constraints to help the LLM execute the task more effectively.
    *   **`## Command Options` (Optional)**: Details any specific parameters or flags the command supports.

### 3.2. Command Loading and Registration

The system will maintain a unified **Command Registry** to manage all available commands.

1.  **Startup Process**:
    *   Upon application startup, an empty "Command Registry" is initialized.
    *   **Load Built-in Commands**: The application scans the `src/commands/` directory, instantiates all Python-based command classes, and registers them into the Command Registry.
    *   **Load Custom Commands**:
        *   The application checks for the existence of the `~/.tiny-claude-code/commands/` directory.
        *   If the directory exists, it iterates through all `.md` files within it.
        *   For each `.md` file, a `MarkdownCommand` instance (a new, generic command class) is created.
        *   The `MarkdownCommand` object stores the command name (derived from the filename), its file path, and its parsed core content.
        *   This `MarkdownCommand` instance is then registered into the same Command Registry.

### 3.3. Interaction and Execution

1.  **Discovery**:
    *   When the user types `/` in the prompt, the autocompletion system queries the Command Registry.
    *   It retrieves the names of all registered commands (both Python and Markdown-defined) and displays them in the autocompletion list.

2.  **Execution**:
    *   When a user executes a command (e.g., `/commit --no-verify`), the command dispatcher looks up the command in the registry.
    *   **If a Python Command is Found**: Its `execute` method is directly invoked.
    *   **If a `MarkdownCommand` is Found**:
        a.  A generic **Markdown Command Executor** is triggered.
        b.  The executor reads the content of the corresponding `.md` file (e.g., `commit.md`).
        c.  **Construct Meta-Task Instruction**: It combines the `.md` file's content (especially sections like `## What This Command Does` and `## Best Practices / Guidelines`) with any user-provided arguments (e.g., `--no-verify`) to form a detailed, context-rich instruction for the LLM.
        d.  **LLM Reasoning and Tool Invocation**: The LLM receives this "meta-task." It then breaks down the task into sub-tasks and, to accomplish these, decides to invoke one or more of the existing base tools (most commonly the `shell` tool, for executing commands like `git status`, `pnpm lint`, etc.).
        e.  **Result Handling**: The application captures the results of the tool executions and presents them to the user.

#### **Key Insight on Execution Environment**:

Custom commands primarily leverage the LLM's ability to reason and generate appropriate calls to **existing base tools** (like the `shell` tool). We do not need to create specific tools for `git`, `python`, `node`, etc. The `shell` tool acts as a universal gateway for the LLM to interact with the underlying operating system and execute any command-line program installed on it.

## 4. Verification Plan

1.  **Create a Custom Command**: In the `~/.tiny-claude-code/commands/` directory, create a file named `test-ls.md` with content that instructs the LLM to list files in the current directory (e.g., using `ls -l`).
2.  **Verify Loading**: Start the application (`python -m src.main`). In the prompt, type `/` and observe if `/test-ls` appears in the autocompletion list.
3.  **Verify Execution**:
    *   Execute `/test-ls` in the terminal.
    *   **Expected Behavior**:
        *   The application should display a "Thinking..." or similar status indicator.
        *   Subsequently, a dynamic tool output panel should appear.
        *   The panel should indicate that the `shell` tool was invoked, with parameters similar to `ls -l`.
        *   The results of the `ls -l` command should stream in real-time within the panel.
        *   Upon completion, the panel should update with a success status.

## 5. Summary of Benefits

*   **Empowered Users**: Users gain significant control over extending the agent's capabilities.
*   **Simplified Customization**: Markdown-based definitions make command creation accessible.
*   **Seamless Integration**: Custom commands feel like native features.
*   **Leveraged LLM Intelligence**: The LLM's reasoning is used to interpret and execute complex custom tasks.
*   **Future-Proof**: The framework is designed to easily incorporate new base tools as they are developed.
