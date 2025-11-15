#!/usr/bin/env python3
"""Debug Kimi's actual API response"""

import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from src.clients.kimi import KimiClient
from src.config.loader import load_config

async def test():
    config = load_config()
    kimi_config = config.get('providers', {}).get('kimi', {})

    client = KimiClient(
        api_key=kimi_config.get('api_key'),
        model=kimi_config.get('model_name', 'kimi-k2-thinking'),
        api_base=kimi_config.get('api_base')
    )

    # Intercept the raw OpenAI response
    original_create_message = client.client.chat.completions.create

    async def patched_create_message(**kwargs):
        print("📤 Calling Kimi with:")
        print(f"  messages count: {len(kwargs.get('messages', []))}")
        print(f"  tools: {len(kwargs.get('tools', []))}")

        response = await original_create_message(**kwargs)

        print("\n📥 Kimi Response:")
        message = response.choices[0].message
        print(f"  message.content: {message.content}")
        print(f"  message.tool_calls: {message.tool_calls}")

        if message.tool_calls:
            for i, tc in enumerate(message.tool_calls):
                print(f"\n  Tool Call {i}:")
                print(f"    id: {repr(tc.id)}")
                print(f"    function.name: {tc.function.name}")
                print(f"    function.arguments: {tc.function.arguments}")

        return response

    client.client.chat.completions.create = patched_create_message

    # Test with a simple tool call request
    result = await client.create_message(
        system="You are a helpful assistant with tools.",
        messages=[
            {"role": "user", "content": "list 3 python files"}
        ],
        tools=[
            {
                "name": "Glob",
                "description": "Search for files",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string"}
                    },
                    "required": ["pattern"]
                }
            }
        ]
    )

    print("\n✅ Converted Response:")
    print(json.dumps(result.content, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test())
