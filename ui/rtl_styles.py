"""
RTL (Right-to-Left) Styles for Onix
Provides comprehensive RTL support for Persian, Arabic, Hebrew, and Urdu
"""



def get_rtl_stylesheet() -> str:
    """Get comprehensive RTL stylesheet."""
    return """
/* === RTL Base Styles === */
[dir="rtl"] * {
    text-align: right;
    direction: rtl;
}

/* === RTL Layout Containers === */
[dir="rtl"] QHBoxLayout {
    direction: rtl;
}

[dir="rtl"] QVBoxLayout {
    direction: rtl;
}

[dir="rtl"] QGridLayout {
    direction: rtl;
}

/* === RTL Text Elements === */
[dir="rtl"] QLabel {
    text-align: right;
    padding-right: 8px;
    padding-left: 0px;
    min-width: 80px;
}

[dir="rtl"] QLineEdit {
    text-align: right;
    padding-right: 12px;
    padding-left: 8px;
    min-width: 120px;
}

[dir="rtl"] QTextEdit {
    text-align: right;
    padding-right: 12px;
    padding-left: 8px;
    min-width: 200px;
}

[dir="rtl"] QPlainTextEdit {
    text-align: right;
    padding-right: 12px;
    padding-left: 8px;
    min-width: 200px;
}

/* === RTL Input Controls === */
[dir="rtl"] QComboBox {
    text-align: right;
    padding-right: 12px;
    padding-left: 8px;
    min-width: 120px;
}

[dir="rtl"] QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: left top;
    left: 0px;
    right: auto;
    width: 20px;
    border-left: 1px solid #d1d5db;
    border-right: none;
}

[dir="rtl"] QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #6b7280;
    border-bottom: none;
    margin-right: 6px;
    margin-left: 0px;
}

[dir="rtl"] QSpinBox {
    text-align: right;
    padding-right: 12px;
    padding-left: 8px;
    min-width: 80px;
}

[dir="rtl"] QDoubleSpinBox {
    text-align: right;
    padding-right: 12px;
    padding-left: 8px;
    min-width: 80px;
}

[dir="rtl"] QSlider {
    direction: rtl;
}

[dir="rtl"] QProgressBar {
    text-align: right;
    min-width: 100px;
    min-height: 20px;
}

/* === RTL Buttons === */
[dir="rtl"] QPushButton {
    text-align: right;
    padding-right: 16px;
    padding-left: 8px;
    min-width: 80px;
}

[dir="rtl"] QToolButton {
    text-align: right;
    padding-right: 8px;
    padding-left: 4px;
}

/* === RTL Lists and Tables === */
[dir="rtl"] QListWidget {
    text-align: right;
    min-width: 200px;
}

[dir="rtl"] QListWidget::item {
    text-align: right;
    padding-right: 12px;
    padding-left: 8px;
}

[dir="rtl"] QTableWidget {
    text-align: right;
}

[dir="rtl"] QTableWidget::item {
    text-align: right;
    padding-right: 12px;
    padding-left: 8px;
}

[dir="rtl"] QTreeWidget {
    text-align: right;
}

[dir="rtl"] QTreeWidget::item {
    text-align: right;
    padding-right: 12px;
    padding-left: 8px;
}

/* === RTL Headers === */
[dir="rtl"] QHeaderView::section {
    text-align: right;
    min-width: 100px;
    min-height: 32px;
    padding-right: 16px;
    padding-left: 8px;
}

/* === RTL Groups and Frames === */
[dir="rtl"] QGroupBox {
    text-align: right;
    min-width: 200px;
    padding-right: 16px;
    padding-left: 8px;
}

[dir="rtl"] QGroupBox::title {
    right: 16px;
    left: auto;
    padding-right: 8px;
    padding-left: 0px;
}

[dir="rtl"] QFrame {
    text-align: right;
}

/* === RTL Menus === */
[dir="rtl"] QMenu {
    text-align: right;
    min-width: 120px;
    padding-right: 8px;
    padding-left: 0px;
}

[dir="rtl"] QMenu::item {
    text-align: right;
    padding-right: 16px;
    padding-left: 8px;
}

[dir="rtl"] QMenuBar {
    text-align: right;
}

[dir="rtl"] QMenuBar::item {
    text-align: right;
    padding-right: 16px;
    padding-left: 8px;
}

/* === RTL Checkboxes and Radio Buttons === */
[dir="rtl"] QCheckBox {
    text-align: right;
    min-width: 120px;
    min-height: 24px;
    padding-right: 8px;
    padding-left: 0px;
}

[dir="rtl"] QCheckBox::indicator {
    margin-right: 8px;
    margin-left: 0px;
}

[dir="rtl"] QRadioButton {
    text-align: right;
    min-width: 120px;
    min-height: 24px;
    padding-right: 8px;
    padding-left: 0px;
}

[dir="rtl"] QRadioButton::indicator {
    margin-right: 8px;
    margin-left: 0px;
}

/* === RTL Scrollbars === */
[dir="rtl"] QScrollBar:vertical {
    right: 0px;
    left: auto;
    width: 12px;
}

[dir="rtl"] QScrollBar:horizontal {
    bottom: 0px;
    top: auto;
    height: 12px;
}

[dir="rtl"] QScrollBar::add-line:vertical {
    right: 0px;
    left: auto;
}

[dir="rtl"] QScrollBar::sub-line:vertical {
    right: 0px;
    left: auto;
}

[dir="rtl"] QScrollBar::add-line:horizontal {
    bottom: 0px;
    top: auto;
}

[dir="rtl"] QScrollBar::sub-line:horizontal {
    bottom: 0px;
    top: auto;
}

/* === RTL Tabs === */
[dir="rtl"] QTabWidget {
    text-align: right;
}

[dir="rtl"] QTabWidget::tab-bar {
    text-align: right;
}

[dir="rtl"] QTabBar {
    text-align: right;
}

[dir="rtl"] QTabBar::tab {
    text-align: right;
    padding-right: 16px;
    padding-left: 8px;
}

/* === RTL Splitters === */
[dir="rtl"] QSplitter {
    direction: rtl;
}

[dir="rtl"] QSplitterHandle {
    direction: rtl;
}

/* === RTL Tooltips === */
[dir="rtl"] QToolTip {
    text-align: right;
    direction: rtl;
}

/* === RTL Status Bar === */
[dir="rtl"] QStatusBar {
    text-align: right;
}

[dir="rtl"] QStatusBar::item {
    text-align: right;
    padding-right: 8px;
    padding-left: 4px;
}

/* === RTL Dock Widgets === */
[dir="rtl"] QDockWidget {
    text-align: right;
}

[dir="rtl"] QDockWidget::title {
    text-align: right;
    padding-right: 8px;
    padding-left: 4px;
}

/* === RTL Custom Widgets === */
[dir="rtl"] #NavRail {
    border-right: 1px solid #dee2e6;
    border-left: none;
    width: 200px;
    padding: 16px 0;
}

[dir="rtl"] #NavRail::item {
    text-align: right;
    padding: 12px 30px 12px 16px;
    margin: 4px 15px 4px 8px;
    min-height: 40px;
    direction: rtl;
}

[dir="rtl"] #ServerDetailsPanel {
    border-left: 1px solid #e9ecef;
    border-right: none;
}

[dir="rtl"] #TopBar {
    text-align: right;
}

[dir="rtl"] #StatusBar {
    text-align: right;
}

[dir="rtl"] #ServerCard {
    text-align: right;
    direction: rtl;
}

[dir="rtl"] #ServerCard::title {
    text-align: right;
    padding-right: 8px;
    padding-left: 0px;
}

[dir="rtl"] #ServerCard::subtitle {
    text-align: right;
    padding-right: 8px;
    padding-left: 0px;
}

/* === RTL Dark Mode Support === */
[dir="rtl"] QWidget {
    font-family: "Vazirmatn", "Tahoma", "Inter", "Segoe UI", "SF Pro Display", system-ui, sans-serif;
}

/* === RTL Animation Support === */
[dir="rtl"] QPropertyAnimation {
    direction: rtl;
}

[dir="rtl"] QParallelAnimationGroup {
    direction: rtl;
}

[dir="rtl"] QSequentialAnimationGroup {
    direction: rtl;
}

/* === RTL Focus Indicators === */
[dir="rtl"] QWidget:focus {
    outline: none;
}

[dir="rtl"] QLineEdit:focus {
    border-right: 2px solid #6366f1;
    border-left: 1px solid #d1d5db;
}

[dir="rtl"] QComboBox:focus {
    border-right: 2px solid #6366f1;
    border-left: 1px solid #d1d5db;
}

[dir="rtl"] QTextEdit:focus {
    border-right: 2px solid #6366f1;
    border-left: 1px solid #d1d5db;
}

/* === RTL Hover Effects === */
[dir="rtl"] QPushButton:hover {
    padding-right: 18px;
    padding-left: 6px;
}

[dir="rtl"] QListWidget::item:hover {
    padding-right: 14px;
    padding-left: 6px;
}

[dir="rtl"] QTableWidget::item:hover {
    padding-right: 14px;
    padding-left: 6px;
}

/* === RTL Selection Indicators === */
[dir="rtl"] QListWidget::item:selected {
    background-color: #e0e7ff;
    border-right: 2px solid #6366f1;
    border-left: 1px solid #e5e7eb;
}

[dir="rtl"] QTableWidget::item:selected {
    background-color: #e0e7ff;
    border-right: 2px solid #6366f1;
    border-left: 1px solid #e5e7eb;
}

/* === RTL Disabled State === */
[dir="rtl"] QWidget:disabled {
    color: #9ca3af;
}

[dir="rtl"] QLineEdit:disabled {
    background-color: #f9fafb;
    border-right: 1px solid #e5e7eb;
    border-left: 1px solid #e5e7eb;
}

[dir="rtl"] QComboBox:disabled {
    background-color: #f9fafb;
    border-right: 1px solid #e5e7eb;
    border-left: 1px solid #e5e7eb;
}

/* === RTL High Contrast Mode === */
@media (prefers-contrast: high) {
    [dir="rtl"] QWidget {
        border: 1px solid;
    }
    
    [dir="rtl"] QPushButton {
        border: 2px solid;
    }
    
    [dir="rtl"] QLineEdit {
        border: 2px solid;
    }
    
    [dir="rtl"] QComboBox {
        border: 2px solid;
    }
}

/* === RTL Reduced Motion === */
@media (prefers-reduced-motion: reduce) {
    [dir="rtl"] * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
"""


