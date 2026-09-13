import os
import sys
import tkinter as tk

import theme
from engine import ClickEngine, MAX_ALLOWED_CPS
from keybind_manager import KeybindManager
from winstyle import apply_dark_titlebar

ICON_FILENAME = "icon.ico"

def _resolve_icon_path():
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, ICON_FILENAME)
    return path if os.path.isfile(path) else None

WINDOW_W = 320
WINDOW_H = 340

class RoundedButton(tk.Canvas):

    def __init__(self, parent, text, command, width, height,
                 fill, hover, pressed, text_color, font, radius=10):
        super().__init__(parent, width=width, height=height,
                          bg=theme.BG, highlightthickness=0, bd=0,
                          cursor="hand2")
        self._command = command
        self._btn_w, self._btn_h = width, height
        self._fill, self._hover, self._pressed = fill, hover, pressed

        self._rect = theme.draw_rounded_rect(
            self, 1, 1, width - 1, height - 1, radius,
            fill=fill, outline="",
        )
        self._label = self.create_text(
            width / 2, height / 2, text=text, fill=text_color, font=font,
        )

        self.bind("<Enter>", lambda e: self.itemconfig(self._rect, fill=self._hover))
        self.bind("<Leave>", lambda e: self.itemconfig(self._rect, fill=self._fill))
        self.bind("<ButtonPress-1>", lambda e: self.itemconfig(self._rect, fill=self._pressed))
        self.bind("<ButtonRelease-1>", self._on_release)

    def set_style(self, text=None, fill=None, hover=None, pressed=None, text_color=None):
        if text is not None:
            self.itemconfig(self._label, text=text)
        if fill is not None:
            self._fill = fill
        if hover is not None:
            self._hover = hover
        if pressed is not None:
            self._pressed = pressed
        if text_color is not None:
            self.itemconfig(self._label, fill=text_color)
        self.itemconfig(self._rect, fill=self._fill)

    def _on_release(self, evt):
        inside = 0 <= evt.x <= self._btn_w and 0 <= evt.y <= self._btn_h
        self.itemconfig(self._rect, fill=self._hover if inside else self._fill)
        if inside and self._command:
            self._command()

class MinimalEntry(tk.Frame):

    def __init__(self, parent, width, initial="", font=theme.FONT_INPUT, justify="center"):
        super().__init__(parent, bg=theme.BG)
        self._width = width

        self.var = tk.StringVar(value=initial)
        self._entry = tk.Entry(
            self, textvariable=self.var, font=font, justify=justify,
            relief="flat", bd=0, bg=theme.BG, fg=theme.TEXT_PRIMARY,
            insertbackground=theme.TEXT_PRIMARY, highlightthickness=0,
            width=6,
        )
        self._entry.pack(fill="x", pady=(0, 6))

        self._line = tk.Canvas(self, width=width, height=2, bg=theme.BG,
                                highlightthickness=0, bd=0)
        self._line.pack(fill="x")
        self._line_item = self._line.create_rectangle(
            0, 0, width, 2, fill=theme.LINE_DEFAULT, outline="",
        )
        self._line.bind(
            "<Configure>",
            lambda e: self._line.coords(self._line_item, 0, 0, e.width, 2),
        )

        self._entry.bind("<FocusIn>", lambda e: self._line.itemconfig(self._line_item, fill=theme.LINE_FOCUS))
        self._entry.bind("<FocusOut>", lambda e: self._line.itemconfig(self._line_item, fill=theme.LINE_DEFAULT))

    def get(self):
        return self.var.get()

