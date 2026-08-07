from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QUrl, Qt, QTimer, Signal
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QWidget

_CHARACTER_DIR = Path(__file__).resolve().parent.parent / "character"


class _CharacterPage(QWebEnginePage):
    """QWebEnginePage subclass so we can see JS console errors in the log
    instead of them vanishing silently — makes future debugging much
    easier if a VRM fails to load."""

    def __init__(self, logger, parent=None) -> None:
        super().__init__(parent)
        self._logger = logger

    def javaScriptConsoleMessage(self, level, message, line, source) -> None:  # noqa: N802
        if self._logger is not None:
            self._logger.debug("Character view JS: %s (line %s)", message, line)


class CharacterWindow(QWidget):
    """Frameless, transparent, always-on-top desktop window that renders
    Arcelia's VRM avatar using three.js + @pixiv/three-vrm inside a
    QWebEngineView. Controlled entirely from Python via small JS calls
    (no QWebChannel needed — the JS surface is tiny: load a model, flap
    the mouth while speaking, play a named expression)."""

    vrm_load_result = Signal(bool, str)  # (ok, error_message)

    def __init__(self, vrm_path: str = "", logger=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Arcelia — Character")
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(360, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._logger = logger
        self.view = QWebEngineView(self)
        self.view.setAttribute(Qt.WA_TranslucentBackground)
        self._page = _CharacterPage(logger, self.view)
        self._page.setBackgroundColor(Qt.transparent)
        self.view.setPage(self._page)
        layout.addWidget(self.view)

        self._pending_vrm_path = vrm_path
        self._load_timeout_timer: QTimer | None = None
        self.view.loadFinished.connect(self._on_load_finished)
        self.view.titleChanged.connect(self._on_title_changed)

        index_path = _CHARACTER_DIR / "index.html"
        self.view.load(QUrl.fromLocalFile(str(index_path)))

        # Let the user drag the (frameless) window around by its content.
        self._drag_offset = None

    def _on_load_finished(self, ok: bool) -> None:
        if not ok:
            if self._logger is not None:
                self._logger.error("Character window gagal load index.html")
            return
        if self._pending_vrm_path:
            self.load_vrm(self._pending_vrm_path)

    def load_vrm(self, vrm_path: str) -> None:
        self._pending_vrm_path = vrm_path

        if not Path(vrm_path).exists():
            msg = f"File tidak ditemukan: {vrm_path}"
            if self._logger is not None:
                self._logger.error("VRM load gagal: %s", msg)
            self.vrm_load_result.emit(False, msg)
            return

        url = QUrl.fromLocalFile(vrm_path).toString()
        # Fire-and-forget: viewer.js reports the result itself by setting
        # document.title (a plain synchronous DOM write), which we pick up
        # via titleChanged below. Relying on runJavaScript()'s own Promise
        # -awaiting callback turned out to be unreliable in testing — it
        # can silently return an empty result even for a resolved Promise
        # — so we deliberately don't depend on it for anything important.
        self._page.runJavaScript(f"window.loadVRM && window.loadVRM('{url}');")

        self._load_timeout_timer = QTimer(self)
        self._load_timeout_timer.setSingleShot(True)
        self._load_timeout_timer.timeout.connect(lambda p=vrm_path: self._on_load_timeout(p))
        self._load_timeout_timer.start(15000)

    def _on_load_timeout(self, vrm_path: str) -> None:
        if vrm_path != self._pending_vrm_path:
            return  # superseded by a newer load_vrm() call, ignore
        msg = (
            "Timeout menunggu jendela karakter merespons (15 detik) — "
            "kemungkinan WebGL gagal diinisialisasi di sistem kamu, atau "
            "file model terlalu besar/rusak."
        )
        if self._logger is not None:
            self._logger.error("VRM load timeout: %s", msg)
        self.vrm_load_result.emit(False, msg)

    def _on_title_changed(self, title: str) -> None:
        if title.startswith("arcelia-character-init-failed:"):
            if self._load_timeout_timer is not None and self._load_timeout_timer.isActive():
                self._load_timeout_timer.stop()
            msg = title[len("arcelia-character-init-failed:"):]
            if self._logger is not None:
                self._logger.error("Jendela karakter gagal init: %s", msg)
            self.vrm_load_result.emit(False, f"Gagal inisialisasi tampilan 3D: {msg}")
            return

        if not title.startswith("vrm-load-result:"):
            return

        if self._load_timeout_timer is not None and self._load_timeout_timer.isActive():
            self._load_timeout_timer.stop()

        payload = title[len("vrm-load-result:"):]
        try:
            result = json.loads(payload)
        except Exception as e:
            msg = f"Respons dari jendela karakter tidak valid: {e}"
            if self._logger is not None:
                self._logger.error("VRM load gagal: %s", msg)
            self.vrm_load_result.emit(False, msg)
            return

        ok = bool(result.get("ok"))
        error = result.get("error", "")
        if self._logger is not None:
            if ok:
                self._logger.info("VRM berhasil dimuat: %s", self._pending_vrm_path)
            else:
                self._logger.error("VRM gagal dimuat: %s", error)
        self.vrm_load_result.emit(ok, error)

    def set_speaking(self, speaking: bool) -> None:
        value = "true" if speaking else "false"
        self._page.runJavaScript(f"window.setSpeaking && window.setSpeaking({value});")

    def play_expression(self, name: str, weight: float = 1.0) -> None:
        self._page.runJavaScript(f"window.playExpression && window.playExpression('{name}', {weight});")

    # -- Drag-to-move support (frameless windows have no title bar) --

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_offset = None
