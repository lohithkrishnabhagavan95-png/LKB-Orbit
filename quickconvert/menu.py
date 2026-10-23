"""The radial menu: a frameless always-on-top ring of slices under the cursor.
Drop a file on a slice (drag mode) or click one (tray mode) to run that action.
Tap the trigger key again to flip between the Convert and Tools rings."""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from . import engine
from .util import category

SIZE = 320
R_OUT = 150
R_IN = 58


def _local_paths(mime) -> list[str]:
    out = []
    for u in mime.urls():
        p = u.toLocalFile()
        if p:
            out.append(p)
    return out


class RadialMenu(QWidget):
    action_chosen = Signal(str, str, str, list)  # cat, ring, label, paths

    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAcceptDrops(True)
        self.resize(SIZE, SIZE)
        self.paths: list[str] = []
        self.cat: str | None = None
        self.ring = "convert"
        self.rings: dict[str, list[str]] = {"convert": [], "tools": []}
        self.hover = -1
        self.got_drag = False
        self.click_mode = False
        self.preview: QPixmap | None = None
        self._pscale = 1.0          # spring-in scale of the preview (0..~1.1..1)
        self._pt = 1.0
        self._panim = QTimer(self, interval=16, timeout=self._pstep)
        self._can_dismiss = False

    # ------------------------------------------------------------ lifecycle
    def popup(self, global_pos, paths: list[str] | None = None):
        self.paths = list(paths) if paths else []
        self.cat = None
        self.ring = "convert"
        self.hover = -1
        self.got_drag = bool(paths)
        self.click_mode = paths is not None
        if self.paths:
            self._build()
        c = self.rect().center()
        self.move(global_pos.x() - c.x(), global_pos.y() - c.y())
        self._clamp_to_screen()
        self.show()
        self.raise_()
        self.activateWindow()
        if self.click_mode:   # allow click-away dismissal shortly after it settles
            self._can_dismiss = False
            QTimer.singleShot(350, lambda: setattr(self, "_can_dismiss", True))

    def focusOutEvent(self, e):
        if self.click_mode and self._can_dismiss:
            self.hide()
        super().focusOutEvent(e)

    def _clamp_to_screen(self):
        scr = self.screen().availableGeometry() if self.screen() else None
        if not scr:
            return
        g = self.frameGeometry()
        x = min(max(g.x(), scr.left()), scr.right() - g.width())
        y = min(max(g.y(), scr.top()), scr.bottom() - g.height())
        self.move(x, y)

    def _build(self):
        if not self.paths:
            return
        self.cat = category(self.paths[0])
        if self.cat is None:
            self.rings = {"convert": [], "tools": []}
        else:
            ext = self.paths[0].rsplit(".", 1)[-1] if "." in self.paths[0] else ""
            self.rings = engine.actions_for(self.cat, ext, len(self.paths))
        # start on whichever ring has slices
        if not self.rings.get("convert") and self.rings.get("tools"):
            self.ring = "tools"
        self.preview = self._make_preview(self.paths[0])
        self._pt = 0.0            # trigger the pop-in animation
        self._pscale = 0.0
        self._panim.start()
        self.update()

    # ------------------------------------------------------------ preview + animation
    def _pstep(self):
        self._pt = min(1.0, self._pt + 0.09)
        c1, c3 = 1.70158, 2.70158           # ease-out-back (slight overshoot = a "pop")
        t = self._pt - 1.0
        self._pscale = 1 + c3 * t ** 3 + c1 * t ** 2
        if self._pt >= 1.0:
            self._pscale = 1.0
            self._panim.stop()
        self.update()

    def _make_preview(self, path: str) -> QPixmap | None:
        ext = path.rsplit(".", 1)[-1].upper() if "." in path else "FILE"
        try:
            if self.cat == "image":
                from PIL import Image, ImageOps
                im = Image.open(path)
                im.seek(0)
                im = ImageOps.exif_transpose(im).convert("RGBA")
                return self._pil_to_pixmap(ImageOps.fit(im, (240, 240), Image.LANCZOS))
            if self.cat == "pdf":
                import pymupdf as fitz
                from PIL import Image, ImageOps
                doc = fitz.open(path)
                pix = doc[0].get_pixmap(dpi=48, alpha=False)
                page = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                doc.close()
                page = ImageOps.contain(page, (236, 236), Image.LANCZOS)
                sq = Image.new("RGBA", (240, 240), (255, 255, 255, 255))
                sq.paste(page, ((240 - page.width) // 2, (240 - page.height) // 2))
                return self._pil_to_pixmap(sq)
        except Exception:
            pass
        return self._badge_pixmap(ext)

    @staticmethod
    def _pil_to_pixmap(im) -> QPixmap:
        im = im.convert("RGBA")
        qimg = QImage(im.tobytes("raw", "RGBA"), im.width, im.height, QImage.Format_RGBA8888).copy()
        return QPixmap.fromImage(qimg)

    def _badge_pixmap(self, text: str) -> QPixmap:
        pm = QPixmap(240, 240)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 235))
        p.drawRoundedRect(QRectF(34, 54, 172, 132), 14, 14)
        p.setPen(QColor(37, 99, 235))
        p.setFont(QFont("Segoe UI", 34, QFont.Bold))
        p.drawText(pm.rect(), Qt.AlignCenter, text[:5])
        p.end()
        return pm

    def toggle(self):
        other = "tools" if self.ring == "convert" else "convert"
        if self.rings.get(other):
            self.ring = other
            self.hover = -1
            self.update()

    def current(self) -> list[str]:
        return self.rings.get(self.ring, [])

    # ------------------------------------------------------------ geometry
    def _span(self) -> float:
        n = max(1, len(self.current()))
        return 360.0 / n

    def hit(self, pos: QPointF) -> int:
        c = QPointF(self.width() / 2, self.height() / 2)
        dx, dy = pos.x() - c.x(), c.y() - pos.y()   # dy flipped: screen y grows downward
        r = math.hypot(dx, dy)
        if r < R_IN or r > R_OUT:
            return -1
        n = len(self.current())
        if n == 0:
            return -1
        ang = (math.degrees(math.atan2(dy, dx)) - 90) % 360   # 0 at top, clockwise slices
        return min(n - 1, int(ang / self._span()))

    def _slice_path(self, i: int) -> QPainterPath:
        c = QPointF(self.width() / 2, self.height() / 2)
        span = self._span()
        a0 = 90 + i * span
        outer = QRectF(c.x() - R_OUT, c.y() - R_OUT, 2 * R_OUT, 2 * R_OUT)
        inner = QRectF(c.x() - R_IN, c.y() - R_IN, 2 * R_IN, 2 * R_IN)
        path = QPainterPath()
        path.arcMoveTo(outer, a0)
        path.arcTo(outer, a0, span)
        path.arcTo(inner, a0 + span, -span)
        path.closeSubpath()
        return path

    def _label_point(self, i: int, r: float) -> QPointF:
        c = QPointF(self.width() / 2, self.height() / 2)
        mid = math.radians(90 + (i + 0.5) * self._span())
        return QPointF(c.x() + r * math.cos(mid), c.y() - r * math.sin(mid))

    # ------------------------------------------------------------ drag & drop
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            if not self.paths:
                self.paths = _local_paths(e.mimeData())
                self.got_drag = True
                self._build()
            e.acceptProposedAction()

    def dragMoveEvent(self, e):
        self.hover = self.hit(e.position())
        self.update()
        e.acceptProposedAction()

    def dragLeaveEvent(self, e):
        self.hover = -1
        self.update()

    def dropEvent(self, e):
        if not self.paths:
            self.paths = _local_paths(e.mimeData())
            self._build()
        i = self.hit(e.position())
        self._fire(i)
        e.acceptProposedAction()

    # ------------------------------------------------------------ click mode
    def mouseMoveEvent(self, e):
        if self.click_mode:
            self.hover = self.hit(e.position())
            self.update()

    def mouseReleaseEvent(self, e):
        if self.click_mode:
            self._fire(self.hit(e.position()))

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.hide()
        elif e.key() in (Qt.Key_Tab, Qt.Key_Space):
            self.toggle()

    def _fire(self, i: int):
        slices = self.current()
        if 0 <= i < len(slices) and self.cat:
            self.action_chosen.emit(self.cat, self.ring, slices[i], list(self.paths))
        self.hide()

    # ------------------------------------------------------------ painting
    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = QPointF(self.width() / 2, self.height() / 2)
        dark = self.palette().window().color().value() < 128
        fg = QColor(235, 238, 245) if dark else QColor(28, 30, 36)
        base = QColor(34, 37, 44, 235) if dark else QColor(255, 255, 255, 240)
        accent = QColor(59, 130, 246)

        slices = self.current()
        if not slices:
            self._hub(p, c, fg, accent)
            msg = "Drop a file" if not self.paths else f"No actions for .{self.cat or '?'}"
            p.setPen(fg)
            p.setFont(QFont("Segoe UI", 10))
            p.drawText(self.rect(), Qt.AlignCenter, msg)
            return

        for i, label in enumerate(slices):
            path = self._slice_path(i)
            p.setPen(QPen(QColor(0, 0, 0, 40), 1))
            p.fillPath(path, accent if i == self.hover else base)
            p.drawPath(path)
            pt = self._label_point(i, (R_IN + R_OUT) / 2)
            p.setPen(QColor(255, 255, 255) if i == self.hover else fg)
            p.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
            p.drawText(QRectF(pt.x() - 44, pt.y() - 12, 88, 24), Qt.AlignCenter, label)

        self._hub(p, c, fg, accent)

    def _hub(self, p: QPainter, c: QPointF, fg: QColor, accent: QColor):
        rin = R_IN - 6
        p.setPen(Qt.NoPen)
        p.setBrush(accent)
        p.drawEllipse(c, rin, rin)

        if self.preview and not self.preview.isNull() and self.paths:
            s = max(0.02, self._pscale)
            rr = rin * s
            clip = QPainterPath()
            clip.addEllipse(c, rr, rr)
            p.save()
            p.setClipPath(clip)
            p.setOpacity(min(1.0, self._pt * 1.4))
            p.drawPixmap(QRectF(c.x() - rr, c.y() - rr, 2 * rr, 2 * rr),
                         self.preview, QRectF(self.preview.rect()))
            p.restore()
            p.setPen(QPen(QColor(255, 255, 255, 235), 2))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(c, rr, rr)
            if len(self.paths) > 1:  # badge for multi-select
                p.setPen(QColor(255, 255, 255))
                p.setFont(QFont("Segoe UI", 9, QFont.Bold))
                p.drawText(QRectF(c.x() - rin, c.y() + rin - 20, 2 * rin, 18),
                           Qt.AlignCenter, f"{len(self.paths)} files")
        else:
            p.setPen(QColor(255, 255, 255))
            p.setFont(QFont("Segoe UI", 9, QFont.Bold))
            p.drawText(QRectF(c.x() - rin, c.y() - 9, 2 * rin, 18),
                       Qt.AlignCenter, self.ring.capitalize())

        # small mode pill under the hub so Convert/Tools stays visible over the preview
        pill_w, pill_h = 86, 22
        pr = QRectF(c.x() - pill_w / 2, c.y() + rin - 6, pill_w, pill_h)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(20, 22, 28, 200))
        p.drawRoundedRect(pr, 11, 11)
        p.setPen(QColor(255, 255, 255))
        p.setFont(QFont("Segoe UI", 9, QFont.DemiBold))
        p.drawText(pr, Qt.AlignCenter, self.ring.capitalize())
