"""
Custom Themes for Onix
Provides additional themes and theme management
"""

from PySide6.QtCore import QObject, Signal
from typing import Dict, Any, List
from constants import LogLevel


class ThemeManager(QObject):
    """Manager for custom themes."""

    theme_changed = Signal(str)  # Emitted when theme changes

    def __init__(self, log_callback):
        super().__init__()
        self.log = log_callback
        self._themes = self._load_default_themes()
        self._current_theme = "default"

    def get_available_themes(self) -> List[str]:
        """Get list of available theme names."""
        return list(self._themes.keys())

    def get_theme(self, theme_name: str) -> Dict[str, Any]:
        """Get theme configuration."""
        return self._themes.get(theme_name, self._themes["default"])

    def set_theme(self, theme_name: str) -> bool:
        """Set current theme."""
        if theme_name in self._themes:
            self._current_theme = theme_name
            self.theme_changed.emit(theme_name)
            self.log(f"Switched to theme: {theme_name}", LogLevel.SUCCESS)
            return True
        return False

    def get_current_theme(self) -> str:
        """Get current theme name."""
        return self._current_theme

    def create_custom_theme(self, name: str, config: Dict[str, Any]) -> bool:
        """Create a custom theme."""
        try:
            self._themes[name] = config
            self.log(f"Created custom theme: {name}", LogLevel.SUCCESS)
            return True
        except Exception as e:
            self.log(f"Failed to create custom theme: {e}", LogLevel.ERROR)
            return False

    def _load_default_themes(self) -> Dict[str, Dict[str, Any]]:
        """Load default themes."""
        return {
            "default": {
                "name": "Default",
                "colors": {
                    "primary": "#007bff",
                    "secondary": "#6c757d",
                    "success": "#28a745",
                    "danger": "#dc3545",
                    "warning": "#ffc107",
                    "info": "#17a2b8",
                    "light": "#f8f9fa",
                    "dark": "#343a40",
                    "background": "#ffffff",
                    "surface": "#f8f9fa",
                    "text": "#212529",
                    "text_secondary": "#6c757d"
                },
                "fonts": {
                    "family": "Segoe UI",
                    "size": 12,
                    "weight": "normal"
                },
                "spacing": {
                    "small": 4,
                    "medium": 8,
                    "large": 16,
                    "xlarge": 24
                },
                "borders": {
                    "radius": 4,
                    "width": 1,
                    "color": "#dee2e6"
                }
            },
            "dark": {
                "name": "Dark",
                "colors": {
                    "primary": "#3daee9",
                    "secondary": "#6c757d",
                    "success": "#28a745",
                    "danger": "#dc3545",
                    "warning": "#ffc107",
                    "info": "#17a2b8",
                    "light": "#f8f9fa",
                    "dark": "#212529",
                    "background": "#1e1e1e",
                    "surface": "#2d2d2d",
                    "text": "#ffffff",
                    "text_secondary": "#b3b3b3"
                },
                "fonts": {
                    "family": "Segoe UI",
                    "size": 12,
                    "weight": "normal"
                },
                "spacing": {
                    "small": 4,
                    "medium": 8,
                    "large": 16,
                    "xlarge": 24
                },
                "borders": {
                    "radius": 4,
                    "width": 1,
                    "color": "#495057"
                }
            },
            "neon": {
                "name": "Neon",
                "colors": {
                    "primary": "#00ff00",
                    "secondary": "#ff00ff",
                    "success": "#00ff00",
                    "danger": "#ff0000",
                    "warning": "#ffff00",
                    "info": "#00ffff",
                    "light": "#f8f9fa",
                    "dark": "#000000",
                    "background": "#000000",
                    "surface": "#111111",
                    "text": "#00ff00",
                    "text_secondary": "#00aa00"
                },
                "fonts": {
                    "family": "Consolas",
                    "size": 12,
                    "weight": "bold"
                },
                "spacing": {
                    "small": 4,
                    "medium": 8,
                    "large": 16,
                    "xlarge": 24
                },
                "borders": {
                    "radius": 0,
                    "width": 2,
                    "color": "#00ff00"
                }
            },
            "ocean": {
                "name": "Ocean",
                "colors": {
                    "primary": "#0077be",
                    "secondary": "#4a90e2",
                    "success": "#00d4aa",
                    "danger": "#ff6b6b",
                    "warning": "#ffd93d",
                    "info": "#74b9ff",
                    "light": "#f0f8ff",
                    "dark": "#1e3a8a",
                    "background": "#f0f8ff",
                    "surface": "#e6f3ff",
                    "text": "#1e3a8a",
                    "text_secondary": "#4a90e2"
                },
                "fonts": {
                    "family": "Segoe UI",
                    "size": 12,
                    "weight": "normal"
                },
                "spacing": {
                    "small": 4,
                    "medium": 8,
                    "large": 16,
                    "xlarge": 24
                },
                "borders": {
                    "radius": 8,
                    "width": 1,
                    "color": "#4a90e2"
                }
            },
            "sunset": {
                "name": "Sunset",
                "colors": {
                    "primary": "#ff6b35",
                    "secondary": "#f7931e",
                    "success": "#4ecdc4",
                    "danger": "#ff4757",
                    "warning": "#ffa502",
                    "info": "#3742fa",
                    "light": "#fff5f5",
                    "dark": "#2f3542",
                    "background": "#fff5f5",
                    "surface": "#ffe8e8",
                    "text": "#2f3542",
                    "text_secondary": "#ff6b35"
                },
                "fonts": {
                    "family": "Segoe UI",
                    "size": 12,
                    "weight": "normal"
                },
                "spacing": {
                    "small": 4,
                    "medium": 8,
                    "large": 16,
                    "xlarge": 24
                },
                "borders": {
                    "radius": 6,
                    "width": 1,
                    "color": "#ff6b35"
                }
            },
            "forest": {
                "name": "Forest",
                "colors": {
                    "primary": "#2d5016",
                    "secondary": "#4a7c59",
                    "success": "#2d5016",
                    "danger": "#8b0000",
                    "warning": "#daa520",
                    "info": "#4682b4",
                    "light": "#f0fff0",
                    "dark": "#1a1a1a",
                    "background": "#f0fff0",
                    "surface": "#e6ffe6",
                    "text": "#1a1a1a",
                    "text_secondary": "#2d5016"
                },
                "fonts": {
                    "family": "Segoe UI",
                    "size": 12,
                    "weight": "normal"
                },
                "spacing": {
                    "small": 4,
                    "medium": 8,
                    "large": 16,
                    "xlarge": 24
                },
                "borders": {
                    "radius": 4,
                    "width": 1,
                    "color": "#4a7c59"
                }
            },
            "midnight": {
                "name": "Midnight",
                "colors": {
                    "primary": "#6366f1",
                    "secondary": "#8b5cf6",
                    "success": "#10b981",
                    "danger": "#ef4444",
                    "warning": "#f59e0b",
                    "info": "#06b6d4",
                    "light": "#f8fafc",
                    "dark": "#0f172a",
                    "background": "#0f172a",
                    "surface": "#1e293b",
                    "text": "#f8fafc",
                    "text_secondary": "#94a3b8"
                },
                "fonts": {
                    "family": "Segoe UI",
                    "size": 12,
                    "weight": "normal"
                },
                "spacing": {
                    "small": 4,
                    "medium": 8,
                    "large": 16,
                    "xlarge": 24
                },
                "borders": {
                    "radius": 6,
                    "width": 1,
                    "color": "#334155"
                }
            }
        }


