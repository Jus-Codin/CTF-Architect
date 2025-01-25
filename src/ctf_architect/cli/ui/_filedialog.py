from __future__ import annotations

import sys
from typing import Literal

from ctf_architect.cli.ui.console import console

_tkinter_available = False


def _handle_unavailable_tkinter(*_, **__) -> Literal[""]:
    console.print(
        "Your system is unable to use the file dialog. Please provide the path manually.",
        style="ctfa.error",
    )
    return ""


try:
    from tkinter.filedialog import askdirectory, askopenfilename, askopenfilenames

    _tkinter_available = True
except ImportError:
    askdirectory = askopenfilename = askopenfilenames = _handle_unavailable_tkinter

if _tkinter_available:
    if sys.platform.startswith("win"):
        # Set DPI awareness to make the file dialog not blurry on Windows
        try:
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    import tkinter as tk

    # Force the window to be on top
    _root = tk.Tk()
    _root.withdraw()

    _root.attributes("-topmost", True)


__all__ = ["askdirectory", "askopenfilename", "askopenfilenames"]
