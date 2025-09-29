THEMES = {
    "blue": {
        "primary": "#0052d9",
        "primary_hover": "#0041ac",
        "primary_light": "#4599ff",
        "primary_light_hover": "#377fdb",
        "selected_bg": "#e8f0fe",
    },
    "green": {
        "primary": "#1DB954",
        "primary_hover": "#1AAE4D",
        "primary_light": "#20c964",
        "primary_light_hover": "#1da855",
        "selected_bg": "#e8f5e9",
    },
    "dark-blue": {
        "primary": "#0d6efd",
        "primary_hover": "#0b5ed7",
        "primary_light": "#3daee9",
        "primary_light_hover": "#299ad6",
        "selected_bg": "#e7f4fd",
    }
}

# --- Stylesheets ---


def get_light_stylesheet(theme):
    return """
QWidget {{
    background-color: #f0f2f5; /* Light Gray */
    color: #1c1e21; /* Dark Gray */
    font-family: "Segoe UI", "Helvetica Neue", "Arial", sans-serif;
    font-size: 10pt;
}}
QLabel {{ background-color: transparent; }}
QMainWindow, #CentralWidget {{ background-color: #f0f2f5; }}

/* --- Containers --- */
QListWidget, QTableWidget, QTextEdit, QGroupBox, QScrollArea {{
    background-color: #ffffff;
    border: 1px solid #dcdfe6;
    border-radius: 6px;
}}
QGroupBox {{ margin-top: 10px; padding: 20px 10px 10px 10px; }}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 3px;
    font-weight: bold;
    color: #606266;
}}

/* --- Top Bar & Status Bar --- */
#TopBar, #StatusBar {{
    background-color: #ffffff;
    border-color: #dcdfe6;
}}
#TopBar {{ border-bottom: 1px solid #dcdfe6; }}
#StatusBar {{ border-top: 1px solid #dcdfe6; }}

/* --- Navigation --- */
#NavRail {{ background-color: #e4e6eb; border: none; }}
#NavRail::item {{ border: none; padding: 8px; color: #4b4f56; }}
#NavRail::item:selected {{ background-color: #ffffff; color: #0052d9; font-weight: bold; }}

/* --- Server List --- */
QListWidget {{
    background-color: #ffffff; /* Solid white background for the whole list */
    border: none;
    padding: 0px;
}}
QListWidget::item {{
    background-color: transparent;
    border-bottom: 1px solid #f0f2f5; /* Light separator line */
    padding: 12px 15px;
}}
QListWidget::item:hover {{
    background-color: #f5f5f5; /* Subtle hover */
}}
QListWidget::item:selected {{ 
    border-left: 3px solid {primary};
    background-color: {selected_bg};
    padding-left: 12px; /* Adjust padding for the border */
}}

/* --- Buttons --- */
QPushButton {{
    background-color: {primary};
    color: white;
    border: none;
    padding: 8px 12px;
    border-radius: 6px;
    font-weight: bold;
}}
QPushButton:hover {{ background-color: {primary_hover}; }}
QPushButton:disabled {{ background-color: #a0a0a0; color: #e0e0e0; }}

/* Specific Buttons */
#TopBar QPushButton, #StatusBar QPushButton {{
    background-color: #e9ebee;
    color: #1c1e21;
    border: 1px solid #dcdfe6;
}}
#TopBar QPushButton:hover, #StatusBar QPushButton:hover {{ background-color: #dcdfe6; }}
#TopBar QPushButton:disabled, #StatusBar QPushButton:disabled {{ background-color: #f0f2f5; color: #a0a0a0; border-color: #e9ebee; }}

/* --- Server Card Menu Button --- */
#ServerCardMenuButton {{
    background-color: transparent;
    border: none;
    border-radius: 6px;
    color: #606266; /* Icon color */
}}
#ServerCardMenuButton:hover {{
    background-color: #dcdfe6;
}}

/* --- Inputs --- */
QLineEdit, QComboBox {{
    background-color: #ffffff;
    border: 1px solid #dcdfe6;
    border-radius: 6px;
    padding: 6px;
}}
QComboBox QAbstractItemView {{
    background-color: #ffffff;
    border: 1px solid #dcdfe6;
    selection-background-color: {primary};
}}

/* --- Other Widgets --- */
QMenu {{ background-color: #ffffff; border: 1px solid #dcdfe6; border-radius: 6px; }}
QMenu::item:selected {{ background-color: {primary}; color: white; }}
QHeaderView::section {{ background-color: #f5f7fa; padding: 6px; border: 1px solid #dcdfe6; font-weight: bold; }}
""".format(primary=theme['primary'], primary_hover=theme['primary_hover'], selected_bg=theme['selected_bg'])