def get_rtl_dark_stylesheet() -> str:
    """Get RTL stylesheet for dark mode."""
    return get_rtl_stylesheet().replace(
        "#d1d5db", "#475569"
    ).replace(
        "#e5e7eb", "#334155"
    ).replace(
        "#f9fafb", "#1e293b"
    ).replace(
        "#e0e7ff", "#1e3a8a"
    ).replace(
        "#6366f1", "#818cf8"
    ).replace(
        "#6b7280", "#94a3b8"
    ).replace(
        "#9ca3af", "#64748b"
    )


def apply_rtl_styles(app, is_dark_mode: bool = False) -> None:
    """Apply RTL styles to the application."""
    try:
        rtl_stylesheet = get_rtl_dark_stylesheet() if is_dark_mode else get_rtl_stylesheet()
        app.setStyleSheet(app.styleSheet() + rtl_stylesheet)
    except Exception as e:
        print(f"Error applying RTL styles: {e}")


def is_rtl_language(language: str) -> bool:
    """Check if a language is RTL."""
    rtl_languages = ["fa", "ar", "he", "ur", "ku", "ps", "sd"]
    return language in rtl_languages


def get_rtl_font_family() -> str:
    """Get appropriate font family for RTL languages."""
    return '"Vazirmatn", "Tahoma", "Inter", "Segoe UI", "SF Pro Display", system-ui, sans-serif'
