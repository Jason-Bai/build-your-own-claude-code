"""Package setup configuration"""

from setuptools import setup, find_packages

setup(
    name="build-your-own-claude-code",
    version="0.1.0",
    description="A minimal implementation of Claude Code - AI coding assistant",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.40.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "mcp": ["mcp>=1.0.0"],
        "ui": ["rich>=13.0.0", "prompt-toolkit>=3.0.0"],
    },
    entry_points={
        "console_scripts": [
            "byoc=src.main:cli",
        ],
    },
    python_requires=">=3.10",
)
