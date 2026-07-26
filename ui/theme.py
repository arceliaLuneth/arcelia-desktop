from __future__ import annotations

PALETTES = {
    "dark": {
        "bg": "#0b0f14",
        "sidebar_bg": "#101722",
        "sidebar_border": "#1d2a3a",
        "text_primary": "#f5f8fc",
        "text_secondary": "#92a1b7",
        "text_muted": "#7f91ab",
        "text_body": "#eef4fb",
        "accent": "#2d6cdf",
        "accent_hover": "#3a78ea",
        "danger": "#dc4d4d",
        "danger_hover": "#e35d5d",
        "surface": "#182232",
        "surface_hover": "#202c3f",
        "surface_border": "#263446",
        "list_selected": "#1a2433",
        "pill_bg": "#122031",
        "pill_text": "#86a6ff",
        "pill_border": "#20324a",
        "composer_bg": "#101722",
        "composer_border": "#223044",
        "bubble_assistant_bg": "#141c29",
        "bubble_assistant_border": "#223044",
        "bubble_user_bg": "#2d6cdf",
        "bubble_user_border": "#2d6cdf",
        "bubble_text_user": "white",
        "timestamp": "#8e9bb0",
        "action_btn_border": "#2a3a52",
        "action_btn_text": "#9db3d1",
        "input_text": "#eef4fb",
    },
    "light": {
        "bg": "#f4f6fa",
        "sidebar_bg": "#ffffff",
        "sidebar_border": "#e2e6ee",
        "text_primary": "#141a24",
        "text_secondary": "#5b6472",
        "text_muted": "#6b7688",
        "text_body": "#1c2430",
        "accent": "#2d6cdf",
        "accent_hover": "#3a78ea",
        "danger": "#d84343",
        "danger_hover": "#e35d5d",
        "surface": "#eef1f6",
        "surface_hover": "#e2e7ef",
        "surface_border": "#d7dce6",
        "list_selected": "#e4ebfb",
        "pill_bg": "#e7edfb",
        "pill_text": "#2d6cdf",
        "pill_border": "#c9d7f7",
        "composer_bg": "#ffffff",
        "composer_border": "#d7dce6",
        "bubble_assistant_bg": "#ffffff",
        "bubble_assistant_border": "#e2e6ee",
        "bubble_user_bg": "#2d6cdf",
        "bubble_user_border": "#2d6cdf",
        "bubble_text_user": "white",
        "timestamp": "#8b93a3",
        "action_btn_border": "#d7dce6",
        "action_btn_text": "#5b6472",
        "input_text": "#1c2430",
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

        QLabel#SidebarTitle {{ color: {p['text_primary']}; font-size: 26px; font-weight: 800; }}
        QLabel#SidebarSubtitle {{ color: {p['text_secondary']}; font-size: 12px; }}

        QPushButton#PrimaryButton {{
            background: {p['accent']}; color: white; border: none;
            border-radius: 14px; padding: 12px 14px; font-weight: 700;
        }}
        QPushButton#PrimaryButton:hover {{ background: {p['accent_hover']}; }}

        QPushButton#SecondaryButton {{
            background: {p['surface']}; color: {p['text_body']};
            border: 1px solid {p['surface_border']}; border-radius: 14px;
            padding: 10px 14px; font-weight: 600;
        }}
        QPushButton#SecondaryButton:hover {{ background: {p['surface_hover']}; }}

        QListWidget#HistoryList {{
            background: transparent; border: none; outline: none;
            color: {p['text_body']}; padding: 4px;
        }}
        QListWidget#HistoryList::item {{
            background: transparent; border-radius: 10px;
            padding: 10px 12px; margin-bottom: 6px;
        }}
        QListWidget#HistoryList::item:selected {{ background: {p['list_selected']}; }}

        QLineEdit#SearchBox {{
            background: {p['surface']}; color: {p['text_body']};
            border: 1px solid {p['surface_border']}; border-radius: 12px;
            padding: 9px 12px; font-size: 13px;
        }}
        QLineEdit#SearchBox:focus {{ border: 1px solid {p['accent']}; }}

        QLabel#SectionLabel {{
            color: {p['text_muted']}; font-size: 11px;
            letter-spacing: 1px; font-weight: 700;
        }}

        QLabel#SessionStats {{ color: {p['text_muted']}; font-size: 11px; }}

        QFrame#ChatPanel {{ background: {p['bg']}; }}
        QLabel#ChatHeaderTitle {{ color: {p['text_primary']}; font-size: 22px; font-weight: 800; }}
        QLabel#ChatHeaderSubtitle {{ color: {p['text_secondary']}; font-size: 12px; }}

        QLabel#StatusPill {{
            background: {p['pill_bg']}; color: {p['pill_text']};
            border: 1px solid {p['pill_border']}; border-radius: 10px;
            padding: 4px 10px; font-size: 11px; font-weight: 700;
        }}

        QComboBox#ModelSelector {{
            background: {p['surface']}; color: {p['text_body']};
            border: 1px solid {p['surface_border']}; border-radius: 10px;
            padding: 5px 10px; font-size: 12px;
        }}
        QComboBox#ModelSelector:hover {{ background: {p['surface_hover']}; }}

        QFrame#Composer {{
            background: {p['composer_bg']}; border: 1px solid {p['composer_border']};
            border-radius: 18px;
        }}
        QTextEdit#PromptInput {{
            background: transparent; border: none; color: {p['input_text']};
            font-size: 14px; padding: 8px; selection-background-color: {p['accent']};
        }}
        QTextEdit#PromptInput:focus {{ outline: none; }}

        QPushButton#SendButton {{
            background: {p['accent']}; color: white; border: none;
            border-radius: 14px; padding: 12px 18px; font-weight: 800;
        }}
        QPushButton#SendButton:hover {{ background: {p['accent_hover']}; }}

        QPushButton#StopButton {{
            background: {p['danger']}; color: white; border: none;
            border-radius: 14px; padding: 12px 18px; font-weight: 800;
        }}
        QPushButton#StopButton:hover {{ background: {p['danger_hover']}; }}

        QPushButton#GhostButton {{
            background: {p['surface']}; color: {p['text_body']};
            border: 1px solid {p['surface_border']}; border-radius: 14px;
            padding: 12px 14px; font-weight: 700;
        }}
        QPushButton#GhostButton:hover {{ background: {p['surface_hover']}; }}

        QScrollArea#MessagesScroll {{ background: transparent; border: none; }}
        QWidget#MessagesContainer {{ background: transparent; }}

        QFrame#BubbleAssistant {{
            background: {p['bubble_assistant_bg']};
            border: 1px solid {p['bubble_assistant_border']};
            border-radius: 18px;
        }}
        QFrame#BubbleUser {{
            background: {p['bubble_user_bg']};
            border: 1px solid {p['bubble_user_border']};
            border-radius: 18px;
        }}

        QTextBrowser#BubbleTextAssistant {{
            background: transparent; border: none; color: {p['text_body']}; font-size: 14px;
        }}
        QLabel#BubbleTextUser {{ color: {p['bubble_text_user']}; font-size: 14px; }}

        QPushButton#BubbleActionButton {{
            background: transparent; border: 1px solid {p['action_btn_border']};
            border-radius: 8px; color: {p['action_btn_text']};
            font-size: 11px; padding: 3px 10px;
        }}
        QPushButton#BubbleActionButton:hover {{
            background: {p['surface_hover']}; color: {p['text_body']};
        }}

        QLabel#Timestamp {{ color: {p['timestamp']}; font-size: 11px; }}
        QLabel#BubbleStats {{ color: {p['text_muted']}; font-size: 10px; }}
        QLabel#MessageRole {{ color: {p['text_muted']}; font-size: 11px; font-weight: 700; letter-spacing: 0.4px; }}

        QFrame#AttachmentChip {{
            background: {p['surface']}; border: 1px solid {p['surface_border']}; border-radius: 10px;
        }}
        QLabel#AttachmentChipLabel {{ color: {p['text_body']}; font-size: 12px; }}
        QPushButton#AttachmentChipRemove {{
            background: transparent; color: {p['text_muted']}; border: none; font-weight: 800;
        }}
        QPushButton#AttachmentChipRemove:hover {{ color: {p['text_body']}; }}
        QLabel#AttachmentThumb {{ border-radius: 8px; border: 1px solid {p['surface_border']}; }}

        QLabel#ToastInfo, QLabel#ToastSuccess, QLabel#ToastError {{
            color: white; font-size: 13px; padding: 10px 14px; border-radius: 12px;
        }}
        QLabel#ToastInfo {{ background: rgba(24, 34, 50, 235); border: 1px solid {p['accent']}; }}
        QLabel#ToastSuccess {{ background: rgba(20, 45, 34, 235); border: 1px solid #2e9e5b; }}
        QLabel#ToastError {{ background: rgba(48, 22, 22, 235); border: 1px solid {p['danger']}; }}

        QDialog#SettingsDialog {{ background: {p['bg']}; }}
        QLabel#SettingsLabel {{ color: {p['text_secondary']}; font-size: 12px; font-weight: 700; }}
        QLineEdit#SettingsField, QTextEdit#SettingsField, QComboBox#SettingsField {{
            background: {p['surface']}; color: {p['text_body']};
            border: 1px solid {p['surface_border']}; border-radius: 10px; padding: 8px;
        }}
        QCheckBox#SettingsCheckbox {{ color: {p['text_body']}; }}

        QFrame#ConnectionBanner {{
            background: rgba(220, 77, 77, 40); border: 1px solid {p['danger']};
            border-radius: 12px;
        }}
        QLabel#ConnectionBannerText {{ color: {p['text_body']}; font-size: 12px; }}
    """
