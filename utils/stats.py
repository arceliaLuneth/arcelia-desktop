from __future__ import annotations

from typing import Optional


def format_stats(stats: dict) -> str:
    """Turn Ollama's raw stream stats (nanosecond durations, token counts)
    into a short caption like '38 tokens · 2.1s · 18.4 tok/s'."""
    if not stats:
        return ""

    eval_count = stats.get("eval_count")
    eval_duration = stats.get("eval_duration")

    if not eval_count or not eval_duration:
        return ""

    seconds = eval_duration / 1_000_000_000
    tokens_per_sec = eval_count / seconds if seconds > 0 else 0

    return f"{eval_count} tokens · {seconds:.1f}s · {tokens_per_sec:.1f} tok/s"


def format_session_stats(reply_count: int, total_tokens: int) -> Optional[str]:
    if reply_count == 0:
        return None
    return f"Sesi ini: {reply_count} balasan · {total_tokens} tokens"
