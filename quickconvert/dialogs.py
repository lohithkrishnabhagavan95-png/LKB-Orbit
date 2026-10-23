"""Small dialogs shown on the UI thread before a tool runs."""
from __future__ import annotations

from PySide6.QtWidgets import (QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

_STYLE = """
QDialog { background: #1b1d22; }
QLabel { color: #e8eaed; font: 13px 'Segoe UI'; }
QPushButton { background: #2a2d34; color: #e8eaed; border: 1px solid #3a3e46;
              border-radius: 7px; padding: 6px 12px; font: 12px 'Segoe UI'; }
QPushButton:hover { border-color: #3b82f6; }
QPushButton:checked { background: #2563eb; border-color: #2563eb; color: white; }
QPushButton#primary { background: #2563eb; border-color: #2563eb; color: white; }
QScrollArea { border: none; }
"""


class PagePicker(QDialog):
    """A grid of numbered buttons — the user clicks the pages/slides to separate."""

    def __init__(self, count: int, title: str = "Choose pages", unit: str = "page", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setStyleSheet(_STYLE)
        self._buttons: list[QPushButton] = []

        v = QVBoxLayout(self)
        v.addWidget(QLabel(f"Click the {unit} numbers to separate  ·  {count} total"))

        area = QScrollArea()
        area.setWidgetResizable(True)
        host = QWidget()
        grid = QGridLayout(host)
        grid.setSpacing(6)
        cols = 8
        for i in range(count):
            b = QPushButton(str(i + 1))
            b.setCheckable(True)
            b.setFixedSize(44, 34)
            grid.addWidget(b, i // cols, i % cols)
            self._buttons.append(b)
        area.setWidget(host)
        rows = (count + cols - 1) // cols
        area.setMinimumHeight(min(320, 50 + rows * 40))
        v.addWidget(area)

        row = QHBoxLayout()
        all_b = QPushButton("Select all")
        all_b.clicked.connect(lambda: [b.setChecked(True) for b in self._buttons])
        clear_b = QPushButton("Clear")
        clear_b.clicked.connect(lambda: [b.setChecked(False) for b in self._buttons])
        row.addWidget(all_b)
        row.addWidget(clear_b)
        row.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Separate")
        ok.setObjectName("primary")
        ok.setDefault(True)
        ok.clicked.connect(self.accept)
        row.addWidget(cancel)
        row.addWidget(ok)
        v.addLayout(row)
        self.resize(430, 380)

    def selected(self) -> list[int]:
        return [i + 1 for i, b in enumerate(self._buttons) if b.isChecked()]
