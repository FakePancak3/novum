BG = "#0b0b0d"
PANEL = "#161619"
PANEL_BORDER = "#26262b"
INPUT_BG = "#1e1e22"
INPUT_BG_FOCUS = "#232328"

TEXT_PRIMARY = "#f2f2f5"
TEXT_SECONDARY = "#8b8b93"
TEXT_MUTED = "#5b5b63"

ACCENT = "#7c5cff"
ACCENT_HOVER = "#8f73ff"
ACCENT_PRESSED = "#6a4de8"

DANGER = "#ff5c6c"
DANGER_HOVER = "#ff727f"
DANGER_PRESSED = "#e6505f"

STATUS_RUNNING = "#3ddc84"
STATUS_STOPPED = "#5b5b63"

LINE_DEFAULT = "#2c2c31"
LINE_FOCUS = ACCENT

TRANSPARENT_KEY = "#010203"

FONT_LABEL = ("Segoe UI", 9)
FONT_MONO_SMALL = ("Consolas", 9)

def rounded_rect_points(x1, y1, x2, y2, r):
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
    points = rounded_rect_points(x1, y1, x2, y2, r)
    return canvas.create_polygon(points, smooth=True, splinesteps=24, **kwargs)

def pick_font(root, candidates):
    import tkinter.font as tkfont
    try:
        families = set(tkfont.families(root))
    except Exception:
        return candidates[-1]
    for candidate in candidates:
        if candidate[0] in families:
            return candidate
    return candidates[-1]


FONT_TITLE_CANDIDATES = [
    ("Bahnschrift SemiBold", 22),
    ("Segoe UI Semibold", 20),
    ("Segoe UI", 20, "bold"),
]
FONT_BUTTON_CANDIDATES = [
    ("Bahnschrift SemiBold", 13),
    ("Segoe UI Semibold", 12),
    ("Segoe UI", 12, "bold"),
]
FONT_INPUT_CANDIDATES = [
    ("Bahnschrift SemiLight", 16),
    ("Segoe UI", 14),
]
FONT_LABEL_CANDIDATES = [
    ("Bahnschrift", 9),
    ("Segoe UI", 9),
]
