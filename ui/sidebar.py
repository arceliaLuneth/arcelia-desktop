from __future__ import annotations

from typing import Any, Dict, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFrame,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class Sidebar(QFrame):
    new_chat_clicked = Signal()
    conversation_selected = Signal(int)
    rename_requested = Signal(int, str)
    delete_requested = Signal(int)
    pin_toggled = Signal(int)
    export_clicked = Signal()
    import_clicked = Signal()
    settings_clicked = Signal()
    shortcuts_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Arcelia")
        title.setObjectName("SidebarTitle")

        self.new_chat_btn = QPushButton("＋  New chat")
        self.new_chat_btn.setObjectName("PrimaryButton")
        self.new_chat_btn.clicked.connect(self.new_chat_clicked.emit)

        self.history_list = QListWidget()
        self.history_list.setObjectName("HistoryList")
        self.history_list.itemClicked.connect(self._on_item_clicked)
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self._open_context_menu)

        # Secondary actions (export/import/settings/shortcuts) are used
        # rarely — tucked behind one compact menu instead of four
        # always-visible buttons, so the sidebar stays focused on the
        # thing people actually look at most: the chat history.
        self.more_btn = QToolButton()
        self.more_btn.setObjectName("MoreButton")
        self.more_btn.setText("⋯  More")
        self.more_btn.setPopupMode(QToolButton.InstantPopup)
        self.more_btn.setCursor(Qt.PointingHandCursor)

        more_menu = QMenu(self.more_btn)
        more_menu.addAction("Export chat", self.export_clicked.emit)
        more_menu.addAction("Import chat", self.import_clicked.emit)
        more_menu.addSeparator()
        more_menu.addAction("Keyboard shortcuts", self.shortcuts_clicked.emit)
        more_menu.addAction("Settings", self.settings_clicked.emit)
        self.more_btn.setMenu(more_menu)

        layout.addWidget(title)
        layout.addWidget(self.new_chat_btn)
        layout.addWidget(self.history_list, 1)
        layout.addWidget(self.more_btn)

    def set_conversations(self, conversations: List[Dict[str, Any]]) -> None:
        current_id = self.current_conversation_id()

        self.history_list.blockSignals(True)
        self.history_list.clear()

        selected_item = None

        for conv in conversations:
            label = conv["title"]
            if conv.get("pinned"):
                label = f"📌 {label}"

            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, int(conv["id"]))
            self.history_list.addItem(item)

            if current_id is not None and int(conv["id"]) == current_id:
                selected_item = item

        self.history_list.blockSignals(False)

        if selected_item is not None:
            self.history_list.setCurrentItem(selected_item)

    def current_conversation_id(self) -> int | None:
        item = self.history_list.currentItem()
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def select_conversation(self, conversation_id: int) -> None:
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            if int(item.data(Qt.UserRole)) == conversation_id:
                self.history_list.setCurrentItem(item)
                return

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        conversation_id = item.data(Qt.UserRole)
        if conversation_id is not None:
            self.conversation_selected.emit(int(conversation_id))

    def _open_context_menu(self, pos) -> None:
        item = self.history_list.itemAt(pos)
        if item is None:
            return

        conversation_id = int(item.data(Qt.UserRole))
        menu = QMenu(self)

        pin_action = QAction("Unpin" if item.text().startswith("📌") else "Pin", self)
        rename_action = QAction("Rename", self)
        delete_action = QAction("Delete", self)

        menu.addAction(pin_action)
        menu.addAction(rename_action)
        menu.addAction(delete_action)

        chosen = menu.exec(self.history_list.mapToGlobal(pos))

        if chosen == pin_action:
            self.pin_toggled.emit(conversation_id)

        elif chosen == rename_action:
            current_title = item.text().replace("📌 ", "", 1)
            new_title, ok = QInputDialog.getText(
                self,
                "Rename chat",
                "New title:",
                text=current_title,
            )
            if ok and new_title.strip():
                self.rename_requested.emit(conversation_id, new_title.strip())

        elif chosen == delete_action:
            current_title = item.text().replace("📌 ", "", 1)
            confirm = QMessageBox.question(
                self,
                "Hapus chat?",
                f'Hapus percakapan "{current_title}"?\n\nIni tidak bisa dibatalkan — seluruh isi chat akan hilang permanen.',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if confirm == QMessageBox.Yes:
                self.delete_requested.emit(conversation_id)
