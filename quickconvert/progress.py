"""A small frameless progress / result window shown during and after a conversion
— so there's real visible feedback, not just a tray tooltip."""
from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QProgressBar, QPushButton,
                               QVBoxLayout, QWidget)

_STYLE = """
QLabel#title { color: #eaf2ff; font: 600 16px 'Segoe UI'; }
QLabel#status { color: #9aa6c2; font: 13px 'Segoe UI'; }
QProgressBar { background: #232733; border: none; border-radius: 5px; height: 8px; }
QProgressBar::chunk { background: #3b82f6; border-radius: 5px; }
QPushButton { background: #2a2e39; color: #eaf2ff; border: 1px solid #3a3f4c;
              border-radius: 8px; padding: 7px 14px; font: 13px 'Segoe UI'; }
QPushButton:hover { border-color: #3b82f6; }
QPushButton#primary { background: #2563eb; border-color: #2563eb; color: white; }
"""


class ProgressWindow(QWidget):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(_STYLE)
        self.resize(460, 172)
        self._outputs: list[str] = []
        self._close_timer = QTimer(self, singleShot=True, timeout=self.hide)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)
        self.title = QLabel("", objectName="title")
        self.status = QLabel("", objectName="status")
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        root.addWidget(self.title)
        root.addWidget(self.bar)
        root.addWidget(self.status)
        self.btns = QHBoxLayout()
        self.btns.addStretch(1)
        self.b_open = QPushButton("Open file", objectName="primary")
        self.b_show = QPushButton("Open folder")
        self.b_close = QPushButton("Close")
        self.b_open.clicked.connect(self._open)
        self.b_show.clicked.connect(self._show)
        self.b_close.clicked.connect(self.hide)
        for b in (self.b_open, self.b_show, self.b_close):
            self.btns.addWidget(b)
        root.addLayout(self.btns)

    # ---- lifecycle ----
    def start(self, op: str, name: str):
        self._close_timer.stop()
        self.title.setText(f"{op}")
        self.status.setText(name)
        self.bar.setRange(0, 0)            # indeterminate
        self._set_buttons(False)
        self._center()
        self.show()
        self.raise_()

    def finish(self, outputs: list[str]):
        self._outputs = outputs
        self.bar.setRange(0, 1)
        self.bar.setValue(1)
        if not outputs:
            self.hide()
            return
        n = len(outputs)
        name = os.path.basename(outputs[0]) + (f"  +{n - 1} more" if n > 1 else "")
        self.title.setText("Done")
        self.status.setText(name)
        self._set_buttons(True)
        self.b_open.setVisible(n == 1)     # for many files, just offer the folder
        self.raise_()
        self._close_timer.start(6000)

    def fail(self, msg: str):
        self.bar.setRange(0, 1)
        self.bar.setValue(0)
        self.title.setText("Couldn't convert")
        self.status.setText(msg)
        self.b_open.setVisible(False)
        self.b_show.setVisible(False)
        self.b_close.setVisible(True)
        self.raise_()
        self._close_timer.start(8000)

    # ---- helpers ----
    def _set_buttons(self, show: bool):
        for b in (self.b_open, self.b_show, self.b_close):
            b.setVisible(show)

    def _open(self):
        if self._outputs and sys.platform == "win32":
            try:
                os.startfile(self._outputs[0])  # noqa: S606
            except OSError:
                pass

    def _show(self):
        if not self._outputs:
            return
        p = os.path.normpath(self._outputs[0])
        if sys.platform == "win32":
            subprocess.run(["explorer", "/select,", p])
        else:
            subprocess.run(["xdg-open", os.path.dirname(p)])

    def _center(self):
        scr = self.screen().availableGeometry() if self.screen() else None
        if scr:
            self.move(scr.center().x() - self.width() // 2, scr.center().y() - self.height() // 2)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 18, 18)
        p.fillPath(path, QColor(27, 29, 34, 245))
        p.setPen(QColor(255, 255, 255, 20))
        p.drawPath(path)
