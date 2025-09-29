THEMES = {
    "blue": {
        "primary": "#6366f1",        # Modern Indigo
        "primary_hover": "#4f46e5",
        "primary_light": "#818cf8",
        "primary_light_hover": "#6366f1",
        "selected_bg": "#e0e7ff",
        "primary_dark": "#4338ca",
    },
    "green": {
        "primary": "#10b981",        # Modern Emerald
        "primary_hover": "#059669",
        "primary_light": "#34d399",
        "primary_light_hover": "#10b981",
        "selected_bg": "#d1fae5",
        "primary_dark": "#047857",
    },
    "purple": {
        "primary": "#8b5cf6",        # Modern Violet
        "primary_hover": "#7c3aed",
        "primary_light": "#a78bfa",
        "primary_light_hover": "#8b5cf6",
        "selected_bg": "#ede9fe",
        "primary_dark": "#6d28d9",
    },
    "rose": {
        "primary": "#f43f5e",        # Modern Rose
        "primary_hover": "#e11d48",
        "primary_light": "#fb7185",
        "primary_light_hover": "#f43f5e",
        "selected_bg": "#ffe4e6",
        "primary_dark": "#be123c",
    }
}

# --- Stylesheets ---


def get_light_stylesheet(theme):
    return """
QWidget {{
    background-color: #fafafa; /* Modern light background */
    color: #1f2937; /* Modern dark text */
    font-family: "Inter", "Segoe UI", "SF Pro Display", system-ui, sans-serif;
    font-size: 14px;
    font-weight: 400;
}}

/* --- RTL Support --- */
[dir="rtl"] QHBoxLayout {{
    direction: rtl;
}}
[dir="rtl"] QVBoxLayout {{
    direction: rtl;
}}
[dir="rtl"] QLabel {{
    text-align: right;
    min-width: 80px;
}}
[dir="rtl"] QLineEdit {{
    text-align: right;
    min-width: 120px;
}}
[dir="rtl"] QTextEdit {{
    text-align: right;
    min-width: 200px;
}}
[dir="rtl"] QComboBox {{
    text-align: right;
    min-width: 120px;
}}
[dir="rtl"] QPushButton {{
    text-align: right;
    min-width: 80px;
}}
[dir="rtl"] QListWidget {{
    text-align: right;
    min-width: 200px;
}}
[dir="rtl"] QGroupBox {{
    text-align: right;
    min-width: 200px;
}}
[dir="rtl"] QGroupBox::title {{
    right: 16px;
    left: auto;
}}
[dir="rtl"] QMenu {{
    text-align: right;
    min-width: 120px;
}}
[dir="rtl"] QHeaderView::section {{
    text-align: right;
    min-width: 100px;
    min-height: 32px;
}}
[dir="rtl"] QProgressBar {{
    text-align: right;
    min-width: 100px;
    min-height: 20px;
}}
[dir="rtl"] QCheckBox {{
    text-align: right;
    min-width: 120px;
    min-height: 24px;
}}
[dir="rtl"] QRadioButton {{
    text-align: right;
    min-width: 120px;
    min-height: 24px;
}}

/* --- RTL Layout Support --- */
[dir="rtl"] #NavRail {{
    border-right: none;
    border-left: 1px solid #dee2e6;
}}
[dir="rtl"] #ServerDetailsPanel {{
    border-left: none;
    border-right: 1px solid #e9ecef;
}}
[dir="rtl"] #TopBar {{
    direction: rtl;
}}
[dir="rtl"] #StatusBar {{
    direction: rtl;
}}
QLabel {{ background-color: transparent; }}
QMainWindow, #CentralWidget {{ background-color: #fafafa; }}

/* --- Containers --- */
QListWidget, QTableWidget, QTextEdit, QGroupBox, QScrollArea {{
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    min-width: 200px;
}}
QGroupBox {{ 
    margin-top: 16px; 
    padding: 24px 16px 16px 16px; 
    background: linear-gradient(135deg, #ffffff, #f9fafb);
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    padding: 0 8px;
    font-weight: 600;
    font-size: 16px;
    color: #374151;
    background: #fafafa;
}}

/* --- Top Bar & Status Bar --- */
#TopBar, #StatusBar {{
    background-color: #ffffff;
    border: none;
}}
#TopBar {{ 
    border-bottom: 1px solid #e5e7eb; 
    padding: 8px 16px;
}}
#StatusBar {{ 
    border-top: 1px solid #e5e7eb; 
    padding: 4px 8px;
    min-height: 50px;
}}

/* --- Navigation --- */
#NavRail {{ 
    background-color: #f8f9fa;
    border-right: 1px solid #dee2e6;
    padding: 16px 0;
    min-width: 100px;
    max-width: 150px;
}}
#NavRail::item {{ 
    border: none; 
    padding: 12px 16px; 
    margin: 4px 8px;
    color: #6b7280;
    border-radius: 6px;
}}
#NavRail::item:selected {{ 
    background-color: {primary};
    color: white;
    font-weight: 600;
}}

/* --- Server List --- */
QListWidget {{
    background-color: transparent;
    border: none;
    padding: 8px;
}}
QListWidget::item {{
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    margin: 4px 0;
    padding: 12px;
}}
QListWidget::item:hover {{
    border-color: {primary};
    background-color: #f8fafc;
}}
QListWidget::item:selected {{ 
    border-color: {primary};
    background-color: {selected_bg};
}}

/* --- Main Buttons --- */
QPushButton {{
    background-color: {primary};
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: 500;
    font-size: 13px;
}}
QPushButton:hover {{ 
    background-color: {primary_hover};
}}
QPushButton:pressed {{
    background-color: {primary_dark};
}}
QPushButton:disabled {{ 
    background-color: #6c757d; 
    color: #adb5bd; 
}}

/* Header Buttons */
#TopBar QPushButton, #StatusBar QPushButton {{
    background-color: #f8f9fa;
    color: #374151;
    border: 1px solid #dee2e6;
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
    min-width: 80px;
    max-width: 140px;
}}
#TopBar QPushButton:hover, #StatusBar QPushButton:hover {{ 
    background-color: #e9ecef;
    border-color: #adb5bd;
}}
#TopBar QPushButton:pressed, #StatusBar QPushButton:pressed {{ 
    background-color: #dee2e6;
}}
#TopBar QPushButton:disabled, #StatusBar QPushButton:disabled {{ 
    background-color: #f8f9fa; 
    color: #6c757d; 
    border-color: #e9ecef; 
}}

/* --- Server Card Menu Button --- */
#ServerCardMenuButton {{
    background-color: transparent;
    border: none;
    border-radius: 4px;
    color: #6b7280;
    padding: 4px 8px;
    font-size: 12px;
}}
#ServerCardMenuButton:hover {{
    background-color: #f8f9fa;
    color: {primary};
}}

/* --- Inputs --- */
QLineEdit, QComboBox {{
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
}}
QLineEdit:focus, QComboBox:focus {{
    border-color: {primary};
    background-color: #f8fafc;
}}
QComboBox QAbstractItemView {{
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    selection-background-color: {primary};
    padding: 8px;
}}

/* --- Other Widgets --- */
QMenu {{ 
    background-color: #ffffff; 
    border: 1px solid #e5e7eb; 
    border-radius: 8px; 
    padding: 8px;
    min-width: 120px;
}}
QMenu::item {{
    padding: 8px 16px;
    border-radius: 6px;
    margin: 2px;
}}
QMenu::item:selected {{ 
    background-color: {primary}; 
    color: white; 
}}
QHeaderView::section {{ 
    background: linear-gradient(135deg, #f8fafc, #f1f5f9);
    padding: 12px 16px; 
    border: 1px solid #e5e7eb; 
    font-weight: 600;
    color: #374151;
    min-width: 100px;
    min-height: 32px;
}}

/* --- Progress Bar --- */
QProgressBar {{
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    text-align: center;
    background-color: #f3f4f6;
    font-weight: 600;
    min-width: 100px;
    min-height: 20px;
}}
QProgressBar::chunk {{
    background: linear-gradient(135deg, {primary}, {primary_light});
    border-radius: 6px;
}}

/* --- Checkbox --- */
QCheckBox {{
    spacing: 8px;
    font-size: 14px;
    min-width: 120px;
    min-height: 24px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid #d1d5db;
    border-radius: 4px;
    background-color: #ffffff;
}}
QCheckBox::indicator:checked {{
    background: linear-gradient(135deg, {primary}, {primary_hover});
    border-color: {primary};
}}
QCheckBox::indicator:hover {{
    border-color: {primary};
}}

/* --- Radio Button --- */
QRadioButton {{
    spacing: 8px;
    font-size: 14px;
    min-width: 120px;
    min-height: 24px;
}}
QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid #d1d5db;
    border-radius: 9px;
    background-color: #ffffff;
}}
QRadioButton::indicator:checked {{
    background: linear-gradient(135deg, {primary}, {primary_hover});
    border-color: {primary};
}}
""".format(
        primary=theme['primary'],
        primary_hover=theme['primary_hover'],
        primary_light=theme['primary_light'],
        primary_dark=theme['primary_dark'],
        selected_bg=theme['selected_bg']
    )