class NovumApp:

    def __init__(self, root: tk.Tk):
        self.root = root
        self._configure_root()

        self.engine = ClickEngine(on_state_change=self._on_engine_state_change)
        self.keybinds = KeybindManager(
            on_trigger=self._on_hotkey,
            on_capture_complete=self._on_keybind_captured,
        )

        self.font_title = theme.pick_font(self.root, theme.FONT_TITLE, theme.FONT_TITLE_FALLBACK)
        self.font_button = theme.pick_font(self.root, theme.FONT_BUTTON, theme.FONT_BUTTON_FALLBACK)

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_root(self):
        self.root.title("NOVUM")
        self.root.configure(bg=theme.BG)
        self.root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.root.resizable(False, False)
        apply_dark_titlebar(self.root)

        icon_path = _resolve_icon_path()
        if icon_path:
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

    def _build_ui(self):
        outer = tk.Frame(self.root, bg=theme.BG)
        outer.pack(fill="both", expand=True, padx=28, pady=26)

        tk.Label(
            outer, text="N O V U M", bg=theme.BG, fg=theme.TEXT_PRIMARY,
            font=self.font_title,
        ).pack(anchor="w")

        cps_row = tk.Frame(outer, bg=theme.BG)
        cps_row.pack(fill="x", pady=(36, 0))

        min_col = tk.Frame(cps_row, bg=theme.BG)
        min_col.pack(side="left", expand=True, fill="x")
        tk.Label(min_col, text="MIN CPS", bg=theme.BG, fg=theme.TEXT_MUTED,
                  font=theme.FONT_LABEL).pack(anchor="w")
        self.min_cps_entry = MinimalEntry(min_col, width=100, initial="8")
        self.min_cps_entry.pack(fill="x", pady=(6, 0))

        max_col = tk.Frame(cps_row, bg=theme.BG)
        max_col.pack(side="left", expand=True, fill="x", padx=(20, 0))
        tk.Label(max_col, text="MAX CPS", bg=theme.BG, fg=theme.TEXT_MUTED,
                  font=theme.FONT_LABEL).pack(anchor="w")
        self.max_cps_entry = MinimalEntry(max_col, width=100, initial="12")
        self.max_cps_entry.pack(fill="x", pady=(6, 0))

        self.error_label = tk.Label(
            outer, text="", bg=theme.BG, fg=theme.DANGER, font=theme.FONT_LABEL,
        )
        self.error_label.pack(anchor="w", pady=(10, 0))

        self.start_button = RoundedButton(
            outer, text="START", command=self._on_toggle_clicked,
            width=WINDOW_W - 56, height=48,
            fill=theme.ACCENT, hover=theme.ACCENT_HOVER, pressed=theme.ACCENT_PRESSED,
            text_color="#0b0b0d", font=self.font_button, radius=10,
        )
        self.start_button.pack(pady=(18, 0))

        footer = tk.Frame(outer, bg=theme.BG)
        footer.pack(fill="x", pady=(28, 0))

        self.status_label = tk.Label(
            footer, text="Stopped", bg=theme.BG, fg=theme.TEXT_SECONDARY,
            font=theme.FONT_LABEL,
        )
        self.status_label.pack(side="left")

        keybind_row = tk.Frame(footer, bg=theme.BG, cursor="hand2")
        keybind_row.pack(side="right")
        tk.Label(keybind_row, text="Toggle key  ", bg=theme.BG,
                  fg=theme.TEXT_MUTED, font=theme.FONT_LABEL).pack(side="left")
        self.keybind_label = tk.Label(
            keybind_row, text=self.keybinds.display_string, bg=theme.BG,
            fg=theme.TEXT_PRIMARY, font=theme.FONT_LABEL,
        )
        self.keybind_label.pack(side="left")
        for widget in (keybind_row, self.keybind_label):
            widget.bind("<Button-1>", lambda e: self._on_keybind_clicked())

    def _validate_and_apply(self) -> bool:
        raw_min = self.min_cps_entry.get().strip()
        raw_max = self.max_cps_entry.get().strip()

        try:
            min_cps = float(raw_min)
            max_cps = float(raw_max)
        except ValueError:
            self.error_label.configure(text="CPS values must be numbers.")
            return False

        if min_cps <= 0 or max_cps <= 0:
            self.error_label.configure(text="CPS values must be greater than 0.")
            return False

        if min_cps > max_cps:
            self.error_label.configure(text="Min CPS cannot exceed max CPS.")
            return False

        if max_cps > MAX_ALLOWED_CPS:
            self.error_label.configure(text=f"Max CPS is capped at {MAX_ALLOWED_CPS}.")
            return False

        self.error_label.configure(text="")
        self.engine.configure(min_cps, max_cps, "Left")
        return True

    def _on_toggle_clicked(self):
        if self.engine.is_running():
            self.engine.stop()
        else:
            if self._validate_and_apply():
                self.engine.start()

    def _on_hotkey(self):
        self.root.after(0, self._on_toggle_clicked)

    def _on_keybind_clicked(self):
        self.keybind_label.configure(text="...")
        self.keybinds.begin_capture()

    def _on_keybind_captured(self, display_str):
        self.root.after(0, lambda: self.keybind_label.configure(text=display_str))

    def _on_engine_state_change(self, is_running: bool):
        self.root.after(0, self._update_status_ui, is_running)

    def _update_status_ui(self, is_running: bool):
        if is_running:
            self.status_label.configure(text="Running", fg=theme.STATUS_RUNNING)
            self.start_button.set_style(
                text="STOP", fill=theme.DANGER, hover=theme.DANGER_HOVER,
                pressed=theme.DANGER_PRESSED, text_color="#1a0b0d",
            )
        else:
            self.status_label.configure(text="Stopped", fg=theme.TEXT_SECONDARY)
            self.start_button.set_style(
                text="START", fill=theme.ACCENT, hover=theme.ACCENT_HOVER,
                pressed=theme.ACCENT_PRESSED, text_color="#0b0b0d",
            )

    def _on_close(self):
        self.engine.shutdown()
        self.keybinds.shutdown()
        self.root.destroy()
