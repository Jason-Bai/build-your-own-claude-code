"""Conversation persistence for saving and loading chat history"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class ConversationPersistence:
    """对话持久化管理"""

    def __init__(self, storage_dir: str = ".conversations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def save_conversation(
        self,
        conversation_id: str,
        messages: list,
        system_prompt: str,
        summary: str = "",
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        保存对话

        Returns:
            保存的文件路径
        """
        data = {
            "id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "system_prompt": system_prompt,
            "summary": summary,
            "messages": messages,
            "metadata": metadata or {}
        }

        file_path = self.storage_dir / f"{conversation_id}.json"

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(file_path)

    def load_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """加载对话"""
        file_path = self.storage_dir / f"{conversation_id}.json"

        if not file_path.exists():
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_conversations(self) -> list[Dict[str, str]]:
        """列出所有保存的对话"""
        conversations = []

        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    conversations.append({
                        "id": data.get("id", file_path.stem),
                        "timestamp": data.get("timestamp", ""),
                        "message_count": len(data.get("messages", [])),
                        "file": str(file_path)
                    })
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

        # 按时间倒序排序
        conversations.sort(key=lambda x: x["timestamp"], reverse=True)
        return conversations

    def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话"""
        file_path = self.storage_dir / f"{conversation_id}.json"

        if file_path.exists():
            file_path.unlink()
            return True

        return False

    def get_latest_conversation_id(self) -> Optional[str]:
        """获取最新的对话 ID"""
        conversations = self.list_conversations()
        return conversations[0]["id"] if conversations else None

    def auto_save_id(self) -> str:
        """生成自动保存的对话 ID"""
        return f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
