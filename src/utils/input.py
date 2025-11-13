"""Prompt-Toolkit 增强的输入管理"""

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter, NestedCompleter
from prompt_toolkit.styles import Style
from pathlib import Path
import os


class PromptInputManager:
    """使用 Prompt-Toolkit 的输入管理器

    提供增强的命令行输入体验：
    - 命令自动补全（Tab 键）
    - 历史记录保存和搜索（Up/Down, Ctrl+R）
    - 多行编辑支持（Alt+Enter）
    - 快捷键支持（Ctrl+A/E/K/U/W）
    - 鼠标支持
    """

    def __init__(self, history_file: str = ".tiny_claude_code_history"):
        """
        初始化输入管理器

        Args:
            history_file: 历史记录文件名（保存在 ~/.cache/tiny_claude_code/ 目录下）
        """
        # 创建缓存目录
        cache_dir = Path.home() / ".cache" / "tiny_claude_code"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # 历史记录路径
        history_path = cache_dir / history_file

        # 创建 FileHistory 对象
        self.history = FileHistory(str(history_path))

        # 定义命令补全列表
        self.commands = {
            '/help': None,
            '/status': None,
            '/todos': None,
            '/save': None,
            '/load': None,
            '/conversations': None,
            '/delete': None,
            '/clear': None,
            '/init': None,
            '/quiet': None,
            '/exit': None,
        }

        # 创建 NestedCompleter 用于命令补全
        self.completer = NestedCompleter({
            cmd.lstrip('/'): None for cmd in self.commands.keys()
        })

        # 定义样式（颜色和格式）
        self.style = Style.from_dict({
            'prompt': '#ffd700 bold',  # 黄色加粗（黄金色）
        })

        # 创建 PromptSession（主要的输入会话）
        self.session = PromptSession(
            history=self.history,
            enable_history_search=True,    # Ctrl+R 搜索历史
            search_ignore_case=True,       # 搜索时忽略大小写
            mouse_support=True,            # 支持鼠标
        )

    def get_input(self, prompt: str = "👤 You: ", default: str = "") -> str:
        """
        获取用户输入 (同步方法)

        注意：此方法不能在已有运行的 asyncio 事件循环中使用。
        请在异步上下文中使用 async_get_input() 方法。

        支持的增强功能：
        - Tab 键：自动补全命令
        - Up/Down：浏览历史记录
        - Ctrl+R：搜索历史记录
        - Ctrl+A/E：行首/行尾
        - Ctrl+K/U：删除到行尾/行首
        - Ctrl+W：删除前一个单词
        - Alt+Enter：切换多行模式
        - 鼠标：选择、复制、粘贴

        Args:
            prompt: 输入提示符
            default: 默认值

        Returns:
            用户输入的文本

        Raises:
            KeyboardInterrupt: 用户按 Ctrl+C
            EOFError: 用户按 Ctrl+D
        """
        try:
            # 使用 PromptSession 获取用户输入
            text = self.session.prompt(
                prompt,
                completer=self.completer,
                style=self.style,
                default=default,
                multiline=False,        # 默认单行（用户可按 Alt+Enter 切换）
                mouse_support=True,
                search_ignore_case=True,
            )
            return text.strip()
        except (KeyboardInterrupt, EOFError):
            # 重新抛出异常，由调用者处理
            raise

    async def async_get_input(self, prompt: str = "👤 You: ", default: str = "") -> str:
        """
        异步获取用户输入

        此方法与 asyncio 事件循环兼容，应在异步上下文中使用。

        支持的增强功能：
        - Tab 键：自动补全命令
        - Up/Down：浏览历史记录
        - Ctrl+R：搜索历史记录
        - Ctrl+A/E：行首/行尾
        - Ctrl+K/U：删除到行尾/行首
        - Ctrl+W：删除前一个单词
        - Alt+Enter：切换多行模式
        - 鼠标：选择、复制、粘贴

        Args:
            prompt: 输入提示符
            default: 默认值

        Returns:
            用户输入的文本

        Raises:
            KeyboardInterrupt: 用户按 Ctrl+C
            EOFError: 用户按 Ctrl+D
        """
        try:
            # 使用异步 prompt 方法，与事件循环兼容
            text = await self.session.prompt_async(
                prompt,
                completer=self.completer,
                style=self.style,
                default=default,
                multiline=False,        # 默认单行（用户可按 Alt+Enter 切换）
                mouse_support=True,
                search_ignore_case=True,
            )
            return text.strip()
        except (KeyboardInterrupt, EOFError):
            # 重新抛出异常，由调用者处理
            raise

    def get_multiline_input(self, prompt: str = "👤 You: ") -> str:
        """
        获取多行输入 (同步方法)

        注意：此方法不能在已有运行的 asyncio 事件循环中使用。
        请在异步上下文中使用 async_get_multiline_input() 方法。

        用于复杂查询或代码块输入。用户可在编辑时按 Ctrl+D 或 Alt+Enter
        完成输入。

        Args:
            prompt: 输入提示符

        Returns:
            用户输入的文本

        Raises:
            KeyboardInterrupt: 用户按 Ctrl+C
            EOFError: 用户按 Ctrl+D
        """
        try:
            text = self.session.prompt(
                prompt,
                completer=self.completer,
                style=self.style,
                multiline=True,         # 启用多行模式
                mouse_support=True,
                search_ignore_case=True,
            )
            return text.strip()
        except (KeyboardInterrupt, EOFError):
            raise

    async def async_get_multiline_input(self, prompt: str = "👤 You: ") -> str:
        """
        异步获取多行输入

        此方法与 asyncio 事件循环兼容，应在异步上下文中使用。

        用于复杂查询或代码块输入。用户可在编辑时按 Ctrl+D 或 Alt+Enter
        完成输入。

        Args:
            prompt: 输入提示符

        Returns:
            用户输入的文本

        Raises:
            KeyboardInterrupt: 用户按 Ctrl+C
            EOFError: 用户按 Ctrl+D
        """
        try:
            text = await self.session.prompt_async(
                prompt,
                completer=self.completer,
                style=self.style,
                multiline=True,         # 启用多行模式
                mouse_support=True,
                search_ignore_case=True,
            )
            return text.strip()
        except (KeyboardInterrupt, EOFError):
            raise

    def clear_history(self) -> None:
        """清空历史记录"""
        self.history.clear()

    @property
    def history_file(self) -> str:
        """获取历史记录文件路径"""
        return str(self.history.filename)


# 全局实例
_input_manager: PromptInputManager = None


def get_input_manager() -> PromptInputManager:
    """获取全局输入管理器实例

    使用单例模式确保整个应用中只有一个 PromptInputManager 实例，
    这样历史记录会被正确共享。

    Returns:
        全局 PromptInputManager 实例
    """
    global _input_manager
    if _input_manager is None:
        _input_manager = PromptInputManager()
    return _input_manager


def reset_input_manager() -> None:
    """重置全局输入管理器

    用于测试环境，清除全局实例。
    """
    global _input_manager
    _input_manager = None
