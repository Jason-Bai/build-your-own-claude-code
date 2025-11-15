"""
Entry point for: python -m src
Delegates to src.cli.main
"""

from .cli.main import cli

if __name__ == "__main__":
    cli()
