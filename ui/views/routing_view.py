from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QHeaderView,
)
from PySide6.QtCore import Qt


def create_routing_view(main_window):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(20, 20, 20, 20)

    top_layout = QHBoxLayout()
    top_layout.addWidget(QLabel(main_window.tr("Custom Routing Rules"),
                         styleSheet="font-size: 14pt; font-weight: bold;"))
    top_layout.addStretch()
    add_rule_button = QPushButton(main_window.tr("Add Rule"))
    add_rule_button.clicked.connect(main_window.show_rule_dialog)
    top_layout.addWidget(add_rule_button)
    layout.addLayout(top_layout)

    main_window.routing_table = QTableWidget()
    main_window.routing_table.setColumnCount(4)
    main_window.routing_table.setHorizontalHeaderLabels(
        [main_window.tr("Type"), main_window.tr("Value"), main_window.tr("Action"), main_window.tr("Actions")])

    # Enable sorting by clicking on headers
    main_window.routing_table.setSortingEnabled(True)
    # Set initial sort order (e.g., by Type, ascending)
    main_window.routing_table.sortByColumn(0, Qt.AscendingOrder)

    header = main_window.routing_table.horizontalHeader()
    # Stretch the 'Value' column
    header.setSectionResizeMode(1, QHeaderView.Stretch)
    # Adjust 'Actions' column to content
    header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

    main_window.routing_table.setEditTriggers(
        QTableWidget.NoEditTriggers)  # Disable direct editing
    main_window.routing_table.setSelectionBehavior(QTableWidget.SelectRows)
    layout.addWidget(main_window.routing_table)

    # Initial population of the table
    main_window.update_routing_table()

    return widget
