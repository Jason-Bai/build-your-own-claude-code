import argparse

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Build Your Own Claude Code - Enhanced Edition"
    )

    # 权限控制参数（互斥）
    permission_group = parser.add_mutually_exclusive_group()
    permission_group.add_argument(
        "--dangerously-skip-permissions",
        action="store_true",
        help="Skip all permission checks (DANGEROUS)"
    )
    permission_group.add_argument(
        "--auto-approve-all",
        action="store_true",
        help="Automatically approve all tools (dangerous)"
    )
    permission_group.add_argument(
        "--always-ask",
        action="store_true",
        help="Always ask for permission, even for safe tools"
    )

    # 输出级别参数（互斥）
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output (show tool details, thinking process)"
    )
    output_group.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode (only show errors and agent responses)"
    )

    # 其他参数
    parser.add_argument(
        "--config",
        default="~/.tiny-claude-code/settings.json",
        help="Path to config file (default: ~/.tiny-claude-code/settings.json)"
    )

    return parser.parse_args()