def generate_theme_stylesheet(theme_config: Dict[str, Any]) -> str:
    """Generate stylesheet from theme configuration."""
    colors = theme_config["colors"]
    fonts = theme_config["fonts"]
    spacing = theme_config["spacing"]
    borders = theme_config["borders"]

    return f"""
    /* Main Application Styles */
    QMainWindow {{
        background-color: {colors['background']};
        color: {colors['text']};
    }}
    
    /* Buttons */
    QPushButton {{
        background-color: {colors['primary']};
        color: white;
        border: {borders['width']}px solid {colors['primary']};
        border-radius: {borders['radius']}px;
        padding: {spacing['small']}px {spacing['medium']}px;
        font-family: {fonts['family']};
        font-size: {fonts['size']}px;
        font-weight: {fonts['weight']};
    }}
    
    QPushButton:hover {{
        background-color: {colors['secondary']};
        border-color: {colors['secondary']};
    }}
    
    QPushButton:pressed {{
        background-color: {colors['dark']};
        border-color: {colors['dark']};
    }}
    
    /* Input Fields */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {colors['surface']};
        color: {colors['text']};
        border: {borders['width']}px solid {borders['color']};
        border-radius: {borders['radius']}px;
        padding: {spacing['small']}px;
        font-family: {fonts['family']};
        font-size: {fonts['size']}px;
    }}
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {colors['primary']};
    }}
    
    /* Combo Boxes */
    QComboBox {{
        background-color: {colors['surface']};
        color: {colors['text']};
        border: {borders['width']}px solid {borders['color']};
        border-radius: {borders['radius']}px;
        padding: {spacing['small']}px;
        font-family: {fonts['family']};
        font-size: {fonts['size']}px;
    }}
    
    QComboBox::drop-down {{
        border: none;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid {colors['text']};
        margin-right: 5px;
    }}
    
    /* Checkboxes and Radio Buttons */
    QCheckBox, QRadioButton {{
        color: {colors['text']};
        font-family: {fonts['family']};
        font-size: {fonts['size']}px;
    }}
    
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 16px;
        height: 16px;
        border: {borders['width']}px solid {borders['color']};
        border-radius: {borders['radius']}px;
        background-color: {colors['surface']};
    }}
    
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background-color: {colors['primary']};
        border-color: {colors['primary']};
    }}
    
    /* Group Boxes */
    QGroupBox {{
        color: {colors['text']};
        font-family: {fonts['family']};
        font-size: {fonts['size']}px;
        font-weight: bold;
        border: {borders['width']}px solid {borders['color']};
        border-radius: {borders['radius']}px;
        margin-top: {spacing['small']}px;
        padding-top: {spacing['medium']}px;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: {spacing['medium']}px;
        padding: 0 {spacing['small']}px 0 {spacing['small']}px;
    }}
    
    /* Lists */
    QListWidget {{
        background-color: {colors['surface']};
        color: {colors['text']};
        border: {borders['width']}px solid {borders['color']};
        border-radius: {borders['radius']}px;
        font-family: {fonts['family']};
        font-size: {fonts['size']}px;
    }}
    
    QListWidget::item {{
        padding: {spacing['small']}px;
        border-bottom: 1px solid {borders['color']};
    }}
    
    QListWidget::item:selected {{
        background-color: {colors['primary']};
        color: white;
    }}
    
    QListWidget::item:hover {{
        background-color: {colors['light']};
    }}
    
    /* Progress Bars */
    QProgressBar {{
        background-color: {colors['surface']};
        border: {borders['width']}px solid {borders['color']};
        border-radius: {borders['radius']}px;
        text-align: center;
        color: {colors['text']};
        font-family: {fonts['family']};
        font-size: {fonts['size']}px;
    }}
    
    QProgressBar::chunk {{
        background-color: {colors['primary']};
        border-radius: {borders['radius']}px;
    }}
    
    /* Tabs */
    QTabWidget::pane {{
        border: {borders['width']}px solid {borders['color']};
        border-radius: {borders['radius']}px;
        background-color: {colors['background']};
    }}
    
    QTabBar::tab {{
        background-color: {colors['surface']};
        color: {colors['text']};
        border: {borders['width']}px solid {borders['color']};
        border-bottom: none;
        border-top-left-radius: {borders['radius']}px;
        border-top-right-radius: {borders['radius']}px;
        padding: {spacing['small']}px {spacing['medium']}px;
        font-family: {fonts['family']};
        font-size: {fonts['size']}px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {colors['background']};
        color: {colors['primary']};
    }}
    
    QTabBar::tab:hover {{
        background-color: {colors['light']};
    }}
    
    /* Status Bar */
    QStatusBar {{
        background-color: {colors['surface']};
        color: {colors['text']};
        border-top: {borders['width']}px solid {borders['color']};
        font-family: {fonts['family']};
        font-size: {fonts['size']}px;
    }}
    
    /* Menu Bar */
    QMenuBar {{
        background-color: {colors['surface']};
        color: {colors['text']};
        border-bottom: {borders['width']}px solid {borders['color']};
        font-family: {fonts['family']};
        font-size: {fonts['size']}px;
    }}
    
    QMenuBar::item {{
        padding: {spacing['small']}px {spacing['medium']}px;
    }}
    
    QMenuBar::item:selected {{
        background-color: {colors['primary']};
        color: white;
    }}
    
    /* Tool Tips */
    QToolTip {{
        background-color: {colors['dark']};
        color: white;
        border: {borders['width']}px solid {borders['color']};
        border-radius: {borders['radius']}px;
        padding: {spacing['small']}px;
        font-family: {fonts['family']};
        font-size: {fonts['size']}px;
    }}
    """
