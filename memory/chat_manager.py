from __future__ import annotations

from typing import Any, Dict, List, Optional

from memory.chat_database import ChatDatabase

Message = Dict[str, Any]


class ChatManager:
    def __init__(self) -> None:
        self.db = ChatDatabase()
        self.current_conversation_id: Optional[int] = None
        self.current_messages: List[Message] = []

    def get_chat_list(self) -> List[Dict[str, Any]]:
        return self.db.get_conversations()

    def search_chats(self, query: str) -> List[Dict[str, Any]]:
        query = query.strip()
        if not query:
            return self.get_chat_list()
        return self.db.search_conversations(query)

    def toggle_pin(self, conversation_id: int) -> None:
        conv = self.db.get_conversation(conversation_id)
        if conv is None:
            return
        currently_pinned = bool(conv.get("pinned", 0))
        self.db.set_pinned(conversation_id, not currently_pinned)

    def new_chat(self, title: str = "New Chat") -> int:
        conversation_id = self.db.create_conversation(title)
        self.current_conversation_id = conversation_id
        self.current_messages = []
        return conversation_id

    def load_chat(self, conversation_id: int) -> List[Message]:
        self.current_conversation_id = conversation_id
        messages = self.db.get_messages(conversation_id)
        self.current_messages = [
            {"role": m["role"], "content": m["content"], "id": m["id"]}
            for m in messages
        ]
        return self.current_messages

    def rename_chat(self, conversation_id: int, title: str) -> None:
        self.db.rename_conversation(conversation_id, title)

    def delete_chat(self, conversation_id: int) -> None:
        self.db.delete_conversation(conversation_id)

        if self.current_conversation_id == conversation_id:
            self.current_conversation_id = None
            self.current_messages = []

    def add_user_message(self, text: str) -> int:
        if self.current_conversation_id is None:
            self.new_chat()

        assert self.current_conversation_id is not None
        msg_id = self.db.save_message(self.current_conversation_id, "user", text)
        self.current_messages.append({"role": "user", "content": text, "id": msg_id})
        return self.current_conversation_id

    def add_assistant_message(self, text: str) -> None:
        if self.current_conversation_id is None:
            return

        msg_id = self.db.save_message(self.current_conversation_id, "assistant", text)
        self.current_messages.append({"role": "assistant", "content": text, "id": msg_id})

    def get_current_messages(self) -> List[Message]:
        return self.current_messages

    def get_current_conversation_id(self) -> Optional[int]:
        return self.current_conversation_id

    def set_current_conversation(self, conversation_id: int) -> List[Message]:
        return self.load_chat(conversation_id)

    def ensure_current_chat(self) -> int:
        if self.current_conversation_id is None:
            return self.new_chat()
        return self.current_conversation_id

    # -- regenerate / edit & resend -------------------------------------

    def remove_last_message(self) -> None:
        """Remove the last message (used before regenerating a reply)."""
        if not self.current_messages:
            return

        last = self.current_messages[-1]
        msg_id = last.get("id")
        if msg_id is not None and self.current_conversation_id is not None:
            self.db.delete_message(msg_id)
        self.current_messages.pop()

    def truncate_from(self, index: int) -> None:
        """Delete the message at `index` and everything after it, both in
        memory and in the database. Used when a user edits an earlier
        prompt: the old follow-up messages are discarded."""
        if self.current_conversation_id is None:
            return
        if not (0 <= index < len(self.current_messages)):
            return

        msg_id = self.current_messages[index].get("id")
        if msg_id is not None:
            self.db.delete_messages_from(self.current_conversation_id, msg_id)

        self.current_messages = self.current_messages[:index]
