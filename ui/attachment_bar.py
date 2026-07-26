from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from attachments.manager import Attachment, make_attachment


class AttachmentChip(QFrame):
    remove_clicked = Signal()

    def __init__(self, attachment: Attachment, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.attachment = attachment
        self.setObjectName("AttachmentChip")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        if attachment.kind == "image":
            pixmap = QPixmap(attachment.path)
            if not pixmap.isNull():
                thumb = QLabel()
                thumb.setPixmap(
                    pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                layout.addWidget(thumb)

        icon = "🖼" if attachment.kind == "image" else "📄"
        label = QLabel(f"{icon} {attachment.name}")
        label.setObjectName("AttachmentChipLabel")
        layout.addWidget(label)

        remove_btn = QPushButton("×")
        remove_btn.setObjectName("AttachmentChipRemove")
        remove_btn.setFixedSize(18, 18)
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.clicked.connect(self.remove_clicked.emit)
        layout.addWidget(remove_btn)


class AttachmentBar(QWidget):
    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._attachments: List[Attachment] = []

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 6)
        self._layout.setSpacing(8)
        self._layout.addStretch(1)

        self.hide()

    def add_path(self, path: str) -> None:
        attachment = make_attachment(path)
        self._attachments.append(attachment)

        chip = AttachmentChip(attachment)
        chip.remove_clicked.connect(lambda a=attachment: self._remove(a))
        self._layout.insertWidget(self._layout.count() - 1, chip)

        self.show()
        self.changed.emit()

    def _remove(self, attachment: Attachment) -> None:
        if attachment in self._attachments:
            self._attachments.remove(attachment)

        for i in range(self._layout.count()):
            item = self._layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, AttachmentChip) and widget.attachment is attachment:
                self._layout.takeAt(i)
                widget.deleteLater()
                break

        if not self._attachments:
            self.hide()
        self.changed.emit()

    def get_attachments(self) -> List[Attachment]:
        return list(self._attachments)

    def clear(self) -> None:
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._attachments.clear()
        self.hide()
