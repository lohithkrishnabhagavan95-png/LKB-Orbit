"""Detects "left button held + mouse moved + trigger key down" anywhere on screen
— what a Shift+drag of a file looks like. Polling global input state needs no admin
rights and can't wedge the system the way a broken low-level hook can (Windows only
for now; GetAsyncKeyState)."""
from __future__ import annotations

import ctypes
import sys

from PySide6.QtCore import QObject, QPoint, QTimer, Signal
from PySide6.QtGui import QCursor

VK = {"lbutton": 0x01, "shift": 0x10, "ctrl": 0x11, "alt": 0x12, "escape": 0x1B}
DRAG_THRESHOLD = 10   # px travelled with the button held before we treat it as a drag
NO_DRAG_TIMEOUT = 50  # ticks (~0.75s) to wait for a drag to arrive before hiding again


class DragWatcher(QObject):
    show_menu = Signal(QPoint)
    toggle_ring = Signal()
    hide_menu = Signal()

    def __init__(self, menu_visible, menu_got_drag, menu_click_mode=lambda: False, parent=None):
        super().__init__(parent)
        self.menu_visible = menu_visible
        self.menu_got_drag = menu_got_drag
        self.menu_click_mode = menu_click_mode
        self.enabled = sys.platform == "win32"
        self.vk = VK["shift"]
        self._down_at: QPoint | None = None
        self._key_was = False
        self._fired = False
        self._idle = 0
        self._shown_at = QPoint()
        self._u32 = ctypes.windll.user32 if sys.platform == "win32" else None
        self.timer = QTimer(self, interval=15, timeout=self._tick)

    def set_key(self, name: str):
        self.vk = VK.get(name, VK["shift"])

    def start(self):
        if self._u32 is not None:
            self.timer.start()

    def _down(self, vk: int) -> bool:
        return bool(self._u32.GetAsyncKeyState(vk) & 0x8000)

    def _tick(self):
        lbtn = self._down(VK["lbutton"])
        key = self._down(self.vk)
        esc = self._down(VK["escape"])
        pos = QCursor.pos()

        if self.menu_visible():
            # A tray-opened (click-mode) menu manages its own lifecycle (click or
            # Escape). Only drag-opened menus are driven by the mouse button here.
            if self.menu_click_mode():
                self._key_was = key
                return
            if not lbtn or esc:
                QTimer.singleShot(120, self.hide_menu.emit)  # let the drop land first
            elif key and not self._key_was and self.menu_got_drag():
                self.toggle_ring.emit()  # tap the key again to flip Convert <-> Tools
            elif not self.menu_got_drag() and (pos - self._shown_at).manhattanLength() > 6:
                self._idle += 1
                if self._idle > NO_DRAG_TIMEOUT:
                    self.hide_menu.emit()
        elif lbtn:
            if self._down_at is None:
                self._down_at, self._fired = pos, False
            moved = (pos - self._down_at).manhattanLength() >= DRAG_THRESHOLD
            if self.enabled and moved and key and not self._fired:
                self._fired = True
                self._idle = 0
                self._shown_at = pos
                self.show_menu.emit(pos)
        else:
            self._down_at, self._fired = None, False
        self._key_was = key
