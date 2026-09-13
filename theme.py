"""
theme.py
--------
Centralized color palette, fonts, and small drawing helpers used to build
the custom dark-themed widgets (rounded buttons, rounded input boxes,
status dot, etc.) on top of plain Tkinter Canvas primitives.

Keeping this separate from gui.py means the visual language (colors,
radii, fonts) can be tweaked in one place without touching layout logic.
"""

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
BG = "#0b0b0d"            # app background (near-black)
PANEL = "#161619"         # panel / card background (dark charcoal)
PANEL_BORDER = "#26262b"  # subtle 1px borders on panels/inputs
INPUT_BG = "#1e1e22"      # input box fill
INPUT_BG_FOCUS = "#232328"

TEXT_PRIMARY = "#f2f2f5"
TEXT_SECONDARY = "#8b8b93"
TEXT_MUTED = "#5b5b63"

ACCENT = "#7c5cff"        # electric violet — brand accent
ACCENT_HOVER = "#8f73ff"
ACCENT_PRESSED = "#6a4de8"

DANGER = "#ff5c6c"        # used for the "STOP" state
DANGER_HOVER = "#ff727f"
DANGER_PRESSED = "#e6505f"

STATUS_RUNNING = "#3ddc84"
STATUS_STOPPED = "#5b5b63"

LINE_DEFAULT = "#2c2c31"   # underline color for minimal inputs, idle
LINE_FOCUS = ACCENT        # underline color for minimal inputs, focused

# ---------------------------------------------------------------------------
# Fonts (family, size, weight) — fall back gracefully if unavailable.
# ---------------------------------------------------------------------------
FONT_TITLE = ("Segoe UI Semibold", 20)
FONT_TITLE_FALLBACK = ("Segoe UI", 20, "bold")
FONT_LABEL = ("Segoe UI", 9)
FONT_INPUT = ("Segoe UI", 13)
FONT_BUTTON = ("Segoe UI Semibold", 12)
FONT_BUTTON_FALLBACK = ("Segoe UI", 12, "bold")
FONT_STATUS = ("Segoe UI Semibold", 10)
FONT_STATUS_FALLBACK = ("Segoe UI", 10, "bold")
FONT_MONO_SMALL = ("Consolas", 9)


def rounded_rect_points(x1, y1, x2, y2, r):
    """Return a smooth polygon point list approximating a rounded rect.

    Used with canvas.create_polygon(..., smooth=True) since plain Tkinter
    has no native rounded-rectangle primitive.
    """
    r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
    return [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]


def draw_rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    """Draw a rounded rectangle on a Tkinter canvas and return its item id."""
    points = rounded_rect_points(x1, y1, x2, y2, r)
    return canvas.create_polygon(points, smooth=True, splinesteps=24, **kwargs)


def pick_font(root, preferred, fallback):
    """Return `preferred` if its family is installed, else `fallback`."""
    import tkinter.font as tkfont
    try:
        families = set(tkfont.families(root))
    except Exception:
        return fallback
    return preferred if preferred[0] in families else fallback
