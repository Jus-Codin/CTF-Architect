from __future__ import annotations

import os
import sys


def _posixify(name: str) -> str:
    return "-".join(name.split()).lower()


def get_app_dir(app_name: str, roaming: bool = True, force_posix: bool = False) -> str:
    """Get the config folder for the application.

    Based on https://github.com/pallets/click/blob/8a47580a00f3404e7071b9ecfec3692a1e18309f/src/click/utils.py#L449

    Args:
        app_name (str): The name of the application. This should be properly capitalized and can contain whitespace.
        roaming (bool): Specifies whether the folder should be in the roaming directory on Windows.
        force_posix (bool): Specifies whether the path should be stored in the home directory with a leading dot on POSIX systems.

    Returns:
        str: The path to the config folder.
    """
    if sys.platform.startswith("win"):
        key = "APPDATA" if roaming else "LOCALAPPDATA"
        folder = os.environ.get(key)
        if folder is None:
            folder = os.path.expanduser("~")
        return os.path.join(folder, app_name)
    if force_posix:
        return os.path.join(os.path.expanduser(f"~/.{_posixify(app_name)}"))
    if sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~/Library/Application Support"), app_name)
    return os.path.join(
        os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
        _posixify(app_name),
    )
