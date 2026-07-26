from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

Message = Dict[str, str]

_HEADER_RE = re.compile(r"^## (You|Arcelia) \(([^)]*)\)\s*$", re.MULTILINE)


def _to_markdown(title: str, messages: List[Message]) -> str:
    lines = [
        "# Arcelia Chat Export",
        f"# Title: {title}",
        f"# Exported: {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]
    for msg in messages:
        speaker = "You" if msg["role"] == "user" else "Arcelia"
        ts = msg.get("created_at", "")
        lines.append(f"## {speaker} ({ts})")
        lines.append(msg["content"].strip())
        lines.append("")
    return "\n".join(lines)


def export_conversation(path: str, title: str, messages: List[Message]) -> None:
    """Export a conversation to .md, .txt, or .pdf based on the file
    extension in `path`. `messages` should include 'role', 'content', and
    ideally 'created_at' (from ChatDatabase.get_messages)."""
    suffix = Path(path).suffix.lower()

    if suffix == ".pdf":
        _export_pdf(path, title, messages)
    else:
        Path(path).write_text(_to_markdown(title, messages), encoding="utf-8")


def _export_pdf(path: str, title: str, messages: List[Message]) -> None:
    # Imported lazily so this module can be unit-tested without a Qt
    # application instance running.
    from PySide6.QtGui import QTextDocument
    from PySide6.QtPrintSupport import QPrinter

    from ui.markdown_render import render_markdown

    html_parts = [f"<h1>{title}</h1>"]
    for msg in messages:
        speaker = "You" if msg["role"] == "user" else "Arcelia"
        full_html, _ = render_markdown(msg["content"])
        inner = full_html.split("<body>", 1)[-1].rsplit("</body>", 1)[0]
        html_parts.append(f"<h3>{speaker}</h3>{inner}<hr/>")

    doc = QTextDocument()
    doc.setHtml("".join(html_parts))

    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(path)
    doc.print_(printer)


def import_conversation(path: str) -> Tuple[str, List[Message]]:
    """Parse a file back into (title, messages). Understands Arcelia's own
    export format; falls back to treating the whole file as one message for
    arbitrary .txt/.md files."""
    text = Path(path).read_text(encoding="utf-8")

    title = Path(path).stem
    title_match = re.search(r"^# Title: (.+)$", text, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()

    messages: List[Message] = []
    matches = list(_HEADER_RE.finditer(text))

    for i, match in enumerate(matches):
        speaker = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if not content:
            continue
        role = "user" if speaker == "You" else "assistant"
        messages.append({"role": role, "content": content})

    if not messages:
        content = text.strip()
        if content:
            messages.append({"role": "user", "content": content})

    return title, messages
