from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


class TTSEngine:
    """Text-to-speech using piper-plus (offline neural TTS — supports the
    Tsukuyomi-chan Japanese voice, plus Indonesian/English/etc via standard
    Piper voices) if a model is configured, falling back to pyttsx3 (lower
    quality, robotic, but needs zero extra setup) so voice output never
    hard-fails just because Piper isn't set up yet."""

    def __init__(self, piper_model_path: str = "", piper_config_path: str = "") -> None:
        self.piper_model_path = piper_model_path
        self.piper_config_path = piper_config_path
        self._piper_binary = shutil.which("piper")
        self._player_binary = (
            shutil.which("paplay") or shutil.which("aplay") or shutil.which("ffplay")
        )
        self._pyttsx3_engine = None

    def update_piper_model(self, model_path: str, config_path: str = "") -> None:
        self.piper_model_path = model_path
        self.piper_config_path = config_path

    def is_piper_ready(self) -> bool:
        if not self._piper_binary or not self.piper_model_path:
            return False

        # Accept either a real file path (standard Piper voices, e.g. a
        # downloaded .onnx) OR a bare model name like "tsukuyomi" —
        # piper-plus resolves short names against its own downloaded-model
        # registry itself, so it won't exist as a path Python can see here.
        if Path(self.piper_model_path).exists():
            return True
        looks_like_bare_name = "/" not in self.piper_model_path and "\\" not in self.piper_model_path
        return looks_like_bare_name

    def backend_name(self) -> str:
        if self.is_piper_ready():
            return "piper"
        try:
            import pyttsx3  # noqa: F401
            return "pyttsx3"
        except ImportError:
            return "none"

    def speak(self, text: str) -> None:
        text = text.strip()
        if not text:
            return

        if self.is_piper_ready():
            self._speak_piper(text)
        else:
            self._speak_pyttsx3(text)

    def _speak_piper(self, text: str) -> None:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name

        try:
            cmd = [self._piper_binary, "-m", self.piper_model_path, "-f", wav_path]
            if self.piper_config_path:
                cmd += ["-c", self.piper_config_path]

            result = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )
            if result.returncode != 0:
                detail = result.stderr.decode("utf-8", errors="replace").strip()
                raise RuntimeError(
                    f"Piper gagal (kode {result.returncode}): {detail or 'tidak ada detail dari piper'}"
                )

            if self._player_binary:
                play_result = subprocess.run(
                    [self._player_binary, wav_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=120,
                )
                if play_result.returncode != 0:
                    detail = play_result.stderr.decode("utf-8", errors="replace").strip()
                    raise RuntimeError(
                        f"Gagal memutar audio lewat {self._player_binary}: {detail or 'tidak ada detail'}"
                    )
            else:
                raise RuntimeError(
                    "Tidak ada audio player ditemukan (paplay/aplay/ffplay) — "
                    "install salah satu, mis. `sudo pacman -S pulseaudio` untuk paplay."
                )
        finally:
            Path(wav_path).unlink(missing_ok=True)

    def _speak_pyttsx3(self, text: str) -> None:
        try:
            import pyttsx3
        except ImportError:
            raise RuntimeError(
                "Tidak ada engine TTS yang siap — model Piper belum diatur "
                "(Settings) dan pyttsx3 juga tidak terpasang."
            )

        if self._pyttsx3_engine is None:
            self._pyttsx3_engine = pyttsx3.init()

        self._pyttsx3_engine.say(text)
        self._pyttsx3_engine.runAndWait()
