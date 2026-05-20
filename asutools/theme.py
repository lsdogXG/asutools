"""iTerm-style minimal black/white themes.

One strong accent color, 4-step gray scale, 1px hairline dividers, 6px radius.
"""

DARK = {
    "bg":         "#0B0B0C",
    "bg_alt":     "#121214",
    "bg_hover":   "#1A1A1D",
    "bg_active":  "#26262A",
    "border":     "#1F1F22",
    "text":       "#F5F5F7",
    "text_dim":   "#9A9AA0",
    "text_mute":  "#5C5C62",
    "accent":     "#E5E5E7",
    "accent_dim": "#3A3A3F",
    "danger":     "#E5484D",
}

LIGHT = {
    "bg":         "#FCFCFD",
    "bg_alt":     "#F4F4F6",
    "bg_hover":   "#EDEDEF",
    "bg_active":  "#E2E2E5",
    "border":     "#E4E4E7",
    "text":       "#0B0B0C",
    "text_dim":   "#5C5C62",
    "text_mute":  "#9A9AA0",
    "accent":     "#0B0B0C",
    "accent_dim": "#D4D4D7",
    "danger":     "#C4302B",
}


_CACHE: dict[int, str] = {}


def qss(t: dict) -> str:
    """Return QSS string for a theme dict; cached by identity to avoid rebuilds."""
    key = id(t)
    if key in _CACHE:
        return _CACHE[key]
    _CACHE[key] = _qss_build(t)
    return _CACHE[key]


def _qss_build(t: dict) -> str:
    return f"""
* {{
    font-family: ".AppleSystemUIFont", "Helvetica Neue", "PingFang SC", sans-serif;
    font-size: 13px;
    color: {t['text']};
    outline: none;
}}

QMainWindow, QWidget#root {{
    background: {t['bg']};
}}

/* Sidebar */
QFrame#sidebar {{
    background: {t['bg_alt']};
    border: none;
    border-right: 1px solid {t['border']};
}}
QListWidget#categoryList {{
    background: transparent;
    border: none;
    padding: 8px 6px;
}}
QListWidget#categoryList::item {{
    padding: 7px 12px;
    margin: 1px 2px;
    border-radius: 6px;
    color: {t['text_dim']};
}}
QListWidget#categoryList::item:hover {{
    background: {t['bg_hover']};
    color: {t['text']};
}}
QListWidget#categoryList::item:selected {{
    background: {t['bg_active']};
    color: {t['text']};
}}

/* Top bar */
QFrame#topbar {{
    background: {t['bg']};
    border: none;
    border-bottom: 1px solid {t['border']};
}}

/* Category tabs row */
QFrame#tabsWrap {{
    background: {t['bg_alt']};
    border-bottom: 1px solid {t['border']};
}}
QTabBar#categoryTabs {{
    background: transparent;
    border: none;
    qproperty-drawBase: 0;
}}
QTabBar#categoryTabs::tab {{
    background: transparent;
    color: {t['text_dim']};
    padding: 7px 14px;
    margin: 4px 2px;
    border: 1px solid transparent;
    border-radius: 6px;
    min-width: 40px;
}}
QTabBar#categoryTabs::tab:hover {{
    background: {t['bg_hover']};
    color: {t['text']};
}}
QTabBar#categoryTabs::tab:selected {{
    background: {t['bg_active']};
    color: {t['text']};
    border-color: {t['border']};
}}
QTabBar QToolButton {{
    background: {t['bg_alt']};
    border: none;
    color: {t['text_dim']};
}}
QTabBar QToolButton:hover {{
    color: {t['text']};
}}
QLineEdit#searchInput {{
    background: {t['bg_alt']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 6px 10px;
    color: {t['text']};
    selection-background-color: {t['accent_dim']};
}}
QLineEdit#searchInput:focus {{
    border: 1px solid {t['accent']};
}}

/* Tool list */
QListView#toolList {{
    background: {t['bg']};
    border: none;
    padding: 8px;
}}

/* Status bar */
QFrame#statusbar {{
    background: {t['bg_alt']};
    border: none;
    border-top: 1px solid {t['border']};
}}
QLabel#statusLabel {{
    color: {t['text_mute']};
    padding: 4px 12px;
    font-size: 12px;
}}

/* Scrollbar */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {t['border']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {t['text_mute']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* Generic buttons */
QPushButton {{
    background: {t['bg_alt']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 6px 14px;
    color: {t['text']};
}}
QPushButton:hover {{
    background: {t['bg_hover']};
    border-color: {t['text_mute']};
}}
QPushButton:pressed {{
    background: {t['bg_active']};
}}
QPushButton#primary {{
    background: {t['accent']};
    border-color: {t['accent']};
    color: {t['bg']};
}}
QPushButton#primary:hover {{
    background: {t['accent_dim']};
}}

/* Dialogs */
QDialog {{
    background: {t['bg']};
}}
QDialog QLabel {{
    color: {t['text']};
}}
QDialog QLineEdit, QDialog QComboBox {{
    background: {t['bg_alt']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 6px 10px 6px 12px;
    color: {t['text']};
    selection-background-color: {t['accent_dim']};
    min-height: 22px;
    min-width: 200px;
}}
QDialog QLineEdit:focus, QDialog QComboBox:focus {{
    border: 1px solid {t['accent']};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
    subcontrol-origin: padding;
    subcontrol-position: center right;
}}
QComboBox::down-arrow {{
    image: none;
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {t['text_dim']};
    margin-right: 10px;
}}
QComboBox:hover::down-arrow {{
    border-top-color: {t['text']};
}}
QComboBox QAbstractItemView {{
    background: {t['bg_alt']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    selection-background-color: {t['bg_active']};
    color: {t['text']};
    padding: 4px;
    outline: none;
}}
QComboBox QAbstractItemView::item {{
    padding: 6px 12px;
    border-radius: 4px;
    min-height: 24px;
}}

/* Tabs */
QTabWidget::pane {{
    border: 1px solid {t['border']};
    border-radius: 8px;
    background: {t['bg_alt']};
    top: -1px;
}}
QTabBar {{
    qproperty-drawBase: 0;
}}
QTabBar::tab {{
    background: transparent;
    color: {t['text_dim']};
    padding: 8px 18px;
    border: none;
    margin-right: 2px;
}}
QTabBar::tab:hover {{
    color: {t['text']};
}}
QTabBar::tab:selected {{
    color: {t['text']};
    border-bottom: 2px solid {t['accent']};
}}

/* Env list (in Settings) */
QListWidget#envList {{
    background: {t['bg']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 4px;
}}
QListWidget#envList::item {{
    padding: 0;
    margin: 1px 0;
    border-radius: 6px;
}}

/* Form labels */
QLabel#formLabel {{
    color: {t['text_dim']};
    padding: 6px 0;
    font-size: 12px;
}}
QLabel#hintLabel {{
    color: {t['text_mute']};
    font-size: 12px;
    padding: 4px 2px;
}}

/* Message box */
QMessageBox {{
    background: {t['bg']};
}}
QMessageBox QLabel {{
    color: {t['text']};
}}
"""
