from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ChatDatabase:
    def __init__(self, db_path: str | None = None) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        data_dir = base_dir / "data"
        data_dir.mkdir(exist_ok=True)

        self.db_path = Path(db_path) if db_path else data_dir / "arcelia.db"
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")

        self.create_tables()

    def now(self) -> str:
        return datetime.now().isoformat(timespec="seconds")

    def create_tables(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(conversation_id)
                    REFERENCES conversations(id)
                    ON DELETE CASCADE
            )
            """
        )

        self.conn.commit()
        self._migrate_add_pinned_column()

    def _migrate_add_pinned_column(self) -> None:
        """Add the 'pinned' column to existing databases created before this
        feature existed. Safe to call every startup — checks first."""
        cur = self.conn.execute("PRAGMA table_info(conversations)")
        columns = {row["name"] for row in cur.fetchall()}
        if "pinned" not in columns:
            self.conn.execute(
                "ALTER TABLE conversations ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0"
            )
            self.conn.commit()

    def create_conversation(self, title: str = "New Chat") -> int:
        created_at = self.now()
        cur = self.conn.execute(
            """
            INSERT INTO conversations (title, created_at, updated_at)
            VALUES (?, ?, ?)
            """,
            (title, created_at, created_at),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def get_conversations(self) -> List[Dict[str, Any]]:
        cur = self.conn.execute(
            """
            SELECT id, title, created_at, updated_at, pinned
            FROM conversations
            ORDER BY pinned DESC, updated_at DESC, id DESC
            """
        )
        return [dict(row) for row in cur.fetchall()]

    def get_conversation(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        cur = self.conn.execute(
            """
            SELECT id, title, created_at, updated_at, pinned
            FROM conversations
            WHERE id = ?
            """,
            (conversation_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def set_pinned(self, conversation_id: int, pinned: bool) -> None:
        self.conn.execute(
            "UPDATE conversations SET pinned = ? WHERE id = ?",
            (1 if pinned else 0, conversation_id),
        )
        self.conn.commit()

    def search_conversations(self, query: str) -> List[Dict[str, Any]]:
        """Find conversations whose title OR any message content contains
        `query` (case-insensitive substring match)."""
        like = f"%{query}%"
        cur = self.conn.execute(
            """
            SELECT DISTINCT c.id, c.title, c.created_at, c.updated_at, c.pinned
            FROM conversations c
            LEFT JOIN messages m ON m.conversation_id = c.id
            WHERE c.title LIKE ? COLLATE NOCASE
               OR m.content LIKE ? COLLATE NOCASE
            ORDER BY c.pinned DESC, c.updated_at DESC, c.id DESC
            """,
            (like, like),
        )
        return [dict(row) for row in cur.fetchall()]

    def save_message(self, conversation_id: int, role: str, content: str) -> int:
        created_at = self.now()
        cur = self.conn.execute(
            """
            INSERT INTO messages (conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (conversation_id, role, content, created_at),
        )

        self.conn.execute(
            """
            UPDATE conversations
            SET updated_at = ?
            WHERE id = ?
            """,
            (created_at, conversation_id),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def get_messages(self, conversation_id: int) -> List[Dict[str, Any]]:
        cur = self.conn.execute(
            """
            SELECT id, conversation_id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,),
        )
        return [dict(row) for row in cur.fetchall()]

    def rename_conversation(self, conversation_id: int, title: str) -> None:
        updated_at = self.now()
        self.conn.execute(
            """
            UPDATE conversations
            SET title = ?, updated_at = ?
            WHERE id = ?
            """,
            (title, updated_at, conversation_id),
        )
        self.conn.commit()

    def delete_conversation(self, conversation_id: int) -> None:
        self.conn.execute(
            """
            DELETE FROM conversations
            WHERE id = ?
            """,
            (conversation_id,),
        )
        self.conn.commit()

    def delete_message(self, message_id: int) -> None:
        """Delete a single message by id (used by 'regenerate')."""
        self.conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        self.conn.commit()

    def delete_messages_from(self, conversation_id: int, message_id: int) -> None:
        """Delete a message and every message after it in the conversation
        (used by 'edit & resend': everything after the edited prompt is
        discarded so the conversation can continue fresh from there)."""
        self.conn.execute(
            """
            DELETE FROM messages
            WHERE conversation_id = ? AND id >= ?
            """,
            (conversation_id, message_id),
        )
        self.conn.commit()

    def close(self) -> None:
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    db = ChatDatabase()
    conv_id = db.create_conversation("Testing Arcelia")
    db.save_message(conv_id, "user", "Halo")
    db.save_message(conv_id, "assistant", "Halo juga!")

    print("Conversations:")
    print(db.get_conversations())

    print("\nMessages:")
    print(db.get_messages(conv_id))

    db.close()
