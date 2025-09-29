from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QPushButton,
    QLineEdit,
    QTextEdit,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt


def create_logs_view(main_window):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(10, 10, 10, 10)

    # --- Filter Bar ---
    filter_bar = QHBoxLayout()
    filter_bar.addWidget(QLabel(main_window.tr("Filter by level:")))
    main_window.log_filter_info = QCheckBox(main_window.tr("Info"))
    main_window.log_filter_info.setChecked(True)
    main_window.log_filter_info.stateChanged.connect(main_window.refresh_log_display)
    main_window.log_filter_warning = QCheckBox(main_window.tr("Warning"))
    main_window.log_filter_warning.setChecked(True)
    main_window.log_filter_warning.stateChanged.connect(main_window.refresh_log_display)
    main_window.log_filter_error = QCheckBox(main_window.tr("Error"))
    main_window.log_filter_error.setChecked(True)
    main_window.log_filter_error.stateChanged.connect(main_window.refresh_log_display)
    main_window.log_filter_debug = QCheckBox(main_window.tr("Debug"))
    main_window.log_filter_debug.setChecked(False)  # Off by default
    main_window.log_filter_debug.stateChanged.connect(main_window.refresh_log_display)

    filter_bar.addWidget(main_window.log_filter_info)
    filter_bar.addWidget(main_window.log_filter_warning)
    filter_bar.addWidget(main_window.log_filter_error)
    filter_bar.addWidget(main_window.log_filter_debug)
    filter_bar.addStretch()

    clear_logs_button = QPushButton(
        QIcon(":/icons/trash-2.svg"), main_window.tr("Clear"))
    clear_logs_button.clicked.connect(main_window.clear_logs)
    filter_bar.addWidget(clear_logs_button)

    layout.addLayout(filter_bar)

    # --- Search Bar ---
    search_bar = QHBoxLayout()
    main_window.log_search_input = QLineEdit()
    main_window.log_search_input.setPlaceholderText(main_window.tr("Search logs..."))

    find_prev_button = QPushButton(QIcon(":/icons/arrow-up.svg"), "")
    find_prev_button.setFixedWidth(40)
    find_prev_button.clicked.connect(main_window.find_prev_log)

    find_next_button = QPushButton(QIcon(":/icons/arrow-down.svg"), "")
    find_next_button.setFixedWidth(40)
    find_next_button.clicked.connect(main_window.find_next_log)

    search_bar.addWidget(main_window.log_search_input)
    search_bar.addWidget(find_prev_button)
    search_bar.addWidget(find_next_button)

    layout.addLayout(search_bar)

    main_window.log_view = QTextEdit()
    main_window.log_view.setReadOnly(True)
    # Enable custom context menu
    main_window.log_view.setContextMenuPolicy(Qt.CustomContextMenu)
    main_window.log_view.customContextMenuRequested.connect(
        main_window.show_log_context_menu)
    layout.addWidget(main_window.log_view)
    return widget
