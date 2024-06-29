from __future__ import annotations

import tkinter as tk

from rich.console import Console

from ctf_architect.chall_architect.terminal.create import create


console = Console()


def main() -> None:
    try:
        import ctypes

        # Set the DPI awareness to make the file dialog not blurry on Windows
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    # Hide the root window
    _root = tk.Tk()
    _root.withdraw()

    # This is to fix a bug on vscode's terminal where the filedialog window
    # will not show up as it is hidden behind it.
    _root.call("wm", "attributes", ".", "-topmost", True)

    try:
        create()
    except (KeyboardInterrupt, EOFError):
        console.print("[bright_red]Aborting...[/bright_red]")
        return
