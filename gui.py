import os
import sys
import tkinter as tk

import theme
import config
from engine import ClickEngine, MAX_ALLOWED_CPS, BUTTON_MAP
from keybind_manager import KeybindManager

ICON_FILENAME = "icon.ico"

WINDOW_W = 360
WINDOW_H = 460
CORNER_RADIUS = 30
TITLEBAR_H = 44


def _resolve_icon_path():
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, ICON_FILENAME)
    return path if os.path.isfile(path) else None


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


class DotButton(tk.Canvas):

    def __init__(self, parent, command, diameter, fill, hover):
        super().__init__(parent, width=diameter, height=diameter, bg=theme.BG,
                          highlightthickness=0, bd=0, cursor="hand2")
        self._command = command
        self._fill, self._hover = fill, hover
        self._dot = self.create_oval(1, 1, diameter - 1, diameter - 1,
                                      fill=fill, outline="")
        self.bind("<Enter>", lambda e: self.itemconfig(self._dot, fill=self._hover))
        self.bind("<Leave>", lambda e: self.itemconfig(self._dot, fill=self._fill))
        self.bind("<Button-1>", lambda e: self._command() if self._command else None)


class PillEntry(tk.Canvas):

    def __init__(self, parent, width, height, initial="", font=None):
        font = font or theme.pick_font(parent, theme.FONT_INPUT_CANDIDATES)
        super().__init__(parent, width=width, height=height, bg=theme.BG,
                          highlightthickness=0, bd=0)
        radius = height / 2
        self._rect = theme.draw_rounded_rect(
            self, 0, 0, width, height, radius,
            fill=theme.INPUT_BG, outline="",
        )

        self.var = tk.StringVar(value=initial)
        self._entry = tk.Entry(
            self, textvariable=self.var, font=font, justify="center",
            relief="flat", bd=0, bg=theme.INPUT_BG, fg=theme.TEXT_PRIMARY,
            insertbackground=theme.TEXT_PRIMARY, highlightthickness=0,
        )
        self.create_window(width / 2, height / 2, window=self._entry,
                            width=width - 24, height=height - 12)

        self._entry.bind("<FocusIn>", lambda e: self.itemconfig(self._rect, fill=theme.INPUT_BG_FOCUS))
        self._entry.bind("<FocusOut>", lambda e: self.itemconfig(self._rect, fill=theme.INPUT_BG))
        self._entry.bind("<FocusIn>", lambda e: self._entry.configure(bg=theme.INPUT_BG_FOCUS), add="+")
        self._entry.bind("<FocusOut>", lambda e: self._entry.configure(bg=theme.INPUT_BG), add="+")

    def get(self):
        return self.var.get()


class Dropdown(tk.Frame):

    def __init__(self, parent, options, initial, on_select, width=120, height=38, font=None):
        super().__init__(parent, bg=theme.BG)
        self._option_list = options
        self._value = initial
        self._on_select = on_select
        self._font = font or theme.pick_font(parent, theme.FONT_LABEL_CANDIDATES)
        self._popup = None

        self.button = RoundedButton(
            self, text=self._label(), command=self._toggle_popup,
            width=width, height=height,
            fill=theme.INPUT_BG, hover=theme.INPUT_BG_FOCUS, pressed=theme.INPUT_BG_FOCUS,
            text_color=theme.TEXT_PRIMARY, font=self._font, radius=height / 2,
        )
        self.button.pack()

    def _label(self):
        return f"{self._value}   \u25be"

    def get(self):
        return self._value

    def _toggle_popup(self):
        if self._popup is not None:
            self._close_popup()
        else:
            self._open_popup()

    def _open_popup(self):
        x = self.button.winfo_rootx()
        y = self.button.winfo_rooty() + self.button.winfo_height() + 6

        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg=theme.PANEL_BORDER)
        popup.geometry(f"+{x}+{y}")

        inner = tk.Frame(popup, bg=theme.PANEL)
        inner.pack(padx=1, pady=1)

        for opt in self._option_list:
            row = tk.Label(
                inner, text=opt, bg=theme.PANEL, fg=theme.TEXT_PRIMARY,
                font=self._font, anchor="w", padx=16, pady=7, cursor="hand2",
                width=12,
            )
            row.pack(fill="x")
            row.bind("<Enter>", lambda e, r=row: r.configure(bg=theme.INPUT_BG_FOCUS))
            row.bind("<Leave>", lambda e, r=row: r.configure(bg=theme.PANEL))
            row.bind("<Button-1>", lambda e, o=opt: self._select(o))

        popup.bind("<FocusOut>", lambda e: self._close_popup())
        popup.focus_force()
        self._popup = popup

    def _select(self, opt):
        self._value = opt
        self.button.set_style(text=self._label())
        self._close_popup()
        if self._on_select:
            self._on_select(opt)

    def _close_popup(self):
        if self._popup is not None:
            self._popup.destroy()
            self._popup = None


