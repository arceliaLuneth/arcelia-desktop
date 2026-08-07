from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class AppSettings:
    ollama_host: str = "http://localhost:11434"
    model: str = "qwen2.5:3b"
    system_prompt: str = (
        "You are Arcelia, a helpful desktop AI assistant. "
        "Reply naturally, clearly, and briefly unless the user asks for detail. "
        "Always answer in Indonesian unless the user asks otherwise."
    )
    theme: str = "dark"  # "dark" | "light"
    debug_mode: bool = False
    voice_enabled: bool = False
    piper_model_path: str = ""
    piper_config_path: str = ""
    vosk_model_path: str = ""
    character_enabled: bool = False
    vrm_path: str = ""

    @classmethod
    def _settings_path(cls) -> Path:
        base_dir = Path(__file__).resolve().parent.parent
        data_dir = base_dir / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir / "settings.json"

    @classmethod
    def load(cls) -> "AppSettings":
        path = cls._settings_path()
        if not path.exists():
            return cls()

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return cls()

        defaults = cls()
        known_fields = asdict(defaults).keys()
        filtered = {k: v for k, v in raw.items() if k in known_fields}
        return cls(**{**asdict(defaults), **filtered})

    def save(self) -> None:
        path = self._settings_path()
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
