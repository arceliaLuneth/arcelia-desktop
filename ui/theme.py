from __future__ import annotations

PALETTES = {
    "dark": {
        "bg": "#0f0f11",
        "sidebar_bg": "#0f0f11",
        "sidebar_border": "#232326",
        "text_primary": "#ececee",
        "text_secondary": "#8e8e93",
        "text_muted": "#6e6e73",
        "text_body": "#e4e4e7",
        "accent": "#4f7cdb",
        "accent_hover": "#5c87e0",
        "danger": "#d1554f",
        "danger_hover": "#dc635d",
        "surface": "#1a1a1d",
        "surface_hover": "#232326",
        "surface_border": "#2a2a2e",
        "list_selected": "#1e1e21",
        "pill_bg": "#1a1a1d",
        "pill_text": "#9db3e8",
        "pill_border": "#2a2a2e",
        "composer_bg": "#1a1a1d",
        "composer_border": "#232326",
        "bubble_assistant_bg": "#18181b",
        "bubble_assistant_border": "#232326",
        "bubble_user_bg": "#2a3a52",
        "bubble_user_border": "#2a3a52",
        "bubble_text_user": "#eef2fa",
        "timestamp": "#6e6e73",
        "action_btn_border": "#2a2a2e",
        "action_btn_text": "#8e8e93",
        "input_text": "#e4e4e7",
    },
    "light": {
        "bg": "#fbfbfa",
        "sidebar_bg": "#fbfbfa",
        "sidebar_border": "#e7e7e4",
        "text_primary": "#1f1f1f",
        "text_secondary": "#6b6b6b",
        "text_muted": "#8a8a8a",
        "text_body": "#2a2a2a",
        "accent": "#3c66c4",
        "accent_hover": "#4a72cc",
        "danger": "#c34840",
        "danger_hover": "#cc554d",
        "surface": "#f1f1ef",
        "surface_hover": "#e9e9e6",
        "surface_border": "#e2e2de",
        "list_selected": "#eeeeeb",
        "pill_bg": "#eef1fa",
        "pill_text": "#3c66c4",
        "pill_border": "#dbe3f5",
        "composer_bg": "#f1f1ef",
        "composer_border": "#e2e2de",
        "bubble_assistant_bg": "#ffffff",
        "bubble_assistant_border": "#e7e7e4",
        "bubble_user_bg": "#e8edf9",
        "bubble_user_border": "#e8edf9",
        "bubble_text_user": "#1f2d4d",
        "timestamp": "#9a9a9a",
        "action_btn_border": "#e2e2de",
        "action_btn_text": "#6b6b6b",
        "input_text": "#2a2a2a",
    },
}


