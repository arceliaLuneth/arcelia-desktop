from __future__ import annotations

from typing import List, Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
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

    def _save_and_close(self) -> None:
        self._result_settings = AppSettings(
            ollama_host=self.host_input.text().strip() or "http://localhost:11434",
            model=self.model_combo.currentText().strip() or "qwen2.5:3b",
            system_prompt=self.system_prompt_input.toPlainText().strip(),
            theme=self.theme_combo.currentText(),
            debug_mode=self.debug_checkbox.isChecked(),
        )
        self.accept()

    def result_settings(self) -> Optional[AppSettings]:
        return self._result_settings
