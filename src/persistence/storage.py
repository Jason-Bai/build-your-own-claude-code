# src/persistence/storage.py
import json
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List

from datetime import datetime

# Use filelock for cross-platform file locking
try:
    from filelock import FileLock, Timeout
    FILELOCK_AVAILABLE = True
except ImportError:
    FILELOCK_AVAILABLE = False


def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(
        f"Object of type {obj.__class__.__name__} is not JSON serializable")


class BaseStorage(ABC):
    @abstractmethod
    async def save(self, category: str, key: str, data: Dict) -> str: pass
    @abstractmethod
    async def load(self, category: str, key: str) -> Optional[Dict]: pass
    @abstractmethod
    async def delete(self, category: str, key: str) -> bool: pass
    @abstractmethod
    async def list(self, category: str) -> List[str]: pass


class JSONStorage(BaseStorage):
    def __init__(self, project_name: str, base_dir: str = "~/.tiny-claude-code"):
        base_path = Path(base_dir).expanduser()
        self.storage_dir = base_path / "projects" / project_name
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, category: str, key: str, data: Dict) -> str:
        category_dir = self.storage_dir / category
        category_dir.mkdir(exist_ok=True)
        file_path = category_dir / f"{key}.json"
        lock_path = category_dir / f"{key}.json.lock"

        if FILELOCK_AVAILABLE:
            lock = FileLock(lock_path, timeout=5)
            try:
                with lock:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False,
                                  indent=2, default=json_serializer)
            except Timeout:
                raise RuntimeError(
                    f"Could not acquire lock for file {file_path}")
        else:
            # Fallback for environments without filelock
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False,
                          indent=2, default=json_serializer)

        return str(file_path)

    async def load(self, category: str, key: str) -> Optional[Dict]:
        file_path = self.storage_dir / category / f"{key}.json"
        if not file_path.exists():
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def delete(self, category: str, key: str) -> bool:
        category_dir = self.storage_dir / category
        file_path = category_dir / f"{key}.json"
        lock_path = category_dir / f"{key}.json.lock"
        if file_path.exists():
            file_path.unlink()
            if Path(lock_path).exists():
                Path(lock_path).unlink()
            return True
        return False

    async def list(self, category: str) -> List[str]:
        category_dir = self.storage_dir / category
        if not category_dir.exists():
            return []
        return [f.stem for f in category_dir.glob("*.json")]


class SQLiteStorage(BaseStorage):
    def __init__(self, project_name: str, base_dir: str = "~/.tiny-claude-code"):
        base_path = Path(base_dir).expanduser()
        self.db_path = base_path / "projects" / project_name / "persistence.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS persistence (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            key TEXT NOT NULL,
            data JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, key)
        )
        """)
        conn.commit()
        conn.close()

    async def save(self, category: str, key: str, data: Dict) -> str:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        unique_id = f"{category}:{key}"
        json_data = json.dumps(data, default=json_serializer)
        cursor.execute("""
        INSERT OR REPLACE INTO persistence (id, category, key, data, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (unique_id, category, key, json_data))
        conn.commit()
        conn.close()
        return unique_id

    async def load(self, category: str, key: str) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT data FROM persistence WHERE category=? AND key=?", (category, key))
        row = cursor.fetchone()
        conn.close()
        return json.loads(row[0]) if row else None

    async def delete(self, category: str, key: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM persistence WHERE category=? AND key=?", (category, key))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    async def list(self, category: str) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT key FROM persistence WHERE category=?", (category,))
        keys = [row[0] for row in cursor.fetchall()]
        conn.close()
        return keys
