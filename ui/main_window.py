from __future__ import annotations

import re
import traceback
from typing import Dict, List

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QMainWindow, QMessageBox, QWidget

from ai.client import OllamaClient
from attachments.manager import (
    Attachment,
    encode_marker,
    read_text_preview,
    split_content_and_attachments,
)
from memory.chat_manager import ChatManager
from skills.registry import SkillRegistry
from ui.chat_widget import ChatWidget
from ui.settings_dialog import SettingsDialog
from ui.sidebar import Sidebar
from ui.theme import build_stylesheet
from ui.toast import ToastManager
from utils.export_import import export_conversation, import_conversation
from utils.logger import get_logger, setup_logging
from utils.settings import AppSettings
from utils.stats import format_session_stats, format_stats

Message = Dict[str, str]


class StreamWorker(QThread):
    chunk = Signal(str)
    completed = Signal(str, bool, dict)  # (reply_text, was_stopped, stats)
    failed = Signal(str)

    def __init__(self, client: OllamaClient, messages: List[Message]) -> None:
        super().__init__()
        self.client = client
        self.messages = messages

    def run(self) -> None:
        try:
            parts: List[str] = []
            was_stopped = False
            stats: dict = {}

            for token in self.client.stream_chat(self.messages, stats=stats):
                if self.isInterruptionRequested():
                    was_stopped = True
                    break
                parts.append(token)
                self.chunk.emit(token)

            reply = "".join(parts).strip()

            if not reply and not was_stopped:
                reply = self.client.chat(self.messages).strip()

            self.completed.emit(reply, was_stopped, stats)
        except Exception as e:
            traceback.print_exc()
            self.failed.emit(str(e))