def get_dark_stylesheet(theme):
    return """
QWidget {{
    background-color: #0f172a; /* Modern dark background */
    color: #f1f5f9; /* Modern light text */
    font-family: "Inter", "Segoe UI", "SF Pro Display", system-ui, sans-serif;
    font-size: 14px;
    font-weight: 400;
}}

/* --- RTL Support for Dark Mode --- */
[dir="rtl"] QHBoxLayout {{
    direction: rtl;
}}
[dir="rtl"] QVBoxLayout {{
    direction: rtl;
}}
[dir="rtl"] QLabel {{
    text-align: right;
    min-width: 80px;
}}
[dir="rtl"] QLineEdit {{
    text-align: right;
    min-width: 120px;
}}
[dir="rtl"] QTextEdit {{
    text-align: right;
    min-width: 200px;
}}
[dir="rtl"] QComboBox {{
    text-align: right;
    min-width: 120px;
}}
[dir="rtl"] QPushButton {{
    text-align: right;
    min-width: 80px;
}}
[dir="rtl"] QListWidget {{
    text-align: right;
    min-width: 200px;
}}
[dir="rtl"] QGroupBox {{
    text-align: right;
    min-width: 200px;
}}
[dir="rtl"] QGroupBox::title {{
    right: 16px;
    left: auto;
}}
[dir="rtl"] QMenu {{
    text-align: right;
    min-width: 120px;
}}
[dir="rtl"] QHeaderView::section {{
    text-align: right;
    min-width: 100px;
    min-height: 32px;
}}
[dir="rtl"] QProgressBar {{
    text-align: right;
    min-width: 100px;
    min-height: 20px;
}}
[dir="rtl"] QCheckBox {{
    text-align: right;
    min-width: 120px;
    min-height: 24px;
}}
[dir="rtl"] QRadioButton {{
    text-align: right;
    min-width: 120px;
    min-height: 24px;
}}

/* --- RTL Layout Support for Dark Mode --- */
[dir="rtl"] #NavRail {{
    border-right: none;
    border-left: 1px solid #475569;
}}
[dir="rtl"] #ServerDetailsPanel {{
    border-left: none;
    border-right: 1px solid #495057;
}}
[dir="rtl"] #TopBar {{
    direction: rtl;
}}
[dir="rtl"] #StatusBar {{
    direction: rtl;
}}
QLabel {{ background-color: transparent; }}
QMainWindow, #CentralWidget {{ background-color: #0f172a; }}

/* --- Containers --- */
QListWidget, QTableWidget, QTextEdit, QGroupBox, QScrollArea {{
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    min-width: 200px;
}}
QGroupBox {{ 
    margin-top: 16px; 
    padding: 24px 16px 16px 16px; 
    background: linear-gradient(135deg, #1e293b, #0f172a);
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    padding: 0 8px;
    font-weight: 600;
    font-size: 16px;
    color: #cbd5e1;
    background: #0f172a;
}}

/* --- Top Bar & Status Bar --- */
#TopBar, #StatusBar {{
    background-color: #1e293b;
    border: none;
}}
#TopBar {{ 
    border-bottom: 1px solid #334155; 
    padding: 8px 16px;
}}
#StatusBar {{ 
    border-top: 1px solid #334155; 
    padding: 4px 8px;
    min-height: 50px;
}}

/* --- Navigation --- */
#NavRail {{ 
    background-color: #1e293b;
    border-right: 1px solid #334155;
    padding: 16px 0;
}}
#NavRail::item {{ 
    border: none; 
    padding: 12px 16px; 
    margin: 4px 8px;
    color: #94a3b8;
    border-radius: 6px;
}}
#NavRail::item:selected {{ 
    background-color: {primary};
    color: white;
    font-weight: 600;
}}

/* --- Server List --- */
QListWidget {{
    background-color: transparent;
    border: none;
    padding: 8px;
}}
QListWidget::item {{
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    margin: 4px 0;
    padding: 12px;
}}
QListWidget::item:hover {{
    border-color: {primary};
    background-color: #334155;
}}
QListWidget::item:selected {{ 
    border-color: {primary};
    background-color: {selected_bg};
}}

/* --- Main Buttons --- */
QPushButton {{
    background-color: {primary};
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: 500;
    font-size: 13px;
}}
QPushButton:hover {{ 
    background-color: {primary_hover};
}}
QPushButton:pressed {{
    background-color: {primary_dark};
}}
QPushButton:disabled {{ 
    background-color: #6c757d; 
    color: #adb5bd; 
}}

/* Header Buttons */
#TopBar QPushButton, #StatusBar QPushButton {{
    background-color: #334155;
    color: #cbd5e1;
    border: 1px solid #475569;
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
    min-width: 80px;
    max-width: 140px;
}}
#TopBar QPushButton:hover, #StatusBar QPushButton:hover {{ 
    background-color: #475569;
    border-color: #64748b;
}}
#TopBar QPushButton:pressed, #StatusBar QPushButton:pressed {{ 
    background-color: #475569;
}}
#TopBar QPushButton:disabled, #StatusBar QPushButton:disabled {{ 
    background-color: #1e293b; 
    color: #64748b; 
    border-color: #334155; 
}}

/* --- Server Card Menu Button --- */
#ServerCardMenuButton {{
    background-color: transparent;
    border: none;
    border-radius: 4px;
    color: #94a3b8;
    padding: 4px 8px;
    font-size: 12px;
}}
#ServerCardMenuButton:hover {{
    background-color: #334155;
    color: {primary};
}}

/* --- Inputs --- */
QLineEdit, QComboBox {{
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
    color: #f1f5f9;
}}
QLineEdit:focus, QComboBox:focus {{
    border-color: {primary};
    background-color: #334155;
}}
QComboBox QAbstractItemView {{
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    selection-background-color: {primary};
    padding: 8px;
    color: #f1f5f9;
}}

/* --- Other Widgets --- */
QMenu {{ 
    background-color: #1e293b; 
    border: 1px solid #334155; 
    border-radius: 8px; 
    padding: 8px;
    min-width: 120px;
}}
QMenu::item {{
    padding: 8px 16px;
    border-radius: 6px;
    margin: 2px;
    color: #f1f5f9;
}}
QMenu::item:selected {{ 
    background-color: {primary}; 
    color: white; 
}}
QHeaderView::section {{
    background: linear-gradient(135deg, #1e293b, #0f172a);
    padding: 12px 16px;
    border: 1px solid #334155;
    font-weight: 600;
    color: #cbd5e1;
    min-width: 100px;
    min-height: 32px;
}}

/* --- Progress Bar --- */
QProgressBar {{
    border: 2px solid #334155;
    border-radius: 8px;
    text-align: center;
    background-color: #0f172a;
    font-weight: 600;
    color: #f1f5f9;
    min-width: 100px;
    min-height: 20px;
}}
QProgressBar::chunk {{
    background: linear-gradient(135deg, {primary}, {primary_light});
    border-radius: 6px;
}}

/* --- Checkbox --- */
QCheckBox {{
    spacing: 8px;
    font-size: 14px;
    color: #f1f5f9;
    min-width: 120px;
    min-height: 24px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid #475569;
    border-radius: 4px;
    background-color: #1e293b;
}}
QCheckBox::indicator:checked {{
    background: linear-gradient(135deg, {primary}, {primary_hover});
    border-color: {primary};
}}
QCheckBox::indicator:hover {{
    border-color: {primary};
}}

/* --- Radio Button --- */
QRadioButton {{
    spacing: 8px;
    font-size: 14px;
    color: #f1f5f9;
    min-width: 120px;
    min-height: 24px;
}}
QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid #475569;
    border-radius: 9px;
    background-color: #1e293b;
}}
QRadioButton::indicator:checked {{
    background: linear-gradient(135deg, {primary}, {primary_hover});
    border-color: {primary};
}}
""".format(
        primary=theme['primary'],
        primary_hover=theme['primary_hover'],
        primary_light=theme['primary_light'],
        primary_dark=theme['primary_dark'],
        selected_bg=theme['selected_bg']
    )
