from __future__ import annotations

from skills.base import Skill

# Each skill lists several possible binaries because EndeavourOS users run
# different desktop environments (KDE, XFCE, GNOME, etc.) and different
# apps for the "same" job. The registry tries them in order and launches
# whichever is actually installed.

BUILTIN_SKILLS: list[Skill] = [
    Skill(
        name="spotify",
        keywords=["spotify"],
        binary_candidates=["spotify", "spotify-launcher"],
        description="Buka Spotify",
    ),
    Skill(
        name="firefox",
        keywords=["firefox", "browser", "internet"],
        binary_candidates=["firefox"],
        description="Buka Firefox",
    ),
    Skill(
        name="chrome",
        keywords=["chrome", "chromium", "google chrome"],
        binary_candidates=["google-chrome-stable", "google-chrome", "chromium"],
        description="Buka Chrome/Chromium",
    ),
    Skill(
        name="discord",
        keywords=["discord"],
        binary_candidates=["discord"],
        description="Buka Discord",
    ),
    Skill(
        name="telegram",
        keywords=["telegram", "telegram desktop"],
        binary_candidates=["telegram-desktop", "Telegram"],
        description="Buka Telegram",
    ),
    Skill(
        name="steam",
        keywords=["steam"],
        binary_candidates=["steam"],
        description="Buka Steam",
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
        binary_candidates=["konsole", "alacritty", "kitty", "xfce4-terminal", "gnome-terminal", "xterm"],
        description="Buka terminal",
    ),
    Skill(
        name="calculator",
        keywords=["kalkulator", "calculator"],
        binary_candidates=["kcalc", "gnome-calculator", "qalculate-gtk", "galculator"],
        description="Buka kalkulator",
    ),
    Skill(
        name="gimp",
        keywords=["gimp", "photoshop"],
        binary_candidates=["gimp"],
        description="Buka GIMP",
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
