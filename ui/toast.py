from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QWidget


class Toast(QLabel):
    def __init__(self, text: str, kind: str, parent: QWidget) -> None:
        super().__init__(text, parent)
        self.setObjectName(f"Toast{kind.capitalize()}")
        self.setWordWrap(True)
        self.setMaximumWidth(360)
        self.adjustSize()


class ToastManager(QWidget):
    """A transparent overlay that stacks toast notifications in the
    bottom-right corner of `parent`. Call show_toast() to display one."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._active: List[Toast] = []
        self.setGeometry(parent.rect())
        self.show()

    def show_toast(self, message: str, kind: str = "info", duration_ms: int = 3500) -> None:
        toast = Toast(message, kind, self)
        toast.adjustSize()
        toast.show()
        self._active.append(toast)
        self._relayout()
        self.raise_()

        QTimer.singleShot(duration_ms, lambda: self._remove(toast))

    def _remove(self, toast: Toast) -> None:
        if toast in self._active:
            self._active.remove(toast)
        toast.deleteLater()
        self._relayout()

    def _relayout(self) -> None:
        margin = 20
        spacing = 10
        y = self.height() - margin

        for toast in reversed(self._active):
            y -= toast.height()
            x = self.width() - toast.width() - margin
            toast.move(max(0, x), max(0, y))
            y -= spacing

    def sync_geometry(self) -> None:
        if self.parent() is not None:
            self.setGeometry(self.parent().rect())
        self._relayout()
