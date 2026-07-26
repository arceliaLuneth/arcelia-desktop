from __future__ import annotations

import shutil
import subprocess
from typing import List, Optional, Tuple

from skills.apps import BUILTIN_SKILLS
from skills.base import Skill

# A message only triggers a skill if it contains BOTH a trigger verb and a
# known app keyword. This keeps ordinary questions like "cara pakai
# spotify gimana?" from accidentally launching the app.
TRIGGER_WORDS = [
    "buka", "bukakan", "jalankan", "nyalain", "nyalakan",
    "mulai", "start", "launch", "run", "open",
]


class SkillRegistry:
    def __init__(self, skills: Optional[List[Skill]] = None) -> None:
        self.skills = skills if skills is not None else list(BUILTIN_SKILLS)

    def match(self, text: str) -> Optional[Skill]:
        lowered = text.lower()

        if not any(word in lowered for word in TRIGGER_WORDS):
            return None

        for skill in self.skills:
            for keyword in skill.keywords:
                if keyword in lowered:
                    return skill
        return None

    def find_binary(self, skill: Skill) -> Optional[str]:
        for candidate in skill.binary_candidates:
            path = shutil.which(candidate)
            if path:
                return path
        return None

    def run(self, skill: Skill) -> Tuple[bool, str]:
        """Launch the skill's application. Returns (success, message)."""
        binary = self.find_binary(skill)
        if binary is None:
            tried = ", ".join(skill.binary_candidates)
            return False, (
                f"{skill.description or skill.name} sepertinya belum terinstall "
                f"(sudah coba cari: {tried}). Coba install dulu lewat "
                f"`pacman -S {skill.binary_candidates[0]}` atau `yay -S {skill.binary_candidates[0]}`."
            )

        try:
            subprocess.Popen(
                [binary, *skill.args],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True, f"Oke, membuka {skill.description or skill.name}."
        except Exception as e:
            return False, f"Gagal membuka {skill.description or skill.name}: {e}"
