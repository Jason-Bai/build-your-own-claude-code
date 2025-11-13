"""Prompt-Toolkit 增强的输入管理"""

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import Completer, Completion, CompleteEvent
from prompt_toolkit.styles import Style
from prompt_toolkit.document import Document
from pathlib import Path
import os


class CommandCompleter(Completer):
    """自定义命令补全器

    提供对带 "/" 前缀的命令的自动补全，支持：
    - 输入 "/" 显示所有命令
    - 输入 "/h" 自动补全到 "/help"
    - 忽略大小写匹配
    """

    def __init__(self, commands):
        """初始化补全器

        Args:
            commands: 命令字典，键为命令字符串（如 "/help"）
        """
        self.commands = list(commands.keys())

    def get_completions(self, document: Document, complete_event: CompleteEvent):
        """获取补全建议

        Args:
            document: 当前输入文本
            complete_event: 补全事件

        Yields:
            符合条件的补全选项
        """
        # 获取光标前的文本
        text_before_cursor = document.text_before_cursor

        # 如果为空，不提供补全
        if not text_before_cursor:
            return

        # 查找最后一个命令（通常以 "/" 开头）
        # 获取最后一个单词（从最后一个空格后开始）
        word_start = len(text_before_cursor)
        for i in range(len(text_before_cursor) - 1, -1, -1):
            if text_before_cursor[i].isspace():
                word_start = i + 1
                break
            elif i == 0:
                word_start = 0

        word = text_before_cursor[word_start:]

        # 如果当前单词不以 "/" 开头，不提供补全
        if not word.startswith('/'):
            return

        # 查找匹配的命令
        word_lower = word.lower()
        for cmd in self.commands:
            cmd_lower = cmd.lower()
            if cmd_lower.startswith(word_lower):
                # 返回补全建议
                # 补全文本是需要追加的部分
                completion_text = cmd[len(word):]
                yield Completion(completion_text, 0)


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

        # 创建自定义命令补全器
        # 提供智能的 "/" 前缀命令补全，支持大小写不敏感匹配
        self.completer = CommandCompleter(self.commands)

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
