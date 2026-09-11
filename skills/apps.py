from __future__ import annotations

from skills.base import Skill

BUILTIN_SKILLS: list[Skill] = [
    Skill(
        name="chrome",
        keywords=["chrome", "chromium", "google chrome"],
        binary_candidates=["google-chrome-stable", "google-chrome", "chromium"],
        description="Buka Chrome/Chromium",
    ),
    Skill(
        name="code",
        keywords=["vscode", "vs code", "visual studio code", "code editor"],
        binary_candidates=["code", "codium", "code-oss"],
        description="Buka VS Code",
    ),
    Skill(
        name="files",
        keywords=["file manager", "file explorer", "explorer", "folder", "berkas"],
        binary_candidates=["dolphin", "nautilus", "thunar", "pcmanfm", "nemo"],
        description="Buka file manager",
    ),
    Skill(
        name="terminal",
        keywords=["terminal", "konsol", "console", "cmd"],
        binary_candidates=["kitty"],
        description="Buka terminal",
    ),
    Skill(
        name="calculator",
        keywords=["kalkulator", "calculator"],
        binary_candidates=["kcalc", "gnome-calculator", "qalculate-gtk", "galculator"],
        description="Buka kalkulator",
    ),
    Skill(
        name="obs",
        keywords=["obs", "obs studio", "rekam layar", "screen record"],
        binary_candidates=["obs"],
        description="Buka OBS Studio",
    ),
    Skill(
        name="settings",
        keywords=["pengaturan sistem", "system settings", "control panel"],
        binary_candidates=["systemsettings", "gnome-control-center", "xfce4-settings-manager"],
        description="Buka pengaturan sistem",
    ),
]
