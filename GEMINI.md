# Project Overview

This project is a command-line AI coding assistant built with Python. It's designed with a modular and extensible architecture, allowing it to interact with the user's file system, execute commands, and leverage various language models.

The core of the application is the `EnhancedAgent`, which manages the agent's state, context, and tools. It uses a state machine to handle the lifecycle of a request, from user input to tool execution and final response. The agent is equipped with a set of tools for file operations (read, write, edit), command execution (bash), and file search (glob, grep).

The application supports multiple LLM providers, including Anthropic, OpenAI, and Google. It's configured through a `config.json` file, `.env` file, or environment variables.

## Building and Running

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Choose one of the following methods to configure your API key:

*   **Environment Variables (Recommended):**
    ```bash
    export ANTHROPIC_API_KEY="your-anthropic-key"
    ```
*   **.env File:**
    Copy `.env.example` to `.env` and add your API key.
*   **config.json:**
    Add your API key to the `model` section of the `config.json` file.

### 3. Run the Application

```bash
python -m src.main
```

### 4. Running Tests

The project includes a comprehensive test suite. To run the tests, use the following command:

```bash
pytest tests/unit/ -v
```

To view the test coverage report, run:

```bash
pytest tests/unit/ --cov=src --cov-report=html
```

## Development Conventions

The project follows standard Python development conventions. It uses `pytest` for testing and has a high level of test coverage. The code is organized into modules with clear responsibilities.

The `src` directory contains the main application logic, with subdirectories for agents, clients, commands, tools, and other components. The `tests` directory contains the test suite, with a structure that mirrors the `src` directory.

The project is designed to be extensible. New tools can be added by creating new classes that inherit from `BaseTool` and implementing the required methods. New commands can be added by creating new functions and registering them with the command registry.
