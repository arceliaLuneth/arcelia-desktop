from __future__ import annotations

from typing import Any, Dict, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFrame,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Sidebar(QFrame):
    new_chat_clicked = Signal()
    conversation_selected = Signal(int)
    rename_requested = Signal(int, str)
    delete_requested = Signal(int)
    pin_toggled = Signal(int)
    search_changed = Signal(str)
    export_clicked = Signal()
    import_clicked = Signal()
    settings_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        title = QLabel("Arcelia")
        title.setObjectName("SidebarTitle")

        subtitle = QLabel("AI Desktop Assistant")
        subtitle.setObjectName("SidebarSubtitle")

        header = QVBoxLayout()
        header.setSpacing(2)
        header.addWidget(title)
        header.addWidget(subtitle)

        self.new_chat_btn = QPushButton("＋ New chat")
        self.new_chat_btn.setObjectName("PrimaryButton")
        self.new_chat_btn.clicked.connect(self.new_chat_clicked.emit)

        self.search_box = QLineEdit()
        self.search_box.setObjectName("SearchBox")
        self.search_box.setPlaceholderText("Cari chat...")
        self.search_box.textChanged.connect(self.search_changed.emit)

        history_label = QLabel("HISTORY")
        history_label.setObjectName("SectionLabel")

        self.history_list = QListWidget()
        self.history_list.setObjectName("HistoryList")
        self.history_list.itemClicked.connect(self._on_item_clicked)
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self._open_context_menu)

        tools_label = QLabel("TOOLS")
        tools_label.setObjectName("SectionLabel")

        self.export_btn = QPushButton("Export chat")
        self.export_btn.setObjectName("SecondaryButton")
        self.export_btn.clicked.connect(self.export_clicked.emit)

        self.import_btn = QPushButton("Import chat")
        self.import_btn.setObjectName("SecondaryButton")
        self.import_btn.clicked.connect(self.import_clicked.emit)

        settings_btn = QPushButton("Settings")
        settings_btn.setObjectName("SecondaryButton")
        settings_btn.clicked.connect(self.settings_clicked.emit)

        self.session_stats_label = QLabel("")
        self.session_stats_label.setObjectName("SessionStats")
        self.session_stats_label.setAlignment(Qt.AlignCenter)

        layout.addLayout(header)
        layout.addWidget(self.new_chat_btn)
        layout.addWidget(self.search_box)
        layout.addWidget(history_label)
        layout.addWidget(self.history_list, 1)
        layout.addWidget(tools_label)
        layout.addWidget(self.export_btn)
        layout.addWidget(self.import_btn)
        layout.addWidget(settings_btn)
        layout.addWidget(self.session_stats_label)

    def set_session_stats(self, text: str) -> None:
        self.session_stats_label.setText(text)

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

    def clear_search(self) -> None:
        self.search_box.blockSignals(True)
        self.search_box.clear()
        self.search_box.blockSignals(False)

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
            self.delete_requested.emit(conversation_id)