class RoundWindow(tk.Canvas):

    def __init__(self, root, width, height, radius):
        self._transparent_supported = sys.platform == "win32"
        key = theme.TRANSPARENT_KEY if self._transparent_supported else theme.BG
        root.configure(bg=key)
        if self._transparent_supported:
            try:
                root.wm_attributes("-transparentcolor", key)
            except Exception:
                self._transparent_supported = False

        super().__init__(root, width=width, height=height, bg=key,
                          highlightthickness=0, bd=0)
        self.place(x=0, y=0)
        theme.draw_rounded_rect(self, 0, 0, width, height, radius,
                                 fill=theme.BG, outline="")

        self.content = tk.Frame(self, bg=theme.BG)
        self.create_window(width / 2, height / 2, window=self.content,
                            width=width, height=height)


class NovumApp:

    def __init__(self, root: tk.Tk):
        self.root = root
        self._drag_offset = (0, 0)
        self._configure_root()

        self.engine = ClickEngine(on_state_change=self._on_engine_state_change)

        saved = config.load_config()
        self.keybinds = KeybindManager(
            on_trigger=self._on_hotkey,
            on_capture_complete=self._on_keybind_captured,
            initial_hotkey_str=saved.get("hotkey_str"),
            initial_display_str=saved.get("display_str"),
        )

        self.font_title = theme.pick_font(self.root, theme.FONT_TITLE_CANDIDATES)
        self.font_button = theme.pick_font(self.root, theme.FONT_BUTTON_CANDIDATES)
        self.font_label = theme.pick_font(self.root, theme.FONT_LABEL_CANDIDATES)

        self._build_ui()

    def _configure_root(self):
        self.root.title("NOVUM")
        self.root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.root.resizable(False, False)
        self.root.overrideredirect(True)

        icon_path = _resolve_icon_path()
        if icon_path:
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        self.root.bind("<Map>", self._on_map)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.window = RoundWindow(self.root, WINDOW_W, WINDOW_H, CORNER_RADIUS)

    def _on_map(self, event):
        if self.root.state() == "normal" and not self.root.overrideredirect():
            self.root.overrideredirect(True)

    def _build_ui(self):
        outer = self.window.content
        self._build_titlebar(outer)
        self._build_body(outer)

    def _build_titlebar(self, parent):
        bar = tk.Frame(parent, bg=theme.BG, height=TITLEBAR_H)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        title_wrap = tk.Frame(bar, bg=theme.BG)
        title_wrap.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(title_wrap, text="NOVUM", bg=theme.BG, fg=theme.TEXT_PRIMARY,
                  font=self.font_title).pack()

        controls = tk.Frame(bar, bg=theme.BG)
        controls.pack(side="right", padx=(0, 18))

        close_dot = DotButton(controls, self._on_close, diameter=13,
                               fill=theme.DANGER, hover=theme.DANGER_HOVER)
        close_dot.pack(side="right", padx=(6, 0))

        min_dot = DotButton(controls, self._on_minimize, diameter=13,
                             fill="#e0a940", hover="#eab659")
        min_dot.pack(side="right")

        for widget in (bar, title_wrap):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._do_drag)

        sep = tk.Canvas(parent, height=1, bg=theme.BG, highlightthickness=0, bd=0)
        sep.pack(fill="x")
        sep.bind("<Configure>", lambda e: self._draw_dotted(sep, e.width))

    def _draw_dotted(self, canvas, width):
        canvas.delete("all")
        canvas.create_line(0, 0, width, 0, fill=theme.PANEL_BORDER, dash=(2, 3))

    def _start_drag(self, event):
        self._drag_offset = (event.x_root - self.root.winfo_x(),
                              event.y_root - self.root.winfo_y())

    def _do_drag(self, event):
        x = event.x_root - self._drag_offset[0]
        y = event.y_root - self._drag_offset[1]
        self.root.geometry(f"+{x}+{y}")

    def _on_minimize(self):
        self.root.overrideredirect(False)
        self.root.iconify()

    def _build_body(self, parent):
        body = tk.Frame(parent, bg=theme.BG)
        body.pack(fill="both", expand=True, padx=26, pady=(20, 26))

        cps_row = tk.Frame(body, bg=theme.BG)
        cps_row.pack(fill="x")

        min_col = tk.Frame(cps_row, bg=theme.BG)
        min_col.pack(side="left", expand=True, fill="x")
        tk.Label(min_col, text="MIN CPS", bg=theme.BG, fg=theme.TEXT_SECONDARY,
                  font=self.font_label).pack()
        self.min_cps_entry = PillEntry(min_col, width=120, height=46, initial="8")
        self.min_cps_entry.pack(pady=(8, 0))

        max_col = tk.Frame(cps_row, bg=theme.BG)
        max_col.pack(side="left", expand=True, fill="x")
        tk.Label(max_col, text="MAX CPS", bg=theme.BG, fg=theme.TEXT_SECONDARY,
                  font=self.font_label).pack()
        self.max_cps_entry = PillEntry(max_col, width=120, height=46, initial="12")
        self.max_cps_entry.pack(pady=(8, 0))

        self.error_label = tk.Label(body, text="", bg=theme.BG, fg=theme.DANGER,
                                     font=self.font_label)
        self.error_label.pack(pady=(10, 0))

        mouse_row = tk.Frame(body, bg=theme.BG)
        mouse_row.pack(fill="x", pady=(16, 0))
        tk.Label(mouse_row, text="Mouse Button", bg=theme.BG, fg=theme.TEXT_PRIMARY,
                  font=self.font_label).pack(side="left")
        self.button_dropdown = Dropdown(
            mouse_row, options=list(BUTTON_MAP.keys()), initial="Left",
            on_select=lambda v: None, width=110, height=36,
        )
        self.button_dropdown.pack(side="right")

        action_row = tk.Frame(body, bg=theme.BG)
        action_row.pack(fill="x", pady=(20, 0))

        self.start_button = RoundedButton(
            action_row, text=f"Start ({self.keybinds.display_string})",
            command=self._on_start_clicked,
            width=(WINDOW_W - 52 - 12) // 2, height=48,
            fill=theme.ACCENT, hover=theme.ACCENT_HOVER, pressed=theme.ACCENT_PRESSED,
            text_color="#0b0b0d", font=self.font_button, radius=24,
        )
        self.start_button.pack(side="left")

        spacer = tk.Frame(action_row, width=12, height=1, bg=theme.BG)
        spacer.pack(side="left")

        self.stop_button = RoundedButton(
            action_row, text=f"Stop ({self.keybinds.display_string})",
            command=self._on_stop_clicked,
            width=(WINDOW_W - 52 - 12) // 2, height=48,
            fill=theme.DANGER, hover=theme.DANGER_HOVER, pressed=theme.DANGER_PRESSED,
            text_color="#1a0b0d", font=self.font_button, radius=24,
        )
        self.stop_button.pack(side="left")

        self.status_label = tk.Label(body, text="Stopped", bg=theme.BG,
                                      fg=theme.TEXT_SECONDARY, font=self.font_label)
        self.status_label.pack(pady=(16, 0))

        bottom_row = tk.Frame(body, bg=theme.BG)
        bottom_row.pack(fill="x", pady=(22, 0))

        self.hotkey_button = RoundedButton(
            bottom_row, text="Change Hotkey", command=self._on_keybind_clicked,
            width=(WINDOW_W - 52 - 12) // 2, height=42,
            fill=theme.PANEL, hover="#202024", pressed="#101012",
            text_color=theme.TEXT_PRIMARY, font=self.font_label, radius=14,
        )
        self.hotkey_button.pack(side="left")

        spacer2 = tk.Frame(bottom_row, width=12, height=1, bg=theme.BG)
        spacer2.pack(side="left")

        self.reset_button = RoundedButton(
            bottom_row, text="Reset Defaults", command=self._on_reset_clicked,
            width=(WINDOW_W - 52 - 12) // 2, height=42,
            fill=theme.PANEL, hover="#202024", pressed="#101012",
            text_color=theme.TEXT_PRIMARY, font=self.font_label, radius=14,
        )
        self.reset_button.pack(side="left")

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
        self.engine.configure(min_cps, max_cps, self.button_dropdown.get())
        return True

    def _on_start_clicked(self):
        if not self.engine.is_running():
            self._validate_and_apply() and self.engine.start()

    def _on_stop_clicked(self):
        if self.engine.is_running():
            self.engine.stop()

    def _on_toggle_clicked(self):
        if self.engine.is_running():
            self.engine.stop()
        else:
            if self._validate_and_apply():
                self.engine.start()

    def _on_hotkey(self):
        self.root.after(0, self._on_toggle_clicked)

    def _on_keybind_clicked(self):
        self.hotkey_button.set_style(text="Press a key...")
        self.keybinds.begin_capture()

    def _on_keybind_captured(self, display_str):
        def update():
            self.hotkey_button.set_style(text="Change Hotkey")
            self.start_button.set_style(text=f"Start ({display_str})")
            self.stop_button.set_style(text=f"Stop ({display_str})")
        self.root.after(0, update)
        config.save_config({
            "hotkey_str": self.keybinds.hotkey_string,
            "display_str": display_str,
        })

    def _on_reset_clicked(self):
        self.min_cps_entry.var.set("8")
        self.max_cps_entry.var.set("12")
        self.error_label.configure(text="")

    def _on_engine_state_change(self, is_running: bool):
        self.root.after(0, self._update_status_ui, is_running)

    def _update_status_ui(self, is_running: bool):
        if is_running:
            self.status_label.configure(text="Running", fg=theme.STATUS_RUNNING)
        else:
            self.status_label.configure(text="Stopped", fg=theme.TEXT_SECONDARY)

    def _on_close(self):
        self.engine.shutdown()
        self.keybinds.shutdown()
        self.root.destroy()
