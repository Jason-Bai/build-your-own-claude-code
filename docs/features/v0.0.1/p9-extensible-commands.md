# Feature: Extensible Custom Commands Framework

**Version**: `v0.0.1`
**Feature ID**: `p9-extensible-commands`
**Author**: Gemini

## 1. Overview

This document describes an extensible command framework that allows users to add custom commands by creating simple Markdown (`.md`) files in a designated directory. These custom commands will seamlessly integrate with existing built-in Python commands, providing a unified, powerful, and highly customizable interactive experience.

## 2. Core Goals

- **Extensibility**: Users should be able to easily create and share their own commands without modifying core application code.
- **Ease of Use**: Utilizing simple Markdown files as the command definition format lowers the barrier to entry for creating new commands.
- **Uniformity**: Custom commands and built-in commands should be indistinguishable to the user in terms of discovery (autocomplete) and execution.
- **Power**: Custom commands should leverage the underlying LLM's reasoning capabilities and existing core tools (e.g., `shell` tool) to execute complex tasks.

## 3. Detailed Design

### 3.1. Command Specification

All custom commands must be Markdown files located in the `~/.tiny-claude-code/commands/` directory.

- **Command Name**: The callable name of the command is derived directly from its filename (without the `.md` extension), prefixed with a `/`.
  - `commit.md` -> `/commit`
  - `run-tests.md` -> `/run-tests`
- **File Structure**: The `.md` file should contain the following sections to guide the LLM's behavior and provide user information.
  - **`# Claude Command: <DisplayName>` (Required)**: Defines the human-readable display name for the command.
  - **`## Usage` (Required)**: Describes how the command is invoked and any parameters it accepts. This serves as a quick reference for both the user and the LLM.
  - **`## What This Command Does` (Required)**: A detailed description of the command's functionality. This is the core content used to construct the LLM's "meta-task" instruction.
  - **`## Best Practices / Guidelines` (Optional)**: Provides additional context, rules, or constraints to help the LLM execute the task more effectively.
  - **`## Command Options` (Optional)**: Details any specific parameters or flags the command supports.

### 3.2. Command Loading and Registration

The system will maintain a unified **Command Registry** to manage all available commands.

1.  **Startup Process**:
    - Upon application startup, an empty "Command Registry" is initialized.
    - **Load Built-in Commands**: The application scans the `src/commands/` directory, instantiates all Python-based command classes, and registers them into the Command Registry.
    - **Load Custom Commands**:
      - The application checks for the existence of the `~/.tiny-claude-code/commands/` directory.
      - If the directory exists, it iterates through all `.md` files within it.
      - For each `.md` file, a `MarkdownCommand` instance (a new, generic command class) is created.
      - The `MarkdownCommand` object stores the command name (derived from the filename), its file path, and its parsed core content.
      - This `MarkdownCommand` instance is then registered into the same Command Registry.

### 3.3. Interaction and Execution

1.  **Discovery**:

    - When the user types `/` in the prompt, the autocompletion system queries the Command Registry.
    - It retrieves the names of all registered commands (both Python and Markdown-defined) and displays them in the autocompletion list.

2.  **Execution**:
    - When a user executes a command (e.g., `/commit --no-verify`), the command dispatcher looks up the command in the registry.
    - **If a Python Command is Found**: Its `execute` method is directly invoked.
    - **If a `MarkdownCommand` is Found**:
      a. A generic **Markdown Command Executor** is triggered.
      b. The executor reads the content of the corresponding `.md` file (e.g., `commit.md`).
      c. **Construct Meta-Task Instruction**: It combines the `.md` file's content (especially sections like `## What This Command Does` and `## Best Practices / Guidelines`) with any user-provided arguments (e.g., `--no-verify`) to form a detailed, context-rich instruction for the LLM.
      d. **LLM Reasoning and Tool Invocation**: The LLM receives this "meta-task." It then breaks down the task into sub-tasks and, to accomplish these, decides to invoke one or more of the existing base tools (most commonly the `shell` tool, for executing commands like `git status`, `pnpm lint`, etc.).
      e. **Result Handling**: The application captures the results of the tool executions and presents them to the user.

#### **Key Insight on Execution Environment**:

Custom commands primarily leverage the LLM's ability to reason and generate appropriate calls to **existing base tools** (like the `shell` tool). We do not need to create specific tools for `git`, `python`, `node`, etc. The `shell` tool acts as a universal gateway for the LLM to interact with the underlying operating system and execute any command-line program installed on it.

### 3.4. Command Management & Builder (New)

To lower the barrier to entry and ensure command quality, a built-in **Command Management Suite** will be introduced.

#### 3.4.1. The `/command` Entry Point

