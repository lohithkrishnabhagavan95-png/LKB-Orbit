"""Self-contained PowerPoint (.pptx) renderer: draws each slide — text, pictures
and solid shapes — to a Pillow image, with no external software. Not pixel-perfect
versus PowerPoint (charts/SmartArt/effects are approximated or skipped), but it
always works offline and handles any number of slides. LibreOffice, when installed,
is used instead for higher fidelity (see engine.py)."""
from __future__ import annotations

import io
import os
from functools import lru_cache

EMU_PER_INCH = 914400
_FONT_DIR = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")


@lru_cache(maxsize=256)
def _font(size: int, bold: bool, italic: bool):
    from PIL import ImageFont
    if bold and italic:
        names = ["arialbi.ttf", "seguisbi.ttf", "segoeuiz.ttf"]
    elif bold:
        names = ["arialbd.ttf", "segoeuib.ttf"]
    elif italic:
        names = ["ariali.ttf", "segoeuii.ttf"]
    else:
        names = ["arial.ttf", "segoeui.ttf", "calibri.ttf"]
    for n in names:
        p = os.path.join(_FONT_DIR, n)
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                pass
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _rgb(color_str) -> tuple[int, int, int]:
    h = str(color_str)
    try:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except (ValueError, IndexError):
        return 20, 20, 20


def _wrap(text: str, font, max_w: float) -> list[str]:
    out: list[str] = []
    for raw in text.split("\n"):
        words = raw.split()
        if not words:
            out.append("")
            continue
        cur = words[0]
        for w in words[1:]:
            if font.getlength(cur + " " + w) <= max_w:
                cur += " " + w
            else:
                out.append(cur)
                cur = w
        out.append(cur)
    return out


def _para_props(para):
    sizes = [r.font.size.pt for r in para.runs if r.font.size is not None]
    size = max(sizes) if sizes else (para.font.size.pt if para.font.size is not None else 18)
    bold = any(r.font.bold for r in para.runs) or bool(para.font.bold)
    italic = any(r.font.italic for r in para.runs) or bool(para.font.italic)
    color = (20, 20, 20)
    for r in para.runs:
        try:
            if r.font.color and r.font.color.type is not None and r.font.color.rgb is not None:
                color = _rgb(r.font.color.rgb)
                break
        except Exception:
            pass
    return float(size), bold, italic, color


def _draw_text_frame(shape, draw, scale: float, dpi: int):
    from pptx.enum.text import PP_ALIGN
    x0 = int((shape.left or 0) * scale) + 5
    y = int((shape.top or 0) * scale) + 5
    bw = max(20, int((shape.width or 0) * scale) - 10)
    y_max = int(((shape.top or 0) + (shape.height or 0)) * scale)
    for para in shape.text_frame.paragraphs:
        text = "".join(r.text for r in para.runs) or (para.text or "")
        size_pt, bold, italic, color = _para_props(para)
        fpx = max(8, int(round(size_pt * dpi / 72)))
        font = _font(fpx, bool(bold), bool(italic))
        line_h = int(fpx * 1.3)
        if not text.strip():
            y += line_h
            continue
        for line in _wrap(text, font, bw):
            if y > y_max + line_h:
                return
            lw = font.getlength(line)
            if para.alignment == PP_ALIGN.CENTER:
                lx = x0 + (bw - lw) / 2
            elif para.alignment == PP_ALIGN.RIGHT:
                lx = x0 + bw - lw
            else:
                lx = x0
            draw.text((lx, y), line, fill=color, font=font)
            y += line_h


def _draw_shape(shape, im, draw, scale: float, dpi: int):
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    try:
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            for sub in shape.shapes:
                _draw_shape(sub, im, draw, scale, dpi)
            return
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
            from PIL import Image
            pic = Image.open(io.BytesIO(shape.image.blob)).convert("RGBA")
            w = max(1, int((shape.width or 0) * scale))
            h = max(1, int((shape.height or 0) * scale))
            pic = pic.resize((w, h), Image.LANCZOS)
            im.paste(pic, (int((shape.left or 0) * scale), int((shape.top or 0) * scale)), pic)
            return
        # solid-filled autoshape -> a colour block behind any text (z-order preserved)
        try:
            from pptx.enum.dml import MSO_FILL
            if shape.fill.type == MSO_FILL.SOLID and shape.fill.fore_color.rgb is not None:
                x0 = int((shape.left or 0) * scale)
                y0 = int((shape.top or 0) * scale)
                x1 = x0 + int((shape.width or 0) * scale)
                y1 = y0 + int((shape.height or 0) * scale)
                draw.rectangle([x0, y0, x1, y1], fill=_rgb(shape.fill.fore_color.rgb))
        except Exception:
            pass
        if shape.has_text_frame:
            _draw_text_frame(shape, draw, scale, dpi)
    except Exception:
        pass  # one bad shape must never break the whole slide


def _open_presentation(src):
    """Open a .pptx robustly, with a precise reason when it can't be read. Copies to a
    local temp first so a OneDrive/cloud placeholder gets downloaded and a locked file is
    snapshotted; falls back to the original path."""
    import shutil
    import tempfile
    from pptx import Presentation
    from .util import UserError

    # Diagnose from the file header so the user gets an actionable message.
    try:
        with open(src, "rb") as f:
            head = f.read(8)
    except OSError:
        raise UserError("Couldn't read this file. If it's on OneDrive/cloud, right-click it "
                        "→ 'Always keep on this device', then try again.")
    if len(head) < 4:
        raise UserError("This file is empty or still downloading from the cloud. Wait for it "
                        "to finish (or right-click → 'Always keep on this device').")
    if head[:4] == b"\xd0\xcf\x11\xe0":
        raise UserError("This looks password-protected or is an old .ppt. Remove the password "
                        "and save as .pptx, or install LibreOffice.")
    if head[:4] != b"PK\x03\x04":
        raise UserError("This isn't a valid PowerPoint file (it may be corrupted or renamed).")

    try:
        return Presentation(str(src)), None
    except Exception:
        pass
    td = tempfile.mkdtemp()
    local = os.path.join(td, "deck.pptx")
    try:
        shutil.copy2(str(src), local)   # reading the bytes hydrates a cloud placeholder
        return Presentation(local), td
    except Exception:
        shutil.rmtree(td, ignore_errors=True)
        raise


def pptx_to_images(src, dpi: int = 150) -> list:
    """Render every slide of a .pptx to a list of RGB Pillow images."""
    import shutil
    from PIL import Image, ImageDraw
    prs, td = _open_presentation(src)
    scale = dpi / EMU_PER_INCH
    sw = int(prs.slide_width or 9144000)
    sh = int(prs.slide_height or 6858000)
    w = max(1, round(sw * scale))
    h = max(1, round(sh * scale))
    from . import engine
    slides = list(prs.slides)
    total = len(slides)
    images = []
    for i, slide in enumerate(slides):
        im = Image.new("RGB", (w, h), "white")
        draw = ImageDraw.Draw(im)
        for shape in slide.shapes:
            _draw_shape(shape, im, draw, scale, dpi)
        images.append(im)
        engine._report(i + 1, total)
    if td:
        shutil.rmtree(td, ignore_errors=True)
    return images
