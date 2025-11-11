"""Workspace context management commands"""

import os
import subprocess
from pathlib import Path
from .base import Command, CLIContext


class InitCommand(Command):
    """初始化工作区，生成 CLAUDE.md"""

    name = "/init"
    description = "Initialize workspace with CLAUDE.md context file"

    async def execute(self, args: str, context: CLIContext) -> str:
        cwd = os.getcwd()
        claude_md_path = Path(cwd) / "CLAUDE.md"

        # 检查是否已存在
        if claude_md_path.exists():
            overwrite = input("CLAUDE.md already exists. Overwrite? [y/N]: ")
            if overwrite.lower() != 'y':
                return "✓ Initialization cancelled"

        # 分析目录结构
        print("📂 Analyzing project structure...")
        file_tree = self._get_file_tree(cwd)

        # 检测项目类型
        project_info = self._detect_project_type(cwd)

        # 生成 CLAUDE.md
        prompt = f"""Please analyze this project and create a CLAUDE.md file.

**Project Path:** {cwd}
**Project Type:** {project_info['type']}
**Key Files Found:** {', '.join(project_info['key_files'])}

**Directory Structure:**
```
{file_tree}
```

Create a comprehensive CLAUDE.md that includes:

1. **Project Overview** (2-3 sentences about what this project does)
2. **Structure** (explain the directory organization)
3. **Key Files** (list important files and their purposes)
4. **Technology Stack** (languages, frameworks, tools)
5. **Development Notes** (setup instructions, conventions)
6. **Common Tasks** (how to run, test, build)

Format it in clear markdown. Be concise but informative.
Use the Read tool to examine key files if needed.

After generating the content, use the Write tool to save it to: {claude_md_path}
"""

        # 使用 agent 生成
        await context.agent.run(prompt, verbose=False)

        if claude_md_path.exists():
            return f"✓ Workspace initialized: {claude_md_path}"
        else:
            return "❌ Failed to create CLAUDE.md"

    def _get_file_tree(self, path: str, max_depth: int = 3) -> str:
        """获取文件树"""
        try:
            result = subprocess.run(
                ["tree", "-L", str(max_depth), "-I", "node_modules|venv|__pycache__|.git|*.pyc"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout if result.returncode == 0 else self._simple_tree(path)
        except Exception:
            return self._simple_tree(path)

    def _simple_tree(self, path: str, max_depth: int = 2) -> str:
        """简单的目录树（fallback）"""
        lines = []
        path_obj = Path(path)

        def walk_dir(dir_path: Path, depth: int, prefix: str = ""):
            if depth > max_depth:
                return

            try:
                items = sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                dirs = [item for item in items if item.is_dir() and not item.name.startswith('.')]
                files = [item for item in items if item.is_file() and not item.name.startswith('.')]

                # 限制数量
                for d in dirs[:10]:
                    lines.append(f"{prefix}├── {d.name}/")
                    walk_dir(d, depth + 1, prefix + "│   ")

                for f in files[:10]:
                    lines.append(f"{prefix}├── {f.name}")
            except PermissionError:
                pass

        lines.append(f"{path_obj.name}/")
        walk_dir(path_obj, 0)
        return '\n'.join(lines[:50])  # 限制总行数

    def _detect_project_type(self, path: str) -> dict:
        """检测项目类型"""
        key_files = []
        project_type = "Unknown"

        checks = {
            "package.json": "Node.js/JavaScript",
            "requirements.txt": "Python",
            "setup.py": "Python",
            "pyproject.toml": "Python",
            "Cargo.toml": "Rust",
            "go.mod": "Go",
            "pom.xml": "Java (Maven)",
            "build.gradle": "Java (Gradle)",
            "Gemfile": "Ruby",
        }

        path_obj = Path(path)
        for file, ptype in checks.items():
            if (path_obj / file).exists():
                key_files.append(file)
                project_type = ptype
                break

        return {
            "type": project_type,
            "key_files": key_files
        }


class ShowContextCommand(Command):
    """显示 CLAUDE.md 内容"""

    name = "/show-context"
    description = "Show current CLAUDE.md content"

    async def execute(self, args: str, context: CLIContext) -> str:
        claude_md_path = Path.cwd() / "CLAUDE.md"

        if not claude_md_path.exists():
            return "ℹ️  No CLAUDE.md found. Use /init to create one."

        with open(claude_md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print("\n" + "=" * 50)
        print(content)
        print("=" * 50)

        return f"✓ CLAUDE.md ({len(content)} chars)"


class LoadContextCommand(Command):
    """加载 CLAUDE.md 到对话上下文"""

    name = "/load-context"
    description = "Load CLAUDE.md into conversation context"

    async def execute(self, args: str, context: CLIContext) -> str:
        claude_md_path = Path.cwd() / "CLAUDE.md"

        if not claude_md_path.exists():
            return "ℹ️  No CLAUDE.md found. Use /init to create one."

        with open(claude_md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 添加到上下文
        context.agent.context_manager.add_user_message(
            f"[System: Loading project context]\n\n{content}"
        )

        return f"✓ Loaded {len(content)} chars from CLAUDE.md"