A new built-in command `/command` will serve as the central hub for managing custom commands.

- **`/command new`**: Starts the interactive **Command Builder Wizard**.
- **`/command validate <file_path>`**: Validates a specific command file against the schema and security rules.
- **`/command export <command_name>`**: Exports a command as a shareable template.

#### 3.4.2. Interactive Command Builder (`/command new`)

This interactive wizard guides users through creating a robust command without needing to manually write Markdown or YAML.

**Workflow**:

1.  **Select Template**: User chooses from pre-set templates (e.g., "Basic Shell Command", "File Analysis", "Git Workflow", "Empty").
2.  **Metadata Input**: System prompts for:
    - Command Name (e.g., `deploy`)
    - Description
    - Permission Level (Safe/Normal/Dangerous)
3.  **Logic Definition**:
    - _For Shell Commands_: Prompts for the base command (e.g., `kubectl apply -f ...`).
    - _For Complex Logic_: Prompts for the "Goal" and "Context" (e.g., "Analyze the current file for security flaws").
4.  **Argument Configuration**: Interactive definition of accepted arguments (e.g., "Does this command accept a `--dry-run` flag?").
5.  **Preview & Save**: Generates the `.md` file with proper YAML Front Matter and saves it to `~/.tiny-claude-code/commands/`.

#### 3.4.3. Command Templates

Templates are "skeleton" Markdown files with placeholders.

**Example Template (Git Workflow)**:

```markdown
---
name: { { name } }
description: { { description } }
permission: normal
usage: /{{name}} [args]
---

# Goal

Perform the following git operation: {{git_operation}}

# Rules

- Always run `git status` first.
- If `{{safety_check}}` is true, ask for confirmation.
```

### 3.5. Security & Validation (New)

#### 3.5.1. Validation Logic

The system will enforce a strict schema for custom commands:

1.  **YAML Front Matter Check**: Must contain `name`, `description`, and valid `permission`.
2.  **Structure Check**: Must contain required Markdown sections (e.g., `# Goal` or `# What This Command Does`).
3.  **Syntax Check**: Verifies that placeholders and arguments are correctly formatted.

#### 3.5.2. Import Verification

When a user manually adds a file or imports a command:

1.  **Auto-Validation**: The system runs `/command validate` on the new file.
2.  **Safety Warning**: If the command is marked as `dangerous` or contains suspicious keywords (e.g., `rm -rf`, `sudo`), the user must explicitly approve it before first use.

## 4. Verification Plan

1.  **Verify Command Builder (`/command new`)**:

    - Run `/command new`.
    - Follow the wizard to create a simple "Hello World" command (e.g., `echo "Hello"`).
    - Verify that a valid `.md` file is created in `~/.tiny-claude-code/commands/` with the correct YAML Front Matter.

2.  **Verify Validation (`/command validate`)**:

    - Create a malformed `.md` file (missing Front Matter).
    - Run `/command validate <path_to_malformed_file>`.
    - Expected: Error message detailing missing fields.
    - Run `/command validate` on the file created in step 1.
    - Expected: Success message.

3.  **Verify Execution**:

    - Execute the command created in step 1 (e.g., `/hello`).
    - **Expected Behavior**:
      - The application should display a "Thinking..." or similar status indicator.
      - Subsequently, a dynamic tool output panel should appear.
      - The panel should indicate that the `shell` tool was invoked.
      - The results should stream in real-time.
      - Upon completion, the panel should update with a success status.

4.  **Create a Custom Command**: In the `~/.tiny-claude-code/commands/` directory, create a file named `test-ls.md` with content that instructs the LLM to list files in the current directory (e.g., using `ls -l`).
5.  **Verify Loading**: Start the application (`python -m src.main`). In the prompt, type `/` and observe if `/test-ls` appears in the autocompletion list.
6.  **Verify Execution**:
    - Execute `/test-ls` in the terminal.
    - **Expected Behavior**:
      - The application should display a "Thinking..." or similar status indicator.
      - Subsequently, a dynamic tool output panel should appear.
      - The panel should indicate that the `shell` tool was invoked, with parameters similar to `ls -l`.
      - The results of the `ls -l` command should stream in real-time within the panel.
      - Upon completion, the panel should update with a success status.

## 5. Summary of Benefits

- **Empowered Users**: Users gain significant control over extending the agent's capabilities.
- **Simplified Customization**: Markdown-based definitions make command creation accessible.
- **Seamless Integration**: Custom commands feel like native features.
- **Leveraged LLM Intelligence**: The LLM's reasoning is used to interpret and execute complex custom tasks.
- **Future-Proof**: The framework is designed to easily incorporate new base tools as they are developed.
