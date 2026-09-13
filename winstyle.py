"""
winstyle.py
-----------
Small platform-specific helper: asks Windows to draw the native title
bar in dark mode (DWMWA_USE_IMMERSIVE_DARK_MODE), so the app doesn't
have a bright white bar sitting above a dark-themed window.

This only affects Windows 10 (1809+) and Windows 11. On any other
platform, or if the call fails for any reason, it silently does
nothing — the app still runs fine with the OS's default title bar.

We keep the native title bar (rather than going fully borderless with
`overrideredirect`) because that would mean hand-building drag-to-move,
minimize, and close behavior — a lot of extra surface area for a small
utility. Recoloring the existing bar is a one-line-of-effect change
without added complexity.
"""

import sys


def apply_dark_titlebar(root):
    if sys.platform != "win32":
        return
    try:
        import ctypes

        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())

        # 20 is DWMWA_USE_IMMERSIVE_DARK_MODE on Windows 11 / late Windows
        # 10 builds; 19 was used on some earlier Windows 10 builds.
        for attribute in (20, 19):
            value = ctypes.c_int(1)
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)
            )
            if result == 0:  # S_OK
                break
    except Exception:
        pass