class AutoTitleWorker(QThread):
    """Asks the model for a short title for a fresh conversation, based on
    its first exchange. Runs off the UI thread since it's a blocking
    (non-streaming) Ollama call."""

    title_ready = Signal(int, str)

    def __init__(self, client: OllamaClient, conversation_id: int, user_text: str, assistant_text: str) -> None:
        super().__init__()
        self.client = client
        self.conversation_id = conversation_id
        self.user_text = user_text
        self.assistant_text = assistant_text

    def run(self) -> None:
        try:
            prompt = (
                "Buatkan judul singkat (maksimal 5 kata, tanpa tanda kutip, "
                "tanpa titik di akhir) untuk percakapan berikut. Balas HANYA "
                "dengan judulnya, tanpa penjelasan lain.\n\n"
                f"User: {self.user_text}\nAsisten: {self.assistant_text}"
            )
            raw_title = self.client.chat([{"role": "user", "content": prompt}])
            title = raw_title.strip().strip('"').strip("'").splitlines()[0].strip()
            title = title[:60]
            if title:
                self.title_ready.emit(self.conversation_id, title)
        except Exception:
            pass  # Auto-rename is a nice-to-have; silently skip on failure.


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Arcelia")
        self.resize(1400, 900)
        self.setMinimumSize(1100, 720)

        self.settings = AppSettings.load()
        self.logger = setup_logging(debug=self.settings.debug_mode)
        self.logger.info("Arcelia starting up")

        self.ollama = OllamaClient(
            model=self.settings.model,
            host=self.settings.ollama_host,
            system_prompt=self.settings.system_prompt,
        )
        self.chat_manager = ChatManager()
        self.skills = SkillRegistry()
        self._worker: StreamWorker | None = None
        self._title_workers: List[AutoTitleWorker] = []
        self._session_replies = 0
        self._session_tokens = 0

        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = Sidebar()
        self.chat_widget = ChatWidget()

        root.addWidget(self.sidebar)
        root.addWidget(self.chat_widget, 1)

        self.sidebar.new_chat_clicked.connect(self.handle_new_chat)
        self.sidebar.conversation_selected.connect(self.handle_conversation_selected)
        self.sidebar.rename_requested.connect(self.handle_rename_requested)
        self.sidebar.delete_requested.connect(self.handle_delete_requested)
        self.sidebar.pin_toggled.connect(self.handle_pin_toggled)
        self.sidebar.search_changed.connect(self.handle_search_changed)
        self.sidebar.export_clicked.connect(self.handle_export)
        self.sidebar.import_clicked.connect(self.handle_import)
        self.sidebar.settings_clicked.connect(self.handle_open_settings)
        self.chat_widget.message_sent.connect(self.handle_user_message)
        self.chat_widget.stop_requested.connect(self.handle_stop_generating)
        self.chat_widget.regenerate_requested.connect(self.handle_regenerate)
        self.chat_widget.edit_requested.connect(self.handle_edit_requested)
        self.chat_widget.model_changed.connect(self.handle_model_changed)
        self.chat_widget.retry_connection_requested.connect(self.check_ollama_connection)

        self.apply_theme()
        self.refresh_sidebar()

        self.toasts = ToastManager(central)
        self._register_shortcuts()

        # Deferred (not called directly) so MainWindow.__init__() returns and
        # main.py's window.show() runs before this blocking network check —
        # otherwise a slow/unreachable Ollama host would freeze the whole
        # app before the window ever appears.
        QTimer.singleShot(0, lambda: self.check_ollama_connection(initial=True))

        conversations = self.chat_manager.get_chat_list()
        if conversations:
            first_id = int(conversations[0]["id"])
            self.load_conversation(first_id)
        else:
            self.start_fresh_chat()

    def apply_theme(self) -> None:
        self.setStyleSheet(build_stylesheet(self.settings.theme))

    def check_ollama_connection(self, initial: bool = False) -> None:
        available = self.ollama.is_available()
        if available:
            self.chat_widget.hide_connection_banner()
            try:
                models = self.ollama.list_models()
                self.chat_widget.set_models(models, self.ollama.model)
            except Exception as e:
                self.logger.warning("Gagal mengambil daftar model: %s", e)
            if not initial:
                self.toasts.show_toast("Terhubung ke Ollama", kind="success")
            self.logger.info("Ollama terhubung di %s", self.settings.ollama_host)
        else:
            message = (
                f"Tidak bisa terhubung ke Ollama di {self.settings.ollama_host}. "
                "Pastikan Ollama sudah jalan (`ollama serve` atau systemd service-nya)."
            )
            self.chat_widget.show_connection_banner(message)
            self.chat_widget.set_models([self.ollama.model], self.ollama.model)
            self.logger.warning("Ollama tidak terhubung di %s", self.settings.ollama_host)

    def handle_model_changed(self, model_name: str) -> None:
        if not model_name or model_name == self.ollama.model:
            return
        self.ollama.model = model_name
        self.settings.model = model_name
        self.settings.save()
        self.logger.info("Model default diganti ke %s", model_name)
        self.toasts.show_toast(f"Model diganti ke {model_name}", kind="info")

    def handle_open_settings(self) -> None:
        available_models: List[str] = []
        try:
            available_models = self.ollama.list_models()
        except Exception as e:
            self.logger.warning("Gagal mengambil daftar model untuk Settings: %s", e)

        dialog = SettingsDialog(self.settings, available_models, parent=self)
        if dialog.exec():
            new_settings = dialog.result_settings()
            if new_settings is None:
                return

            host_changed = new_settings.ollama_host != self.settings.ollama_host
            theme_changed = new_settings.theme != self.settings.theme

            self.settings = new_settings
            self.settings.save()

            self.ollama.model = self.settings.model
            self.ollama.system_prompt = self.settings.system_prompt
            if host_changed:
                self.ollama = OllamaClient(
                    model=self.settings.model,
                    host=self.settings.ollama_host,
                    system_prompt=self.settings.system_prompt,
                )

            setup_logging(debug=self.settings.debug_mode)
            self.logger = get_logger()
            self.logger.info("Pengaturan disimpan (host_changed=%s, theme_changed=%s)", host_changed, theme_changed)

            if theme_changed:
                self.apply_theme()

            self.check_ollama_connection()
            self.toasts.show_toast("Pengaturan disimpan", kind="success")

    def _register_shortcuts(self) -> None:
        self._shortcuts: List[QShortcut] = []

        bindings = [
            ("Ctrl+N", self.handle_new_chat, "Chat baru"),
            ("Ctrl+F", lambda: self.sidebar.search_box.setFocus(), "Cari chat"),
            ("Ctrl+L", lambda: self.chat_widget.input.setFocus(), "Fokus ke kolom pesan"),
            ("Ctrl+R", self.handle_regenerate, "Regenerate response"),
            ("Ctrl+Shift+O", self.chat_widget._pick_files, "Lampirkan file"),
            ("Escape", self.handle_stop_generating, "Stop generating"),
            ("Ctrl+/", self.show_shortcuts_help, "Daftar shortcut"),
            ("F1", self.show_shortcuts_help, "Daftar shortcut"),
        ]

        for key, handler, _label in bindings:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(handler)
            self._shortcuts.append(shortcut)

        self._shortcut_help = bindings

    def show_shortcuts_help(self) -> None:
        lines = [f"{key} — {label}" for key, _handler, label in self._shortcut_help]
        QMessageBox.information(self, "Keyboard shortcuts", "\n".join(lines))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "toasts"):
            self.toasts.sync_geometry()

    def refresh_sidebar(self) -> None:
        conversations = self.chat_manager.get_chat_list()
        self.sidebar.set_conversations(conversations)
        stats_text = format_session_stats(self._session_replies, self._session_tokens)
        self.sidebar.set_session_stats(stats_text or "")

    def start_fresh_chat(self) -> None:
        conversation_id = self.chat_manager.new_chat("New Chat")
        self.refresh_sidebar()
        self.sidebar.select_conversation(conversation_id)
        self.chat_widget.clear_messages()
        self.chat_widget.add_message(
            "Chat baru dibuat. Silakan kirim pesan.",
            role="assistant",
            track=False,
        )

    def load_conversation(self, conversation_id: int) -> None:
        messages = self.chat_manager.load_chat(conversation_id)
        self.chat_widget.clear_messages()

        for msg in messages:
            clean_text, attachments = split_content_and_attachments(msg["content"])
            self.chat_widget.add_message(clean_text, role=msg["role"], attachments=attachments)

        if messages and messages[-1]["role"] == "assistant":
            self.chat_widget.show_regenerate(True)

        conv = self.chat_manager.db.get_conversation(conversation_id)
        if conv is not None:
            self.statusBar().showMessage(f"Conversation: {conv['title']}", 2500)

    def handle_new_chat(self) -> None:
        self.stop_worker_if_running()
        self.start_fresh_chat()

    def handle_conversation_selected(self, conversation_id: int) -> None:
        self.stop_worker_if_running()
        self.sidebar.clear_search()
        self.refresh_sidebar()
        self.sidebar.select_conversation(conversation_id)
        self.load_conversation(conversation_id)

    def handle_rename_requested(self, conversation_id: int, new_title: str) -> None:
        self.chat_manager.rename_chat(conversation_id, new_title)
        self.refresh_sidebar()
        self.sidebar.select_conversation(conversation_id)

    def handle_delete_requested(self, conversation_id: int) -> None:
        self.stop_worker_if_running()
        self.chat_manager.delete_chat(conversation_id)
        self.refresh_sidebar()

        conversations = self.chat_manager.get_chat_list()
        if conversations:
            first_id = int(conversations[0]["id"])
            self.sidebar.select_conversation(first_id)
            self.load_conversation(first_id)
        else:
            self.start_fresh_chat()

    def handle_pin_toggled(self, conversation_id: int) -> None:
        self.chat_manager.toggle_pin(conversation_id)

        query = self.sidebar.search_box.text()
        if query.strip():
            self.handle_search_changed(query)
        else:
            self.refresh_sidebar()

        self.sidebar.select_conversation(conversation_id)

    def handle_search_changed(self, query: str) -> None:
        results = self.chat_manager.search_chats(query)
        self.sidebar.set_conversations(results)

    def handle_user_message(self, text: str, attachments: List[Attachment] | None = None) -> None:
        if self._worker is not None:
            return

        attachments = attachments or []

        skill = self.skills.match(text) if text else None
        if skill is not None:
            self.handle_skill_message(text, skill, attachments)
            return

        display_text = text or "📎"
        stored_content = display_text + encode_marker(attachments)

        conversation_id = self.chat_manager.add_user_message(stored_content)
        self.refresh_sidebar()
        self.sidebar.select_conversation(conversation_id)
        self._start_streaming()

    def handle_skill_message(self, text: str, skill, attachments: List[Attachment] | None = None) -> None:
        # Skill actions are instant (no need to round-trip through the LLM):
        # save the user's message, run the action, and show the result
        # right away as Arcelia's reply.
        attachments = attachments or []
        stored_content = (text or "📎") + encode_marker(attachments)
        self.chat_manager.add_user_message(stored_content)
        success, message = self.skills.run(skill)

        self.chat_manager.add_assistant_message(message)
        self.refresh_sidebar()
        self.chat_widget.add_message(message, role="assistant", track=False)
        self.chat_widget.show_regenerate(False)

        self.toasts.show_toast(message, kind="success" if success else "error")
        if success:
            self.logger.info("Skill '%s' dijalankan", skill.name)
        else:
            self.logger.warning("Skill '%s' gagal: %s", skill.name, message)
            self.statusBar().showMessage(f"Skill '{skill.name}' gagal dijalankan", 3000)

    def handle_stop_generating(self) -> None:
        self.stop_worker_if_running()

    def handle_regenerate(self) -> None:
        if self._worker is not None:
            return

        messages = self.chat_manager.get_current_messages()
        if not messages or messages[-1]["role"] != "assistant":
            return

        self.chat_manager.remove_last_message()
        self.chat_widget.remove_last_assistant_bubble()
        self.refresh_sidebar()
        self._start_streaming()

    def handle_edit_requested(self, text: str, index: int) -> None:
        if self._worker is not None:
            return

        conversation_id = self.chat_manager.get_current_conversation_id()
        if conversation_id is None:
            return

        # Discard the edited prompt and everything that came after it, then
        # reload the (now shorter) conversation and resend the edited text.
        self.chat_manager.truncate_from(index)
        self.load_conversation(conversation_id)
        self.chat_widget.input.setPlainText(text)
        self.chat_widget.input.setFocus()

    def handle_export(self) -> None:
        conversation_id = self.chat_manager.get_current_conversation_id()
        if conversation_id is None:
            self.statusBar().showMessage("Belum ada chat untuk diekspor", 3000)
            return

        conv = self.chat_manager.db.get_conversation(conversation_id)
        messages = self.chat_manager.db.get_messages(conversation_id)
        if conv is None or not messages:
            self.statusBar().showMessage("Belum ada pesan untuk diekspor", 3000)
            return

        safe_name = re.sub(r"[^\w\-. ]", "", conv["title"]).strip() or "chat"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export chat",
            f"{safe_name}.md",
            "Markdown (*.md);;Text (*.txt);;PDF (*.pdf)",
        )
        if not path:
            return

        try:
            export_conversation(path, conv["title"], messages)
            self.statusBar().showMessage(f"Chat diekspor ke {path}", 4000)
            self.toasts.show_toast(f"Chat diekspor ke {path}", kind="success")
            self.logger.info("Chat %s diekspor ke %s", conversation_id, path)
        except Exception as e:
            self.statusBar().showMessage(f"Export gagal: {e}", 4000)
            self.toasts.show_toast(f"Export gagal: {e}", kind="error")
            self.logger.error("Export gagal: %s", e)

    def handle_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import chat",
            "",
            "Text/Markdown (*.md *.txt);;All files (*)",
        )
        if not path:
            return

        try:
            title, messages = import_conversation(path)
        except Exception as e:
            self.statusBar().showMessage(f"Import gagal: {e}", 4000)
            self.logger.error("Import gagal: %s", e)
            return

        if not messages:
            self.statusBar().showMessage("Tidak ada pesan yang bisa diimport", 4000)
            return

        self.stop_worker_if_running()
        conversation_id = self.chat_manager.new_chat(title)
        for msg in messages:
            if msg["role"] == "user":
                self.chat_manager.add_user_message(msg["content"])
            else:
                self.chat_manager.add_assistant_message(msg["content"])

        self.refresh_sidebar()
        self.load_conversation(conversation_id)
        self.statusBar().showMessage(f"Chat diimport: {title}", 4000)
        self.toasts.show_toast(f"Chat diimport: {title}", kind="success")

    def maybe_auto_rename(self) -> None:
        conversation_id = self.chat_manager.get_current_conversation_id()
        if conversation_id is None:
            return

        conv = self.chat_manager.db.get_conversation(conversation_id)
        if conv is None or conv["title"] != "New Chat":
            return

        messages = self.chat_manager.get_current_messages()
        if len(messages) < 2:
            return

        user_text = messages[-2]["content"] if messages[-2]["role"] == "user" else ""
        assistant_text = messages[-1]["content"]

        worker = AutoTitleWorker(self.ollama, conversation_id, user_text, assistant_text)
        worker.title_ready.connect(self.on_auto_title_ready)
        worker.finished.connect(lambda w=worker: self._forget_title_worker(w))
        self._title_workers.append(worker)
        worker.start()

    def _forget_title_worker(self, worker: AutoTitleWorker) -> None:
        if worker in self._title_workers:
            self._title_workers.remove(worker)

    def on_auto_title_ready(self, conversation_id: int, title: str) -> None:
        self.chat_manager.rename_chat(conversation_id, title)
        self.refresh_sidebar()
        if self.chat_manager.get_current_conversation_id() == conversation_id:
            self.sidebar.select_conversation(conversation_id)

    def _start_streaming(self) -> None:
        self.chat_widget.begin_streaming_reply()
        self.chat_widget.set_typing(True)
        self.chat_widget.set_generating(True)
        self.chat_widget.input.setEnabled(False)

        messages = list(self.chat_manager.get_current_messages())
        if messages and messages[-1]["role"] == "user":
            clean_text, attachments = split_content_and_attachments(messages[-1]["content"])
            augmented = clean_text
            for att in attachments:
                if att.kind == "text":
                    file_text = read_text_preview(att.path)
                    augmented += f"\n\n--- lampiran: {att.name} ---\n```\n{file_text}\n```"
                elif att.kind == "image":
                    augmented += (
                        f"\n\n[Catatan sistem: user melampirkan gambar '{att.name}', "
                        "tapi model ini belum bisa melihat/menganalisis gambar.]"
                    )
                else:
                    augmented += f"\n\n[Catatan sistem: user melampirkan file '{att.name}' (tidak bisa dibaca isinya).]"
            messages[-1] = {**messages[-1], "content": augmented}

        self._worker = StreamWorker(self.ollama, messages)
        self._worker.chunk.connect(self.on_stream_chunk)
        self._worker.completed.connect(self.on_stream_completed)
        self._worker.failed.connect(self.on_stream_failed)
        self._worker.finished.connect(self.on_worker_finished)
        self._worker.start()

    def on_stream_chunk(self, token: str) -> None:
        if self.sender() is not self._worker:
            return  # stale signal from a worker we already gave up on (Stop/switch chat)
        self.chat_widget.append_streaming_text(token)

    def on_stream_completed(self, reply: str, was_stopped: bool, stats: dict) -> None:
        if self.sender() is not self._worker:
            return  # stale signal — don't attach this reply to whatever chat is open now
        final_reply = reply.strip()
        if was_stopped:
            final_reply = final_reply or "(dihentikan)"
        else:
            final_reply = final_reply or "..."

        self.chat_manager.add_assistant_message(final_reply)
        self.refresh_sidebar()

        stats_text = format_stats(stats)
        self.chat_widget.finish_streaming_reply(final_reply, stats_text)
        self.chat_widget.show_regenerate(True)
        self.maybe_auto_rename()

        self._session_replies += 1
        if stats.get("eval_count"):
            self._session_tokens += stats["eval_count"]
        self.refresh_sidebar()

        self.logger.debug("Balasan selesai (%s) — %s", "dihentikan" if was_stopped else "normal", stats_text or "no stats")

    def on_stream_failed(self, error_text: str) -> None:
        if self.sender() is not self._worker:
            return  # stale signal from an abandoned worker
        self.logger.error("Stream Ollama gagal: %s", error_text)
        self.chat_widget.discard_streaming_reply()
        self.chat_widget.add_message(
            f"Error saat menghubungi Ollama:\n{error_text}",
            role="assistant",
            track=False,
        )
        self.toasts.show_toast(f"Gagal menghubungi Ollama: {error_text}", kind="error")
        self.check_ollama_connection()

    def on_worker_finished(self) -> None:
        self.chat_widget.set_typing(False)
        self.chat_widget.set_generating(False)
        self.chat_widget.input.setEnabled(True)
        self._worker = None

    def stop_worker_if_running(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.quit()
            self._worker.wait(1000)
        self._worker = None
