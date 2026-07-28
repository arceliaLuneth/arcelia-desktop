from __future__ import annotations

import json
import queue
from pathlib import Path
from typing import Callable


class STTEngine:
    """Offline speech-to-text using Vosk. Needs a Vosk model directory
    (downloaded separately, see README) — nothing is bundled since models
    are hundreds of MB and language-specific."""

    def __init__(self, model_path: str = "", samplerate: int = 16000) -> None:
        self.model_path = model_path
        self.samplerate = samplerate
        self._model = None

    def update_model_path(self, model_path: str) -> None:
        if model_path != self.model_path:
            self.model_path = model_path
            self._model = None  # force reload on next use

    def is_ready(self) -> bool:
        return bool(self.model_path and Path(self.model_path).is_dir())

    def _get_model(self):
        if self._model is None:
            import vosk
            vosk.SetLogLevel(-1)  # silence Vosk's own console spam
            self._model = vosk.Model(self.model_path)
        return self._model

    def listen_until_stopped(self, should_stop: Callable[[], bool]) -> str:
        """Record from the default microphone and transcribe with Vosk
        until `should_stop()` returns True. Blocking — call this from a
        background thread, never from the UI thread."""
        import sounddevice as sd
        import vosk

        model = self._get_model()
        recognizer = vosk.KaldiRecognizer(model, self.samplerate)
        recognizer.SetWords(False)

        audio_queue: "queue.Queue[bytes]" = queue.Queue()

        def callback(indata, frames, time_info, status) -> None:
            audio_queue.put(bytes(indata))

        with sd.RawInputStream(
            samplerate=self.samplerate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=callback,
        ):
            while not should_stop():
                try:
                    data = audio_queue.get(timeout=0.2)
                except queue.Empty:
                    continue
                recognizer.AcceptWaveform(data)

        result = json.loads(recognizer.FinalResult())
        return result.get("text", "").strip()
