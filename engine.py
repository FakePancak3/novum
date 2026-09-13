"""
engine.py
---------
The auto-clicking engine, fully decoupled from any GUI toolkit. This is
the "model" layer: it owns the background thread, the click timing
algorithm, and thread-safe configuration. The GUI (gui.py) only ever
calls its public methods and receives state-change callbacks — it never
touches thread internals directly.

CPS randomization strategy
---------------------------
Picking a brand-new random delay for every single click tends to make
the *average* click rate wander outside the user's requested range, and
also produces a "flat" statistical texture that doesn't resemble how a
human's speed drifts over time.

Instead we use a phase-based model:

1. Pick a target CPS for the upcoming "phase" — a random value drawn
   from [min_cps, max_cps].
2. Pick a phase duration — a random span of time (PHASE_MIN_DURATION to
   PHASE_MAX_DURATION seconds) during which we aim for that target CPS.
3. For each click inside the phase, compute the ideal delay
   (1 / target_cps) and apply a small +/- jitter so consecutive clicks
   aren't perfectly uniform.
4. Clamp every computed delay to [MIN_DELAY, MAX_DELAY] so the loop can
   never spin dangerously fast or stall unnaturally long.
5. When a phase ends, pick a new target CPS, biased away from repeating
   almost the same value as the previous phase, so speed changes are
   noticeable rather than looking like a fixed repeating cycle.

This keeps short-term speed visibly varying (e.g. 8 -> 9 -> 10 -> 12 ->
11 -> 9 -> 8 ...) while the long-run average stays solidly within the
configured [min_cps, max_cps] band.
"""

import random
import threading
import time

from pynput.mouse import Controller, Button

MIN_DELAY = 0.03            # seconds; hard floor on any single click delay
MAX_DELAY = 0.5             # seconds; hard ceiling on any single click delay
PHASE_MIN_DURATION = 0.5    # seconds a given CPS "phase" lasts, minimum
PHASE_MAX_DURATION = 2.0    # seconds a given CPS "phase" lasts, maximum
JITTER_FRACTION = 0.15      # +/-15% jitter applied to each click's delay
MAX_ALLOWED_CPS = 50        # sanity cap enforced by validation layer

# Delay before the very first click after Start is pressed. Without
# this, the cursor is typically still resting on the Start button when
# the first synthetic click fires, which immediately re-triggers the
# button (a real OS-level click at the cursor's position looks no
# different to Tkinter than a manual one) and stops the clicker right
# after starting it. This grace period gives the user time to move the
# mouse to their intended target first.
START_GRACE_PERIOD = 0.35

BUTTON_MAP = {
    "Left": Button.left,
    "Right": Button.right,
    "Middle": Button.middle,
}


class ClickEngine:
    """Owns the background click thread and naturalistic CPS timing."""

    def __init__(self, on_state_change=None):
        """
        on_state_change: optional callable(is_running: bool) invoked
        whenever the engine starts or stops (from whatever thread
        triggered the change — callers must marshal to the GUI thread
        themselves if needed).
        """
        self._thread = None
        self._running = threading.Event()
        self._stop_flag = threading.Event()
        self._lock = threading.Lock()

        self.min_cps = 8.0
        self.max_cps = 12.0
        self.button = Button.left

        self._mouse = Controller()
        self._on_state_change = on_state_change
        self._last_phase_cps = None

    # -- configuration --------------------------------------------------
    def configure(self, min_cps: float, max_cps: float, button_name: str = "Left"):
        with self._lock:
            self.min_cps = min_cps
            self.max_cps = max_cps
            self.button = BUTTON_MAP.get(button_name, Button.left)

    # -- lifecycle --------------------------------------------------------
    def start(self):
        if self.is_running():
            return
        self._stop_flag.clear()
        self._running.set()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._notify(True)

    def stop(self):
        if not self.is_running():
            return
        self._stop_flag.set()
        self._running.clear()
        self._notify(False)

    def toggle(self):
        if self.is_running():
            self.stop()
        else:
            self.start()

    def is_running(self) -> bool:
        return self._running.is_set()

    def shutdown(self):
        """Stop and join the click thread cleanly (call on app exit)."""
        self._stop_flag.set()
        self._running.clear()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _notify(self, is_running: bool):
        if self._on_state_change:
            try:
                self._on_state_change(is_running)
            except Exception:
                pass

    # -- internal timing logic --------------------------------------------
    def _pick_next_phase_cps(self, min_cps, max_cps, avoid_value=None):
        value = random.uniform(min_cps, max_cps)
        span = max_cps - min_cps
        if avoid_value is not None and span > 0.5:
            attempts = 0
            while abs(value - avoid_value) < span * 0.15 and attempts < 5:
                value = random.uniform(min_cps, max_cps)
                attempts += 1
        return value

    def _run_loop(self):
        phase_end_time = 0.0
        target_cps = None

        # Grace period so the first click doesn't land on the button
        # the user just pressed (see START_GRACE_PERIOD above).
        slept = 0.0
        step = 0.02
        while slept < START_GRACE_PERIOD and not self._stop_flag.is_set():
            t = min(step, START_GRACE_PERIOD - slept)
            time.sleep(t)
            slept += t

        while not self._stop_flag.is_set():
            now = time.monotonic()

            with self._lock:
                min_cps = max(0.1, self.min_cps)
                max_cps = max(min_cps, self.max_cps)
                button = self.button

            if target_cps is None or now >= phase_end_time:
                target_cps = self._pick_next_phase_cps(
                    min_cps, max_cps, avoid_value=self._last_phase_cps
                )
                self._last_phase_cps = target_cps
                phase_duration = random.uniform(PHASE_MIN_DURATION, PHASE_MAX_DURATION)
                phase_end_time = now + phase_duration

            ideal_delay = 1.0 / target_cps
            jitter = random.uniform(-JITTER_FRACTION, JITTER_FRACTION)
            delay = max(MIN_DELAY, min(MAX_DELAY, ideal_delay * (1.0 + jitter)))

            try:
                self._mouse.click(button, 1)
            except Exception:
                break

            slept = 0.0
            step = 0.02
            while slept < delay and not self._stop_flag.is_set():
                t = min(step, delay - slept)
                time.sleep(t)
                slept += t

        self._running.clear()
