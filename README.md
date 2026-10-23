<div align="center">

<img src="quickconvert/assets/logo.png" width="150" alt="LKB Orbit logo">

# LKB Orbit

**Convert any file on Windows — right from your desktop.**
Start dragging a file, hold **Shift**, and drop it on a slice. No websites, no uploads.

[![License: MIT](https://img.shields.io/badge/license-MIT-3b82f6.svg)](LICENSE)
![Platform](https://img.shields.io/badge/platform-Windows-0078D6.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB.svg)
![PRs welcome](https://img.shields.io/badge/PRs-welcome-22c55e.svg)

[**⬇ Download the app**](../../releases/latest) · [▶ Watch the demo](../../releases/latest) · [Report a bug](../../issues)

<img src="docs/preview.jpg" width="640" alt="LKB Orbit radial menu">

</div>

---

## What is it?

LKB Orbit is a free, open-source Windows utility that converts files locally. Instead of
hunting for an online converter and uploading your documents to a stranger's server, you
**start dragging any file and hold Shift** — a radial menu blooms under your cursor. Drop
the file on the format or tool you want. The result is saved **next to the original**, and
the original is never touched.

Tap **Shift** again while the menu is open to flip between **Convert** and **Tools**.

## Download

Grab the latest build from the [**Releases page**](../../releases/latest):

- **`LKB Orbit.exe`** — a single portable file. No install, no admin rights. Double-click and it lives in your system tray.

> On first launch Windows SmartScreen may warn because the app isn't code-signed yet.
> Click **More info → Run anyway**. The entire source is in this repo.

## How to use

1. Start dragging a file in File Explorer (or on the desktop).
2. Hold **Shift** — the menu opens under the cursor and a preview of the file pops into the center.
3. Drop the file on a slice. Done — with a tray notification.
4. Tap **Shift** again to switch **Convert ⇄ Tools**.

No drag? **Double-click the tray icon** to pick a file and click a slice instead, or turn on
the **right-click → Convert with LKB Orbit** entry from the tray menu.

## What it converts

| File | Convert to | Tools |
|------|-----------|-------|
| **Images** (PNG, JPG, WEBP, TIFF, BMP, GIF, ICO) | any of those, or PDF | Compress · Resize · several images → one PDF |
| **PDF** | JPG / PNG (per page), DOCX, TXT | Merge · Split (pick pages) · Rotate · Compress |
| **Word** (.docx, .doc, .odt, .rtf) | PDF, TXT | — |
| **Spreadsheets** (.xlsx, .xls, .csv, .tsv, .ods) | PDF, CSV, XLSX | — |
| **Presentations** (.pptx, .ppt, .odp) | PDF, PNG, TXT | Split (pick slides) |
| **Text** (.txt, .md, .json, .xml, .html…) | PDF, DOCX | — |

Highlights:

- **Everything is local** — no network calls, nothing is uploaded.
- **Originals are preserved** and outputs never overwrite existing files.
- **Multi-page jobs auto-folder** — converting a PDF or deck to images drops them in a folder named after the file.
- **Split by page/slide** — click exactly the pages or slides you want to pull out.
- Most conversions are **pure Python**. A few (`.doc/.odt/.rtf`, `.ods`, presentation → PDF/PNG)
  use **LibreOffice** if it's installed, and say so clearly if it isn't.
- Windows integration: **start with Windows** and an **Explorer right-click** entry, both toggled from the tray (no admin needed).

## Run from source

```bash
git clone https://github.com/lohithkrishnabhagavan95-png/LKB-Orbit.git
cd LKB-Orbit
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\pythonw run.py
```

Run the tests:

```bash
.venv\Scripts\pytest -q
```

## Build the standalone exe

```bash
.venv\Scripts\pip install pyinstaller
.venv\Scripts\pyinstaller "LKB Orbit.spec"
```

Output: `dist/LKB Orbit.exe`. Regenerate the logo/icons with `python tools/make_logo.py`.

## How it works

```
quickconvert/
  engine.py    all file processing (Pillow + PyMuPDF + python-docx + openpyxl + python-pptx). Pure & testable.
  render.py    self-contained .pptx → image renderer (no external software needed)
  trigger.py   the drag+Shift watcher (polls GetAsyncKeyState — no admin, no hooks)
  menu.py      the radial menu widget (drop-on-slice, two-ring toggle, pop-in preview)
  dialogs.py   the page/slide picker for Split
  integration.py  start-with-Windows + Explorer right-click (HKCU only)
  app.py       tray icon, background jobs, notifications, single-instance handoff
  util.py      file categories, output paths, config
  assets/      logo + app icon
run.py         entry point
tests/         engine round-trip tests
tools/         logo generator
```

- The **trigger** polls global input state (left button held + movement + Shift) — no admin rights and no fragile low-level hooks.
- The **engine** is UI-free, so every conversion is covered by a round-trip test in `tests/`.
- Jobs run on a background thread pool, so the menu stays responsive.

## Contributing

Contributions of any size are welcome — issues and pull requests both. A good PR:

- keeps `engine.py` UI-free and adds a round-trip test in `tests/` for any new conversion,
- runs `pytest -q` green, and
- matches the existing style (small, readable functions).

New conversions usually slot in as one more entry in `engine.TOOLS` (plus a small dialog for
options), so they're easy to add.

## License

[MIT](LICENSE) — free to use, modify, and distribute.

© 2026 Lohith Krishna Bhagavan and the LKB Orbit contributors.
