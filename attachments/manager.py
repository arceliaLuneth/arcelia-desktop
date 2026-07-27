from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
TEXT_EXTENSIONS = {
    ".txt", ".md", ".py", ".js", ".ts", ".json", ".csv", ".log",
    ".yaml", ".yml", ".toml", ".ini", ".xml", ".html", ".css", ".sh",
}

MAX_TEXT_CHARS = 20_000


@dataclass
class Attachment:
    path: str
    name: str
    kind: str  # "image" | "text" | "other"


def classify(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in TEXT_EXTENSIONS:
        return "text"
    return "other"


def make_attachment(path: str) -> Attachment:
    p = Path(path)
    return Attachment(path=str(p), name=p.name, kind=classify(path))


def read_text_preview(path: str, max_chars: int = MAX_TEXT_CHARS) -> str:
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"[gagal membaca file: {e}]"

    if len(text) > max_chars:
        text = text[:max_chars] + f"\n... (dipotong, file lebih dari {max_chars} karakter)"
    return text


# -- persisting attachments alongside a chat message ------------------------
#
# Rather than adding a new DB table/column, attachment metadata is appended
# to the message's own `content` string as an HTML-comment marker (invisible
# once parsed back out). This keeps chat_database.py untouched and means
# attachments survive reload/export without any schema migration.

_MARKER_RE = re.compile(r"<!--ATTACH:(.*?)-->", re.DOTALL)


def encode_marker(attachments: List[Attachment]) -> str:
    if not attachments:
        return ""
    payload = [{"path": a.path, "name": a.name, "kind": a.kind} for a in attachments]
    return f"\n\n<!--ATTACH:{json.dumps(payload)}-->"


def split_content_and_attachments(content: str) -> Tuple[str, List[Attachment]]:
    match = _MARKER_RE.search(content)
    if not match:
        return content, []

    text = content[: match.start()].rstrip()
    try:
        payload = json.loads(match.group(1))
    except Exception:
        return content, []

    attachments = [
        Attachment(path=item["path"], name=item["name"], kind=item["kind"])
        for item in payload
    ]
    return text, attachments
