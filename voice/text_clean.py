from __future__ import annotations

import re

_CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`]*`")
_MARKDOWN_SYMBOLS_RE = re.compile(r"[#*_>~]")
_URL_RE = re.compile(r"https?://\S+")
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
_MULTI_NEWLINE_RE = re.compile(r"\n{2,}")


def strip_for_speech(text: str, max_chars: int = 800) -> str:
    """Turn a markdown assistant reply into plain text suitable for TTS:
    code blocks are dropped (reading raw code aloud is useless/annoying),
    markdown symbols and links are stripped, and very long replies are
    capped so a giant answer doesn't turn into a 3-minute monologue."""
    cleaned = _CODE_BLOCK_RE.sub(" (ada contoh kode di layar) ", text)
    cleaned = _INLINE_CODE_RE.sub(lambda m: m.group(0).strip("`"), cleaned)
    cleaned = _URL_RE.sub("", cleaned)
    cleaned = _MARKDOWN_SYMBOLS_RE.sub("", cleaned)
    cleaned = _MULTI_NEWLINE_RE.sub(". ", cleaned)
    cleaned = _MULTI_SPACE_RE.sub(" ", cleaned)
    cleaned = cleaned.strip()

    if len(cleaned) > max_chars:
        cut = cleaned.rfind(". ", 0, max_chars)
        cleaned = cleaned[: cut + 1] if cut > 0 else cleaned[:max_chars]

    return cleaned
