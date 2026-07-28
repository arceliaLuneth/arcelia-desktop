from __future__ import annotations

from typing import List, Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from utils.settings import AppSettings


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, available_models: Optional[List[str]] = None, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SettingsDialog")
        self.setWindowTitle("Settings — Arcelia")
        self.setMinimumWidth(440)

        self._result_settings: Optional[AppSettings] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        layout.addWidget(self._field_label("Ollama host"))
        self.host_input = QLineEdit(settings.ollama_host)
        self.host_input.setObjectName("SettingsField")
        layout.addWidget(self.host_input)

        layout.addWidget(self._field_label("Model default"))
        self.model_combo = QComboBox()
        self.model_combo.setObjectName("SettingsField")
        self.model_combo.setEditable(True)
        models = available_models or []
        if settings.model not in models:
            models = [settings.model] + models
        self.model_combo.addItems(models)
        self.model_combo.setCurrentText(settings.model)
        layout.addWidget(self.model_combo)

        layout.addWidget(self._field_label("System prompt"))
        self.system_prompt_input = QTextEdit(settings.system_prompt)
        self.system_prompt_input.setObjectName("SettingsField")
        self.system_prompt_input.setFixedHeight(90)
        layout.addWidget(self.system_prompt_input)

        layout.addWidget(self._field_label("Tema"))
        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("SettingsField")
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(settings.theme)
        layout.addWidget(self.theme_combo)

        self.debug_checkbox = QCheckBox("Debug mode (logging lebih detail)")
        self.debug_checkbox.setObjectName("SettingsCheckbox")
        self.debug_checkbox.setChecked(settings.debug_mode)
        layout.addWidget(self.debug_checkbox)

        layout.addWidget(self._field_label("Suara (Text-to-Speech)"))

        self.voice_checkbox = QCheckBox("Aktifkan suara — Arcelia membacakan balasannya")
        self.voice_checkbox.setObjectName("SettingsCheckbox")
        self.voice_checkbox.setChecked(settings.voice_enabled)
        layout.addWidget(self.voice_checkbox)

        model_row = QHBoxLayout()
        self.piper_model_input = QLineEdit(settings.piper_model_path)
        self.piper_model_input.setObjectName("SettingsField")
        self.piper_model_input.setPlaceholderText("Path ke model Piper (.onnx) — kosongkan untuk pakai fallback TTS bawaan sistem")
        browse_btn = QPushButton("Pilih...")
        browse_btn.setObjectName("SecondaryButton")
        browse_btn.clicked.connect(self._browse_piper_model)
        model_row.addWidget(self.piper_model_input, 1)
        model_row.addWidget(browse_btn)
        layout.addLayout(model_row)

        self.piper_config_input = QLineEdit(settings.piper_config_path)
        self.piper_config_input.setObjectName("SettingsField")
        self.piper_config_input.setPlaceholderText("Path ke config Piper (.onnx.json) — opsional, biasanya satu folder dengan model")
        layout.addWidget(self.piper_config_input)

        layout.addWidget(self._field_label("Voice input (Speech-to-Text)"))
        vosk_row = QHBoxLayout()
        self.vosk_model_input = QLineEdit(settings.vosk_model_path)
        self.vosk_model_input.setObjectName("SettingsField")
        self.vosk_model_input.setPlaceholderText("Folder model Vosk — kosongkan untuk nonaktifkan mikrofon")
        vosk_browse_btn = QPushButton("Pilih...")
        vosk_browse_btn.setObjectName("SecondaryButton")
        vosk_browse_btn.clicked.connect(self._browse_vosk_model)
        vosk_row.addWidget(self.vosk_model_input, 1)
        vosk_row.addWidget(vosk_browse_btn)
        layout.addLayout(vosk_row)

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        cancel_btn = QPushButton("Batal")
        cancel_btn.setObjectName("SecondaryButton")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Simpan")
        save_btn.setObjectName("PrimaryButton")
        save_btn.clicked.connect(self._save_and_close)

        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("SettingsLabel")
        return label

    def _browse_piper_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Pilih model Piper", "", "Piper model (*.onnx)")
        if path:
            self.piper_model_input.setText(path)
            # Piper models are almost always shipped with a sibling
            # <model>.onnx.json config file — auto-fill if it exists and
            # the user hasn't already set one.
            guess_config = path + ".json"
            if not self.piper_config_input.text().strip():
                self.piper_config_input.setText(guess_config)

    def _browse_vosk_model(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Pilih folder model Vosk")
        if path:
            self.vosk_model_input.setText(path)

    def _save_and_close(self) -> None:
        self._result_settings = AppSettings(
            ollama_host=self.host_input.text().strip() or "http://localhost:11434",
            model=self.model_combo.currentText().strip() or "qwen2.5:3b",
            system_prompt=self.system_prompt_input.toPlainText().strip(),
            theme=self.theme_combo.currentText(),
            debug_mode=self.debug_checkbox.isChecked(),
            voice_enabled=self.voice_checkbox.isChecked(),
            piper_model_path=self.piper_model_input.text().strip(),
            piper_config_path=self.piper_config_input.text().strip(),
            vosk_model_path=self.vosk_model_input.text().strip(),
        )
        self.accept()

    def result_settings(self) -> Optional[AppSettings]:
        return self._result_settings
