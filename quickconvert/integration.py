"""Windows integration: start at login and an Explorer right-click entry.
Everything lives under HKEY_CURRENT_USER, so no administrator rights are needed."""
from __future__ import annotations

import os
import sys

APP = "LKB Orbit"
_RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"
_SHELL = r"Software\Classes\*\shell\LKB Orbit"


def available() -> bool:
    return sys.platform == "win32"


def _launch_cmd(with_arg: bool) -> str:
    """How Windows should start the app (frozen exe, or pythonw + run.py in dev)."""
    if getattr(sys, "frozen", False):
        cmd = f'"{sys.executable}"'
    else:
        pyw = sys.executable
        if pyw.lower().endswith("python.exe"):
            cand = pyw[:-len("python.exe")] + "pythonw.exe"
            if os.path.exists(cand):
                pyw = cand
        run = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "run.py")
        cmd = f'"{pyw}" "{run}"'
    return cmd + (' "%1"' if with_arg else "")


def _icon() -> str:
    if getattr(sys, "frozen", False):
        return sys.executable  # the exe embeds the icon
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.ico")


# ---------------------------------------------------------------- start at login
def is_startup() -> bool:
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN) as k:
            winreg.QueryValueEx(k, APP)
            return True
    except FileNotFoundError:
        return False


def set_startup(enabled: bool) -> None:
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _RUN) as k:
        if enabled:
            winreg.SetValueEx(k, APP, 0, winreg.REG_SZ, _launch_cmd(False))
        else:
            try:
                winreg.DeleteValue(k, APP)
            except FileNotFoundError:
                pass


# ---------------------------------------------------------------- right-click entry
def has_context() -> bool:
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _SHELL + r"\command"):
            return True
    except FileNotFoundError:
        return False


def set_context(enabled: bool) -> None:
    import winreg
    if enabled:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _SHELL) as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, f"Convert with {APP}")
            winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, _icon())
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _SHELL + r"\command") as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, _launch_cmd(True))
    else:
        for sub in (_SHELL + r"\command", _SHELL):
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, sub)
            except FileNotFoundError:
                pass