def build_stylesheet(theme: str = "dark") -> str:
    p = PALETTES.get(theme, PALETTES["dark"])
    return f"""
        QMainWindow {{ background: {p['bg']}; }}
        QWidget#CentralWidget {{ background: {p['bg']}; }}

        QFrame#Sidebar {{
            background: {p['sidebar_bg']};
            border-right: 1px solid {p['sidebar_border']};
        }}

        QWidget#CharacterPanel {{
            background: {p['sidebar_bg']};
            border-left: 1px solid {p['sidebar_border']};
        }}

        QLabel#CharacterOverlay {{
            background: {p['sidebar_bg']};
            color: {p['text_muted']};
            font-size: 13px;
            padding: 24px;
        }}
        QLabel#CharacterOverlay[error="true"] {{
            color: {p['danger']};
        }}

        QLabel#SidebarTitle {{ color: {p['text_primary']}; font-size: 18px; font-weight: 700; padding: 0 4px 4px 4px; }}

        QPushButton#PrimaryButton {{
            background: {p['surface']}; color: {p['text_primary']}; border: 1px solid {p['surface_border']};
            border-radius: 10px; padding: 10px 12px; font-weight: 600; text-align: left;
        }}
        QPushButton#PrimaryButton:hover {{ background: {p['surface_hover']}; }}

        QPushButton#SecondaryButton {{
            background: transparent; color: {p['text_body']};
            border: 1px solid {p['surface_border']}; border-radius: 10px;
            padding: 9px 12px; font-weight: 500;
        }}
        QPushButton#SecondaryButton:hover {{ background: {p['surface_hover']}; }}

        QToolButton#MoreButton {{
            background: transparent; color: {p['text_secondary']};
            border: none; border-radius: 8px;
            padding: 8px 10px; font-weight: 500; text-align: left;
        }}
        QToolButton#MoreButton:hover {{ background: {p['surface']}; color: {p['text_primary']}; }}
        QToolButton#MoreButton::menu-indicator {{ image: none; }}

        QListWidget#HistoryList {{
            background: transparent; border: none; outline: none;
            color: {p['text_secondary']}; padding: 4px 0;
        }}
        QListWidget#HistoryList::item {{
            background: transparent; border-radius: 8px;
            padding: 8px 10px; margin-bottom: 2px;
        }}
        QListWidget#HistoryList::item:hover {{ background: {p['surface']}; }}
        QListWidget#HistoryList::item:selected {{ background: {p['list_selected']}; color: {p['text_primary']}; }}

        QFrame#ChatPanel {{ background: {p['bg']}; }}
        QLabel#ChatHeaderTitle {{ color: {p['text_secondary']}; font-size: 13px; font-weight: 600; }}
        QLabel#ChatHeaderSubtitle {{ color: {p['text_muted']}; font-size: 11px; }}

        QComboBox#ModelSelector {{
            background: transparent; color: {p['text_secondary']};
            border: none; border-radius: 8px;
            padding: 5px 8px; font-size: 12px;
        }}
        QComboBox#ModelSelector:hover {{ background: {p['surface']}; color: {p['text_primary']}; }}

        QFrame#Composer {{
            background: {p['composer_bg']}; border: 1px solid {p['composer_border']};
            border-radius: 16px;
        }}
        QTextEdit#PromptInput {{
            background: transparent; border: none; color: {p['input_text']};
            font-size: 14px; padding: 8px; selection-background-color: {p['accent']};
        }}
        QTextEdit#PromptInput:focus {{ outline: none; }}

        QPushButton#SendButton {{
            background: {p['accent']}; color: white; border: none;
            border-radius: 12px; padding: 11px 18px; font-weight: 600;
        }}
        QPushButton#SendButton:hover {{ background: {p['accent_hover']}; }}
        QPushButton#SendButton:disabled {{ background: {p['surface']}; color: {p['text_muted']}; }}

        QPushButton#StopButton {{
            background: {p['danger']}; color: white; border: none;
            border-radius: 12px; padding: 11px 18px; font-weight: 600;
        }}
        QPushButton#StopButton:hover {{ background: {p['danger_hover']}; }}

        QPushButton#GhostButton {{
            background: transparent; color: {p['text_secondary']};
            border: 1px solid {p['surface_border']}; border-radius: 12px;
            padding: 11px 14px; font-weight: 500;
        }}
        QPushButton#GhostButton:hover {{ background: {p['surface']}; color: {p['text_primary']}; }}
        QPushButton#GhostButton:checked {{
            background: {p['accent']}; border: 1px solid {p['accent']}; color: white;
        }}

        QScrollArea#MessagesScroll {{ background: transparent; border: none; }}
        QWidget#MessagesScrollOuter {{ background: transparent; }}
        QWidget#MessagesContainer {{ background: transparent; }}

        QWidget#PlainAssistant {{
            background: transparent;
            border: none;
        }}
        QFrame#TypingBubble {{
            background: {p['bubble_assistant_bg']};
            border: 1px solid {p['bubble_assistant_border']};
            border-radius: 16px;
        }}
        QLabel#TypingBubbleText {{ color: {p['text_secondary']}; font-size: 14px; }}
        QFrame#BubbleUser {{
            background: {p['bubble_user_bg']};
            border: none;
            border-radius: 16px;
        }}

        QTextBrowser#PlainTextAssistant {{
            background: transparent; border: none; color: {p['text_body']}; font-size: 14px;
        }}
        QLabel#BubbleTextUser {{ color: {p['bubble_text_user']}; font-size: 14px; }}

        QPushButton#BubbleIconButton {{
            background: transparent; border: none;
            border-radius: 6px; color: {p['action_btn_text']};
            font-size: 13px; padding: 0;
        }}
        QPushButton#BubbleIconButton:hover {{
            background: {p['surface']}; color: {p['text_body']};
        }}

        QLabel#Timestamp {{ color: {p['timestamp']}; font-size: 11px; }}
        QLabel#MessageRole {{ color: {p['text_muted']}; font-size: 11px; font-weight: 600; letter-spacing: 0.3px; }}

        QFrame#AttachmentChip {{
            background: {p['surface']}; border: 1px solid {p['surface_border']}; border-radius: 10px;
        }}
        QLabel#AttachmentChipLabel {{ color: {p['text_body']}; font-size: 12px; }}
        QPushButton#AttachmentChipRemove {{
            background: transparent; color: {p['text_muted']}; border: none; font-weight: 700;
        }}
        QPushButton#AttachmentChipRemove:hover {{ color: {p['text_body']}; }}
        QLabel#AttachmentThumb {{ border-radius: 8px; border: 1px solid {p['surface_border']}; }}

        QLabel#ToastInfo, QLabel#ToastSuccess, QLabel#ToastError {{
            color: white; font-size: 13px; padding: 10px 14px; border-radius: 10px;
        }}
        QLabel#ToastInfo {{ background: rgba(26, 26, 29, 235); border: 1px solid {p['accent']}; }}
        QLabel#ToastSuccess {{ background: rgba(20, 40, 30, 235); border: 1px solid #3d8a5f; }}
        QLabel#ToastError {{ background: rgba(42, 22, 20, 235); border: 1px solid {p['danger']}; }}

        QDialog#SettingsDialog {{ background: {p['bg']}; }}
        QLabel#SettingsLabel {{ color: {p['text_secondary']}; font-size: 12px; font-weight: 600; }}
        QLineEdit#SettingsField, QTextEdit#SettingsField, QComboBox#SettingsField {{
            background: {p['surface']}; color: {p['text_body']};
            border: 1px solid {p['surface_border']}; border-radius: 10px; padding: 8px;
        }}
        QCheckBox#SettingsCheckbox {{ color: {p['text_body']}; }}

        QFrame#ConnectionBanner {{
            background: rgba(209, 85, 79, 30); border: 1px solid {p['danger']};
            border-radius: 10px;
        }}
        QLabel#ConnectionBannerText {{ color: {p['text_body']}; font-size: 12px; }}
    """
