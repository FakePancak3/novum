"""
keybind_manager.py
-------------------
Manages a single global, rebindable hotkey (optionally with modifiers,
e.g. "Ctrl+H") using pynput.

Two pynput mechanisms are combined:

- `keyboard.GlobalHotKeys` runs a lightweight OS-level listener on its
  own thread and fires a callback when the configured key combo is
  pressed — this is what makes the toggle work even when the app's
  window isn't focused. It's re-created whenever the bound combo
  changes (GlobalHotKeys doesn't support live-updating its key map).
- `keyboard.Listener` is used transiently, only while the user is in
  "capture mode" (after clicking "Add a keybind..."), to watch which
  modifier keys are held and grab the next non-modifier key to form a
  combo binding.

Why not just use key.char directly
-----------------------------------
When a modifier like Ctrl is held, pynput/the OS reports `.char` as a
control character rather than the plain letter (e.g. Ctrl+H comes
through as the backspace control code, not "H"). Rendering that raw
control character in a Tkinter label shows up as an unprintable
"tofu" box. To avoid this, the actual letter is recovered from the
key's virtual key code (`.vk`) whenever possible, which is unaffected
by modifier state.
"""

from pynput import keyboard

# Modifier keys, normalized to a small canonical set. getattr() with a
# default guards against attributes that don't exist on every platform.
_MODIFIER_ATTRS = {
    "ctrl": ["ctrl", "ctrl_l", "ctrl_r"],
    "alt": ["alt", "alt_l", "alt_r", "alt_gr"],
    "shift": ["shift", "shift_l", "shift_r"],
    "cmd": ["cmd", "cmd_l", "cmd_r"],
}
_MODIFIER_ORDER = ["ctrl", "alt", "shift", "cmd"]


def _build_modifier_lookup():
    lookup = {}
    for canonical, attr_names in _MODIFIER_ATTRS.items():
        for attr_name in attr_names:
            key_obj = getattr(keyboard.Key, attr_name, None)
            if key_obj is not None:
                lookup[key_obj] = canonical
    return lookup


_MODIFIER_LOOKUP = _build_modifier_lookup()


def normalize_modifier(key):
    """Return 'ctrl'/'alt'/'shift'/'cmd' if `key` is a modifier, else None."""
    return _MODIFIER_LOOKUP.get(key)


def normalize_base_key(key):
    """Turn a non-modifier pynput key into (hotkey_token, display_token).

    hotkey_token is suitable for GlobalHotKeys (e.g. 'h', '<f6>').
    display_token is human-readable (e.g. 'H', 'F6').
    Returns (None, None) if the key can't be reliably represented.
    """
    if isinstance(key, keyboard.KeyCode):
        # Prefer the virtual key code: it identifies the physical key
        # regardless of modifier state, so Ctrl+H still resolves to 'H'
        # instead of a control character.
        vk = getattr(key, "vk", None)
        if vk is not None and 65 <= vk <= 90:  # A-Z on Windows/X11 VK codes
            letter = chr(vk).lower()
            return letter, letter.upper()
        if vk is not None and 48 <= vk <= 57:  # 0-9
            digit = chr(vk)
            return digit, digit
        if key.char is not None and key.char.isprintable():
            return key.char.lower(), key.char.upper()
        return None, None
    # Named keys like Key.f6, Key.space, Key.esc
    name = str(key).split(".")[-1]
    return f"<{name}>", name.replace("_", " ").title()


class KeybindManager:
    """Owns the active global hotkey and the transient "capture next key
    (+ modifiers)" mode used when the user rebinds the toggle key."""

    def __init__(self, on_trigger, on_capture_complete=None):
        """
        on_trigger: callable() invoked when the bound hotkey is pressed.
        on_capture_complete: callable(display_str) invoked after a new
        combo has been captured and successfully bound.
        """
        self._on_trigger = on_trigger
        self._on_capture_complete = on_capture_complete

        self._hotkey_str = "<f6>"
        self._display_str = "F6"
        self._hotkey_listener = None
        self._capture_listener = None
        self._held_modifiers = set()

        self._start_global_listener()

    # -- public API -------------------------------------------------------
    @property
    def display_string(self) -> str:
        return self._display_str

    def begin_capture(self):
        """Start watching for modifier keys + the next base key, then
        bind that combo as the new global toggle hotkey.

        While capturing, the previous global hotkey stays active so the
        clicker can still be toggled with the old combo until the new
        one is confirmed.
        """
        self._stop_capture_listener()
        self._held_modifiers = set()

        def on_press(key):
            mod = normalize_modifier(key)
            if mod:
                self._held_modifiers.add(mod)
                return  # keep listening for the base key

            hotkey_token, display_token = normalize_base_key(key)
            if hotkey_token is None:
                return  # unsupported key (e.g. a dead key) — keep waiting

            mods_in_order = [m for m in _MODIFIER_ORDER if m in self._held_modifiers]
            hotkey_str = "+".join([f"<{m}>" for m in mods_in_order] + [hotkey_token])
            display_str = "+".join([m.upper() for m in mods_in_order] + [display_token])

            self._rebind(hotkey_str, display_str)
            if self._on_capture_complete:
                self._on_capture_complete(display_str)
            return False  # stop this one-shot listener

        def on_release(key):
            mod = normalize_modifier(key)
            if mod:
                self._held_modifiers.discard(mod)

        self._capture_listener = keyboard.Listener(
            on_press=on_press, on_release=on_release
        )
        self._capture_listener.start()

    def shutdown(self):
        self._stop_capture_listener()
        self._stop_global_listener()

    # -- internal -------------------------------------------------------
    def _rebind(self, hotkey_str: str, display_str: str):
        self._hotkey_str = hotkey_str
        self._display_str = display_str
        self._start_global_listener()

    def _start_global_listener(self):
        self._stop_global_listener()
        try:
            self._hotkey_listener = keyboard.GlobalHotKeys(
                {self._hotkey_str: self._on_trigger}
            )
            self._hotkey_listener.start()
        except Exception:
            self._hotkey_listener = None

    def _stop_global_listener(self):
        if self._hotkey_listener is not None:
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass
            self._hotkey_listener = None

    def _stop_capture_listener(self):
        if self._capture_listener is not None:
            try:
                self._capture_listener.stop()
            except Exception:
                pass
            self._capture_listener = None
