from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Skill:
    """A single 'thing Arcelia can do' — e.g. opening an application.

    - name: internal id, e.g. "spotify"
    - keywords: words that, combined with a trigger verb ("buka", "open",
      "jalankan", "start", "nyalain"), identify this skill in a message.
    - binary_candidates: possible executable names to try, in priority
      order (covers different desktop environments / installed apps).
    - description: shown to the user if nothing matches, for discoverability.
    """

    name: str
    keywords: List[str]
    binary_candidates: List[str]
    description: str = ""
    args: List[str] = field(default_factory=list)
