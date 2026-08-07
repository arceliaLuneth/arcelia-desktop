from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl, Qt, Signal
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QLabel, QStackedLayout, QVBoxLayout, QWidget

_CHARACTER_DIR = Path(__file__).resolve().parent.parent / "character"


class _CharacterPage(QWebEnginePage):
    """QWebEnginePage subclass so JS console errors reach the app log
    instead of vanishing silently."""

    def __init__(self, logger, parent=None) -> None:
        super().__init__(parent)
        self._logger = logger

    def javaScriptConsoleMessage(self, level, message, line, source) -> None:  # noqa: N802
        if self._logger is not None:
            self._logger.debug("Character view JS: %s (line %s)", message, line)


class CharacterPanel(QWidget):
    """Embedded panel (a normal child widget, NOT a floating window) that
    renders Arcelia's VRM avatar as the third column of the main layout,
    next to the sidebar and chat. Controlled from Python via small JS
    calls through page().runJavaScript() — no QWebChannel needed."""

    vrm_load_result = Signal(bool, str)  # (ok, error_message)

    def __init__(self, vrm_path: str = "", logger=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CharacterPanel")
        self.setMinimumWidth(200)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedLayout()
        self._stack.setStackingMode(QStackedLayout.StackAll)
        outer.addLayout(self._stack)

        self._logger = logger
        self.view = QWebEngineView(self)
        self._page = _CharacterPage(logger, self.view)
        self._page.setBackgroundColor(Qt.transparent)
        self.view.setPage(self._page)

        self._overlay = QLabel("")
        self._overlay.setObjectName("CharacterOverlay")
        self._overlay.setWordWrap(True)
        self._overlay.setAlignment(Qt.AlignCenter)

        # StackAll keeps both widgets alive (the view keeps rendering
        # underneath) — we just raise/lower which one is on top.
        self._stack.addWidget(self.view)
        self._stack.addWidget(self._overlay)
        self._set_overlay("Memuat karakter...")

        self._pending_vrm_path = vrm_path
        self._load_timeout_timer: QTimer | None = None
        self.view.loadFinished.connect(self._on_load_finished)
        self.view.titleChanged.connect(self._on_title_changed)
        self.vrm_load_result.connect(self._on_vrm_load_result_overlay)

        index_path = _CHARACTER_DIR / "index.html"
        self.view.load(QUrl.fromLocalFile(str(index_path)))

    def _set_overlay(self, text: str, is_error: bool = False) -> None:
        self._overlay.setText(text)
        self._overlay.setProperty("error", is_error)
        self._overlay.style().unpolish(self._overlay)
        self._overlay.style().polish(self._overlay)
        self._overlay.show()
        self._overlay.raise_()

    def _hide_overlay(self) -> None:
        self._overlay.hide()

    def _on_vrm_load_result_overlay(self, ok: bool, error: str) -> None:
        if ok:
            self._hide_overlay()
        else:
            self._set_overlay(f"Karakter gagal dimuat:\n{error}", is_error=True)

    def _on_load_finished(self, ok: bool) -> None:
        if not ok:
            if self._logger is not None:
                self._logger.error("Character panel gagal load index.html")
            return
        if self._pending_vrm_path:
            self.load_vrm(self._pending_vrm_path)

    def load_vrm(self, vrm_path: str) -> None:
        self._pending_vrm_path = vrm_path
        self._set_overlay("Memuat karakter...")

        if not Path(vrm_path).exists():
            msg = f"File tidak ditemukan: {vrm_path}"
            if self._logger is not None:
                self._logger.error("VRM load gagal: %s", msg)
            self.vrm_load_result.emit(False, msg)
            return

        url = QUrl.fromLocalFile(vrm_path).toString()
        # Fire-and-forget: viewer.js reports the result itself by setting
        # document.title (plain synchronous DOM write), picked up via
        # titleChanged below. Relying on runJavaScript()'s own Promise
        # -awaiting callback turned out to be unreliable in testing.
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
                self._logger.error("Character panel gagal init: %s", msg)
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
