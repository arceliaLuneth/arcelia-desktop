from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Skill:
    name: str
    keywords: List[str]
    binary_candidates: List[str]
    description: str = ""
    args: List[str] = field(default_factory=list)
