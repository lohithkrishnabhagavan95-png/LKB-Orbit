"""Shared helpers: file categories, output paths, sizes, runtime config."""
from __future__ import annotations

import os
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp", ".gif", ".ico",
              ".heic", ".heif", ".avif"}
PDF_EXTS = {".pdf"}
DOCX_EXTS = {".docx", ".doc", ".odt", ".rtf"}
SHEET_EXTS = {".xlsx", ".xls", ".csv", ".tsv", ".ods"}
SLIDE_EXTS = {".pptx", ".ppt", ".odp"}
EBOOK_EXTS = {".epub"}
VECTOR_EXTS = {".svg"}
TEXT_EXTS = {".txt", ".md", ".log", ".json", ".xml", ".html", ".htm"}

APP_NAME = "LKB Orbit"

# Runtime options (plain values so worker threads can read them without Qt).
CONFIG = {
    "output": "next",      # "next" = beside original, "folder" = an APP_NAME subfolder
    "jpg_quality": 90,
    "pdf_dpi": 200,
    "trigger": "shift",    # shift | ctrl | alt
}


class UserError(Exception):
    """An error whose message is safe to show the user verbatim."""


def category(path: str | Path) -> str | None:
    ext = Path(path).suffix.lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in PDF_EXTS:
        return "pdf"
    if ext in DOCX_EXTS:
        return "docx"
    if ext in SHEET_EXTS:
        return "sheet"
    if ext in SLIDE_EXTS:
        return "slide"
    if ext in EBOOK_EXTS:
        return "ebook"
    if ext in VECTOR_EXTS:
        return "vector"
    if ext in TEXT_EXTS:
        return "text"
    return None


def resolve_shortcuts(paths: list[str]) -> list[str]:
    """A Windows .lnk (desktop shortcut) stands for the file it points to."""
    if os.name != "nt" or not any(str(p).lower().endswith(".lnk") for p in paths):
        return list(paths)
    out = []
    for p in paths:
        if str(p).lower().endswith(".lnk"):
            try:
                import win32com.client  # type: ignore
                tgt = win32com.client.Dispatch("WScript.Shell").CreateShortcut(str(p)).TargetPath
                if tgt and os.path.isfile(tgt):
                    p = tgt
            except Exception:
                pass
        out.append(p)
    return out


def unique_path(path: str | Path) -> Path:
    """`path`, or `name (1).ext`, `name (2).ext`, ... if it already exists."""
    p = Path(path)
    if not p.exists():
        return p
    i = 1
    while (cand := p.with_name(f"{p.stem} ({i}){p.suffix}")).exists():
        i += 1
    return cand


def output_dir(src: str | Path) -> Path:
    d = Path(src).parent
    if CONFIG.get("output") == "folder":
        d = d / APP_NAME
        d.mkdir(exist_ok=True)
    return d


def sibling(src: str | Path, label: str = "", ext: str | None = None) -> Path:
    """Output path next to `src`, never overwriting. sibling('a.jpg','Small','.png') -> 'a Small.png'."""
    base = output_dir(src) / Path(src).name
    stem = f"{base.stem} {label}".strip() if label else base.stem
    new_ext = ext if ext is not None else base.suffix
    if not new_ext.startswith("."):
        new_ext = "." + new_ext
    return unique_path(base.with_name(stem + new_ext))


def sibling_folder(src: str | Path, label: str = "") -> Path:
    """A new (unique) folder next to `src`, named after it — e.g. for the many
    images a multi-page PDF or deck produces, so the source folder stays tidy."""
    stem = Path(src).stem
    name = f"{stem} {label}".strip() if label else stem
    folder = unique_path(output_dir(src) / name)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def human_size(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


def file_size(path: str | Path) -> int:
    try:
        return os.path.getsize(path)
    except OSError:
        return 0
