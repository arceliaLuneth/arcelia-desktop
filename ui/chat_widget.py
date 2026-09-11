from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from attachments.manager import Attachment
from ui.attachment_bar import AttachmentBar
from ui.markdown_render import render_markdown


class PromptInput(QTextEdit):
    send_requested = Signal()

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            event.accept()
            self.send_requested.emit()
            return
        super().keyPressEvent(event)


class MessageBubble(QFrame):
    edit_clicked = Signal()
    regenerate_clicked = Signal()

    ASSISTANT_TEXT_WIDTH = 720  # capped reading width, Claude/ChatGPT-style

    def __init__(
        self,
        text: str,
        role: str = "assistant",
        attachments: Optional[List[Attachment]] = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.role = role
        self._raw_text = ""
        self._code_blocks: dict[str, str] = {}
        self._stats_text = ""
        self._regenerate_eligible = False

        # Only user messages get the "bubble" box treatment now — assistant
        # replies render as plain flowing text (Claude/ChatGPT-style),
        # distinguished by left alignment + the small "ARCELIA" label
        # instead of a background/border.
        self.setObjectName("BubbleUser" if role == "user" else "PlainAssistant")
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.setMaximumWidth(self.ASSISTANT_TEXT_WIDTH if role == "assistant" else 760)
        self.setAttribute(Qt.WA_Hover, True)

        layout = QVBoxLayout(self)
        if role == "assistant":
            layout.setContentsMargins(4, 4, 4, 4)
        else:
            layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        role_label = QLabel("YOU" if role == "user" else "ARCELIA")
        role_label.setObjectName("MessageRole")
        layout.addWidget(role_label)

        if role == "user" and attachments:
            attach_row = QHBoxLayout()
            attach_row.setSpacing(6)
            for att in attachments:
                if att.kind == "image":
                    pixmap = QPixmap(att.path)
                    if not pixmap.isNull():
                        thumb = QLabel()
                        thumb.setObjectName("AttachmentThumb")
                        thumb.setPixmap(
                            pixmap.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        )
                        attach_row.addWidget(thumb)
                        continue
                chip = QLabel(f"📄 {att.name}")
                chip.setObjectName("AttachmentChipLabel")
                attach_row.addWidget(chip)
            attach_row.addStretch(1)
            layout.addLayout(attach_row)

        if role == "assistant":
            self.body = QTextBrowser()
            self.body.setObjectName("PlainTextAssistant")
            self.body.setFrameShape(QFrame.NoFrame)
            self.body.setOpenLinks(False)
            self.body.setOpenExternalLinks(False)
            self.body.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.body.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.body.anchorClicked.connect(self._handle_anchor_click)
            self.body.document().documentLayout().documentSizeChanged.connect(
                self._adjust_body_height
            )
        else:
            self.body = QLabel(text)
            self.body.setWordWrap(True)
            self.body.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.body.setTextFormat(Qt.PlainText)
            self.body.setObjectName("BubbleTextUser")

        layout.addWidget(self.body)

        # Action icons (Copy / Edit / Regenerate) are icon-only and only
        # shown on hover — Claude/ChatGPT-style, instead of a permanently
        # visible text button that competes with the message content.
        meta_row = QHBoxLayout()
        meta_row.setSpacing(4)

        self._action_buttons: List[QPushButton] = []

        if role == "assistant":
            copy_btn = self._make_icon_button("⧉", "Copy")
            copy_btn.clicked.connect(self._copy_full_text)
            meta_row.addWidget(copy_btn)

            self.regenerate_btn = self._make_icon_button("↻", "Regenerate response")
            self.regenerate_btn.clicked.connect(self.regenerate_clicked.emit)
            self.regenerate_btn.hide()  # only shown for the latest reply, via set_regenerate_eligible()
            meta_row.addWidget(self.regenerate_btn)
        else:
            self.regenerate_btn = None
            edit_btn = self._make_icon_button("✎", "Edit")
            edit_btn.clicked.connect(self.edit_clicked.emit)
            meta_row.addWidget(edit_btn)

        meta_row.addStretch(1)

        self.meta_label = QLabel(datetime.now().strftime("%H:%M"))
        self.meta_label.setObjectName("Timestamp")
        meta_row.addWidget(self.meta_label)

        layout.addLayout(meta_row)
        self.stats_label = None  # kept for API compat

        self._set_actions_visible(False)
        self.set_text(text)

    def _make_icon_button(self, icon: str, tooltip: str) -> QPushButton:
        btn = QPushButton(icon)
        btn.setObjectName("BubbleIconButton")
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(26, 22)
        self._action_buttons.append(btn)
        return btn

    def _set_actions_visible(self, visible: bool) -> None:
        for btn in self._action_buttons:
            btn.setVisible(visible)
        if self.regenerate_btn is not None:
            self.regenerate_btn.setVisible(visible and self._regenerate_eligible)

    def enterEvent(self, event) -> None:
        self._set_actions_visible(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._set_actions_visible(False)
        super().leaveEvent(event)

    def set_regenerate_eligible(self, eligible: bool) -> None:
        """Only the most recent assistant reply should offer 'Regenerate' —
        ChatWidget calls this to turn it on/off as new messages arrive."""
        self._regenerate_eligible = eligible
        if self.regenerate_btn is not None:
            self.regenerate_btn.setVisible(False)  # only reveal again on next hover

    def set_stats(self, stats_text: str) -> None:
        if self.role != "assistant" or not stats_text:
            return
        self._stats_text = stats_text
        timestamp = datetime.now().strftime("%H:%M")
        self.meta_label.setText(f"{timestamp} · {stats_text}")

    def set_text(self, text: str) -> None:
        self._raw_text = text

        if self.role == "assistant":
            html_content, code_blocks = render_markdown(text if text else " ")
            self._code_blocks = code_blocks
            self.body.document().setTextWidth(self.ASSISTANT_TEXT_WIDTH - 8)
            self.body.setHtml(html_content)
            self._adjust_body_height()
        else:
            self.body.setText(text)
            self.body.adjustSize()

        self.adjustSize()

    def _adjust_body_height(self) -> None:
        doc_height = self.body.document().size().height()
        self.body.setFixedHeight(max(24, int(doc_height) + 12))
        self.adjustSize()

    def _handle_anchor_click(self, url: QUrl) -> None:
        if url.scheme() != "copy":
            return
        block_id = url.toString().split(":", 1)[-1]
        code = self._code_blocks.get(block_id, "")
        if code:
            QGuiApplication.clipboard().setText(code)

    def _copy_full_text(self) -> None:
        QGuiApplication.clipboard().setText(self._raw_text)


class TypingIndicator(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TypingBubble")
        self.setMaximumWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self._base_text = "Arcelia sedang mengetik"
        self._dot_frames = ["", ".", "..", "..."]
        self._dot_index = 0

        self.text_label = QLabel(self._base_text)
        self.text_label.setObjectName("TypingBubbleText")

        ts = QLabel(datetime.now().strftime("%H:%M"))
        ts.setObjectName("Timestamp")

        layout.addWidget(self.text_label)
        layout.addWidget(ts, alignment=Qt.AlignRight)

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick)
        self._anim_timer.start(400)

    def _tick(self) -> None:
        self._dot_index = (self._dot_index + 1) % len(self._dot_frames)
        self.text_label.setText(self._base_text + self._dot_frames[self._dot_index])

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._anim_timer.isActive():
            self._anim_timer.start(400)

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        self._anim_timer.stop()  # no point animating an invisible widget


class ChatWidget(QWidget):
    message_sent = Signal(str, list)
    stop_requested = Signal()
    regenerate_requested = Signal()
    edit_requested = Signal(str, int)
    model_changed = Signal(str)
    retry_connection_requested = Signal()
    voice_toggled = Signal(bool)
    mic_toggled = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ChatPanel")
        self.setAcceptDrops(True)

        self._streaming_row: QWidget | None = None
        self._streaming_bubble: MessageBubble | None = None
        self._streaming_text: str = ""
        self._is_generating = False
        self._message_index = 0
        self._last_assistant_bubble: MessageBubble | None = None

        # Streaming text arrives token-by-token; re-rendering markdown +
        # syntax highlighting on every single token is O(n^2) over the
        # length of the reply. Coalesce into a max ~12 renders/sec instead.
        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self._flush_streaming_render)
        self._pending_render = False

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 22)
        root.setSpacing(14)

        header = QHBoxLayout()
        header.setSpacing(10)
        header.setContentsMargins(2, 0, 2, 0)

        self.model_selector = QComboBox()
        self.model_selector.setObjectName("ModelSelector")
        self.model_selector.setMinimumWidth(140)
        self.model_selector.currentTextChanged.connect(self.model_changed.emit)

        self.voice_toggle = QPushButton("🔇")
        self.voice_toggle.setObjectName("GhostButton")
        self.voice_toggle.setFixedWidth(40)
        self.voice_toggle.setCheckable(True)
        self.voice_toggle.setToolTip("Aktifkan/matikan suara Arcelia")
        self.voice_toggle.setCursor(Qt.PointingHandCursor)
        self.voice_toggle.toggled.connect(self._on_voice_toggled)

        header.addWidget(self.model_selector)
        header.addStretch(1)
        header.addWidget(self.voice_toggle)

        root.addLayout(header)

        self.connection_banner = QFrame()
        self.connection_banner.setObjectName("ConnectionBanner")
        banner_layout = QHBoxLayout(self.connection_banner)
        banner_layout.setContentsMargins(14, 10, 14, 10)
        self.connection_banner_text = QLabel("")
        self.connection_banner_text.setObjectName("ConnectionBannerText")
        self.connection_banner_text.setWordWrap(True)
        retry_btn = QPushButton("Coba lagi")
        retry_btn.setObjectName("GhostButton")
        retry_btn.clicked.connect(self.retry_connection_requested.emit)
        banner_layout.addWidget(self.connection_banner_text, 1)
        banner_layout.addWidget(retry_btn)
        self.connection_banner.hide()
        root.addWidget(self.connection_banner)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("MessagesScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        
        self.MAX_CONTENT_WIDTH = 820

        scroll_outer = QWidget()
        scroll_outer.setObjectName("MessagesScrollOuter")
        outer_layout = QHBoxLayout(scroll_outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.message_container = QWidget()
        self.message_container.setObjectName("MessagesContainer")
        self.message_container.setMaximumWidth(self.MAX_CONTENT_WIDTH)
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setContentsMargins(6, 6, 6, 6)
        self.message_layout.setSpacing(12)
        self.message_layout.addStretch(1)

        outer_layout.addStretch(1)
        outer_layout.addWidget(self.message_container)
        outer_layout.addStretch(1)

        self.scroll.setWidget(scroll_outer)
        root.addWidget(self.scroll, 1)

        # Typing indicator row: kept as the LAST layout item (after the
        # stretch, which stays first) so add_message()'s "insert before the
        # last item" logic always keeps it pinned at the bottom, right above
        # the composer, instead of stuck above every message.
        self.typing_widget = TypingIndicator()
        self.typing_widget.hide()
        self.typing_row = QWidget()
        typing_row_layout = QHBoxLayout(self.typing_row)
        typing_row_layout.setContentsMargins(0, 0, 0, 0)
        typing_row_layout.setSpacing(0)
        typing_row_layout.addWidget(self.typing_widget)
        typing_row_layout.addStretch(1)
        self.message_layout.addWidget(self.typing_row)

        self.attachment_bar = AttachmentBar()
        root.addWidget(self.attachment_bar)

        composer = QFrame()
        composer.setObjectName("Composer")
        composer_layout = QHBoxLayout(composer)
        composer_layout.setContentsMargins(14, 14, 14, 14)
        composer_layout.setSpacing(10)

        self.attach_button = QPushButton("＋")
        self.attach_button.setObjectName("GhostButton")
        self.attach_button.setFixedWidth(52)
        self.attach_button.setCursor(Qt.PointingHandCursor)
        self.attach_button.clicked.connect(self._pick_files)

        self.mic_button = QPushButton("🎤")
        self.mic_button.setObjectName("GhostButton")
        self.mic_button.setFixedWidth(52)
        self.mic_button.setCheckable(True)
        self.mic_button.setCursor(Qt.PointingHandCursor)
        self.mic_button.setToolTip("Rekam suara — klik lagi untuk berhenti")
        self.mic_button.toggled.connect(self.mic_toggled.emit)

        self.input = PromptInput()
        self.input.setObjectName("PromptInput")
        self.input.setPlaceholderText("Tulis pesan di sini...  (Enter untuk kirim, Shift+Enter untuk baris baru)")
        self.input.setFixedHeight(64)
        self.input.send_requested.connect(self.send_message)

        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("SendButton")
        self.send_button.setFixedWidth(120)
        self.send_button.clicked.connect(self.send_message)

        composer_layout.addWidget(self.attach_button)
        composer_layout.addWidget(self.mic_button)
        composer_layout.addWidget(self.input, 1)
        composer_layout.addWidget(self.send_button)

        root.addWidget(composer)

    def _refresh_view(self) -> None:
        if self._streaming_bubble is not None:
            self._streaming_bubble.adjustSize()
        self.message_container.adjustSize()
        self.scroll_to_bottom(force=False)

    def _animate_fade_in(self, widget: QWidget) -> None:
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setDuration(220)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _mark_latest_assistant_bubble(self, bubble: "MessageBubble") -> None:
        if self._last_assistant_bubble is not None:
            self._last_assistant_bubble.set_regenerate_eligible(False)
        self._last_assistant_bubble = bubble
        bubble.set_regenerate_eligible(True)

    def add_message(
        self,
        text: str,
        role: str = "assistant",
        track: bool = True,
        attachments: Optional[List[Attachment]] = None,
    ) -> None:
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)

        bubble = MessageBubble(text, role=role, attachments=attachments)

        if role == "user" and track:
            idx = self._message_index
            bubble.edit_clicked.connect(lambda: self.edit_requested.emit(text, idx))

        if role == "assistant":
            bubble.regenerate_clicked.connect(self.regenerate_requested.emit)
            self._mark_latest_assistant_bubble(bubble)

        if role == "user":
            row_layout.addStretch(1)
            row_layout.addWidget(bubble)
        else:
            row_layout.addWidget(bubble)
            row_layout.addStretch(1)

        insert_at = max(0, self.message_layout.count() - 1)
        self.message_layout.insertWidget(insert_at, row)
        self._animate_fade_in(bubble)

        if track:
            self._message_index += 1

        QTimer.singleShot(0, self.scroll_to_bottom)

    def clear_messages(self) -> None:
        self.discard_streaming_reply()
        self._message_index = 0
        self._last_assistant_bubble = None

        # Remove every row except the fixed typing_row and the stretch.
        keep = {self.typing_row}
        i = 0
        while i < self.message_layout.count():
            item = self.message_layout.itemAt(i)
            widget = item.widget()
            if widget is not None and widget not in keep:
                self.message_layout.takeAt(i)
                widget.deleteLater()
            else:
                i += 1

        self.scroll_to_bottom()

    def begin_streaming_reply(self) -> None:
        self.discard_streaming_reply()
        if self._last_assistant_bubble is not None:
            self._last_assistant_bubble.set_regenerate_eligible(False)
            self._last_assistant_bubble = None

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)

        bubble = MessageBubble("", role="assistant")
        bubble.setMaximumWidth(MessageBubble.ASSISTANT_TEXT_WIDTH)
        bubble.regenerate_clicked.connect(self.regenerate_requested.emit)

        row_layout.addWidget(bubble)
        row_layout.addStretch(1)

        insert_at = max(0, self.message_layout.count() - 1)
        self.message_layout.insertWidget(insert_at, row)
        self._animate_fade_in(bubble)

        self._streaming_row = row
        self._streaming_bubble = bubble
        self._streaming_text = ""

        self.message_container.adjustSize()
        self.scroll_to_bottom(force=True)

    def append_streaming_text(self, chunk: str) -> None:
        if self._streaming_bubble is None:
            return

        self._streaming_text += chunk
        self._pending_render = True
        if not self._render_timer.isActive():
            self._render_timer.start(80)  # ~12 renders/sec max, not one per token

    def _flush_streaming_render(self) -> None:
        if self._streaming_bubble is None or not self._pending_render:
            return
        self._streaming_bubble.set_text(self._streaming_text)
        self._pending_render = False
        self._refresh_view()

    def finish_streaming_reply(self, final_text: str | None = None, stats_text: str = "") -> None:
        if self._streaming_bubble is None:
            return

        self._render_timer.stop()
        self._pending_render = False

        if final_text is not None:
            self._streaming_text = final_text

        final_text_clean = self._streaming_text.strip()
        if not final_text_clean:
            final_text_clean = "..."

        self._streaming_bubble.set_text(final_text_clean)
        if stats_text:
            self._streaming_bubble.set_stats(stats_text)
        self._mark_latest_assistant_bubble(self._streaming_bubble)
        self.message_container.adjustSize()
        self.scroll_to_bottom(force=True)

        self._streaming_row = None
        self._streaming_bubble = None
        self._streaming_text = ""

    def discard_streaming_reply(self) -> None:
        self._render_timer.stop()
        self._pending_render = False

        if self._streaming_row is not None:
            self._streaming_row.setParent(None)
            self._streaming_row.deleteLater()

        self._streaming_row = None
        self._streaming_bubble = None
        self._streaming_text = ""

    def remove_last_assistant_bubble(self) -> None:
        """Remove the last message row (used right before regenerating)."""
        self._last_assistant_bubble = None
        for i in range(self.message_layout.count() - 1, -1, -1):
            item = self.message_layout.itemAt(i)
            widget = item.widget()
            if widget is not None and widget is not self.typing_row:
                self.message_layout.takeAt(i)
                widget.deleteLater()
                return

    def set_typing(self, enabled: bool) -> None:
        self.typing_widget.setVisible(enabled)
        QTimer.singleShot(0, self.scroll_to_bottom)

    def show_regenerate(self, visible: bool) -> None:
        # No-op: kept so existing main_window.py call sites don't need
        # touching. Regenerate eligibility is now tracked per-bubble
        # automatically (see _mark_latest_assistant_bubble) — the hover
        # icon just reflects whichever bubble is currently "latest".
        pass

    def set_generating(self, is_generating: bool) -> None:
        self._is_generating = is_generating
        self.send_button.setText("Stop" if is_generating else "Send")
        self.send_button.setObjectName("StopButton" if is_generating else "SendButton")
        self.send_button.style().unpolish(self.send_button)
        self.send_button.style().polish(self.send_button)

    def send_message(self) -> None:
        if self._is_generating:
            self.stop_requested.emit()
            return

        text = self.input.toPlainText().strip()
        attachments = self.attachment_bar.get_attachments()
        if not text and not attachments:
            return

        self.add_message(text or "📎", role="user", attachments=attachments)
        self.input.clear()
        self.attachment_bar.clear()
        self.message_sent.emit(text, attachments)

    def _pick_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Lampirkan file")
        for path in paths:
            self.attachment_bar.add_path(path)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path:
                self.attachment_bar.add_path(path)
        event.acceptProposedAction()

    def _on_voice_toggled(self, enabled: bool) -> None:
        self.voice_toggle.setText("🔊" if enabled else "🔇")
        self.voice_toggled.emit(enabled)

    def set_voice_enabled(self, enabled: bool) -> None:
        """Set the toggle's initial state (e.g. from saved settings) without
        re-emitting voice_toggled — avoids a pointless save-loop on startup."""
        self.voice_toggle.blockSignals(True)
        self.voice_toggle.setChecked(enabled)
        self.voice_toggle.setText("🔊" if enabled else "🔇")
        self.voice_toggle.blockSignals(False)

    def set_mic_state(self, recording: bool) -> None:
        self.mic_button.blockSignals(True)
        self.mic_button.setChecked(recording)
        self.mic_button.setText("⏹" if recording else "🎤")
        self.mic_button.blockSignals(False)

    def insert_transcribed_text(self, text: str) -> None:
        if not text:
            return
        current = self.input.toPlainText()
        combined = (current + " " + text).strip() if current else text
        self.input.setPlainText(combined)
        cursor = self.input.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.input.setTextCursor(cursor)
        self.input.setFocus()

    def set_models(self, models: List[str], current: str) -> None:
        self.model_selector.blockSignals(True)
        self.model_selector.clear()
        items = list(models)
        if current and current not in items:
            items = [current] + items
        self.model_selector.addItems(items)
        if current:
            self.model_selector.setCurrentText(current)
        self.model_selector.blockSignals(False)

    def show_connection_banner(self, message: str) -> None:
        self.connection_banner_text.setText(message)
        self.connection_banner.show()

    def hide_connection_banner(self) -> None:
        self.connection_banner.hide()

    def scroll_to_bottom(self, force: bool = True) -> None:
        bar = self.scroll.verticalScrollBar()
        near_bottom = bar.value() >= bar.maximum() - 60
        if force or near_bottom:
            bar.setValue(bar.maximum())