def get_dark_stylesheet(theme):
    return """
QWidget {{
    background-color: #1c1c1e; /* Very Dark Gray */
    color: #e4e6eb;
    font-family: "Segoe UI", "Helvetica Neue", "Arial", sans-serif;
    font-size: 10pt;
}}
QLabel {{ background-color: transparent; }}
QMainWindow, #CentralWidget {{ background-color: #1c1c1e; }}

/* --- Containers --- */
QListWidget, QTableWidget, QTextEdit, QGroupBox, QScrollArea {{
    background-color: #28282a;
    border: 1px solid #3a3a3c;
    border-radius: 6px;
}}
QGroupBox {{ margin-top: 10px; padding: 20px 10px 10px 10px; }}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 3px;
    font-weight: bold;
    color: #b0b3b8;
}}

/* --- Top Bar & Status Bar --- */
#TopBar, #StatusBar {{
    background-color: #242526;
    border-color: #3a3a3c;
}}
#TopBar {{ border-bottom: 1px solid #3a3a3c; }}
#StatusBar {{ border-top: 1px solid #3a3a3c; }}

/* --- Navigation --- */
#NavRail {{ background-color: #3a3a3c; border: none; }}
#NavRail::item {{ border: none; padding: 8px; color: #b0b3b8; }}
#NavRail::item:selected {{ background-color: #1c1c1e; color: #4599ff; font-weight: bold; }}

/* --- Server List --- */
QListWidget {{
    background-color: #242526; /* Solid dark background for the whole list */
    border: none;
    padding: 0px;
}}
QListWidget::item {{
    background-color: transparent;
    border-bottom: 1px solid #3a3a3c; /* Light separator line */
    padding: 12px 15px;
}}
QListWidget::item:hover {{
    background-color: #303031; /* Subtle hover */
}}
QListWidget::item:selected {{ 
    border-left: 3px solid {primary_light};
    background-color: #3a3a3c;
    padding-left: 12px; /* Adjust padding for the border */
}}

/* --- Buttons --- */
QPushButton {{
    background-color: {primary_light};
    color: #ffffff;
    border: none;
    padding: 8px 12px;
    border-radius: 6px;
    font-weight: bold;
}}
QPushButton:hover {{ background-color: {primary_light_hover}; }}
QPushButton:disabled {{ background-color: #4e4e50; color: #8a8d91; }}

/* Specific Buttons */
#TopBar QPushButton, #StatusBar QPushButton {{
    background-color: #3a3a3c;
    color: #e4e6eb;
    border: 1px solid #555557;
}}
#TopBar QPushButton:hover, #StatusBar QPushButton:hover {{ background-color: #4e4e50; }}
#TopBar QPushButton:disabled, #StatusBar QPushButton:disabled {{ background-color: #28282a; color: #8a8d91; border-color: #3a3a3c; }}

/* --- Server Card Menu Button --- */
#ServerCardMenuButton {{
    background-color: transparent;
    border: none;
    border-radius: 6px;
    color: #b0b3b8; /* Icon color */
}}
#ServerCardMenuButton:hover {{
    background-color: #4e4e50;
}}

/* --- Inputs --- */
QLineEdit, QComboBox {{
    background-color: #3a3a3c;
    border: 1px solid #555557;
    border-radius: 6px;
    padding: 6px;
}}
QComboBox QAbstractItemView {{
    background-color: #3a3a3c;
    border: 1px solid #555557;
    selection-background-color: {primary_light};
}}

/* --- Other Widgets --- */
QMenu {{ background-color: #28282a; border: 1px solid #3a3a3c; border-radius: 6px; }}
QMenu::item:selected {{ background-color: {primary_light}; color: white; }}
QHeaderView::section {{ background-color: #3a3a3c; padding: 6px; border: 1px solid #555557; font-weight: bold; }}
""".format(primary_light=theme['primary_light'], primary_light_hover=theme['primary_light_hover'])
