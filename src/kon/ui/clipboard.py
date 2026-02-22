import base64
import os
import shutil
import subprocess
import sys


def copy_to_clipboard(text: str) -> None:
    encoded = base64.b64encode(text.encode()).decode()
    print(f"\033]52;c;{encoded}\a", end="", flush=True)

    if sys.platform == "darwin":
        _try_run(["pbcopy"], text)
        return

    if sys.platform == "win32":
        _try_run(["clip"], text)
        return

    if os.environ.get("TERMUX_VERSION") and _try_run(["termux-clipboard-set"], text):
        return

    if _is_wayland_session():
        if _try_run(["wl-copy"], text):
            return
        if _try_run(["xclip", "-selection", "clipboard"], text):
            return
        _try_run(["xsel", "--clipboard", "--input"], text)
        return

    if _try_run(["xclip", "-selection", "clipboard"], text):
        return
    _try_run(["xsel", "--clipboard", "--input"], text)


def _is_wayland_session() -> bool:
    return (
        bool(os.environ.get("WAYLAND_DISPLAY")) or os.environ.get("XDG_SESSION_TYPE") == "wayland"
    )


def _try_run(command: list[str], text: str) -> bool:
    if shutil.which(command[0]) is None:
        return False

    try:
        subprocess.run(
            command,
            input=text,
            text=True,
            check=True,
            timeout=5,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return False

    return True
