---
id: 003
title: Event-tap gesture activation + click-vs-hold disambiguation (the kernel)
status: ready
depends_on: [001]
effort: L
---

# Event-tap gesture activation + click-vs-hold disambiguation (the kernel)

## What
The risky core. Make a normal button-down (back/forward/middle) on the macOS CGEventTap **arm gesture
tracking** when that button is a gesture owner, compute direction from the slide, and — critically —
still deliver the button's **normal click** when the user taps without sliding (dual-mode). Freeze the
cursor while a gesture is active.

## Why
This is the single missing wire (PRD § Technical Considerations): nothing currently sets
`_gesture_active` from an event-tap button-down — only the HID listener does
(`core/mouse_hook_macos.py:422-432`). Satisfies D2, D4, D7, D8 and the dual-mode + latency acceptance
criteria.

## Technical Approach
- **`core/mouse_hook_macos.py`, `OtherMouseDown`/`OtherMouseUp` handlers (`:329-366`):**
  - On **down of a gesture-owner button**: record press time, set `_gesture_active`, call
    `_start_gesture_tracking()` (mirror `_on_hid_gesture_down` `:422-432`), and **defer** the normal
    down (do not emit MIDDLE/XBUTTON1/XBUTTON2 down yet; return None to swallow).
  - **Move branch (`:289-327`) needs no logic change** — it already accumulates deltas when
    `_gesture_active`. For **D8**, suppress net pointer delivery while active (return None / zero the
    posted delta) so the cursor doesn't drift.
  - On **up**: compute `held_ms` and inspect accumulated delta. Treat as a gesture **only if**
    `held_ms ≥ gesture_hold_floor_ms` AND `_detect_gesture_event()` returns a direction; then
    `_finish_gesture_tracking()` and let the direction event dispatch. **Else** synthesize the deferred
    normal click (down+up) — mirror `should_click = not self._gesture_triggered` (`:434-450`). Use the
    existing injection path + `_INJECTED_EVENT_MARKER` (`:46`, `:83-133`) so replayed clicks aren't
    re-captured.
- Owner set + `hold_floor_ms` arrive via the extended `configure_gestures` (issue 004); for this issue,
  accept them through the hook's gesture-config state and default to "no owners" when unset (feature off).
- **One active gesture at a time:** if a second owner button goes down while one is active, pass it
  through normally (first-wins, per PRD edge case).
- Do not reset `_gesture_active` on a profile reload mid-hold (PRD edge case).

## Acceptance Criteria
- [ ] Owner button down → slide > threshold → release ⇒ a `gesture_swipe_<dir>` is detected; no normal click emitted.
- [ ] Owner button quick tap (held < floor, or sub-deadzone) ⇒ normal click IS emitted and reaches the app.
- [ ] Non-owner buttons behave exactly as before (instant, no defer).
- [ ] While a gesture is active, net cursor delta delivered to the OS is zero (D8).
- [ ] The HID `_on_hid_gesture_down/up` path is untouched (MX Master regression guard).

## Test Plan
- New `tests/test_event_tap_gesture.py` with a simulated event feeder (fake CGEvent dicts / the same
  seam existing hook tests use — see `tests/test_mouse_hook.py`): feed down→moves→up sequences and
  assert emitted events for: (a) clean gesture, (b) tap-no-move → click, (c) held-but-below-deadzone
  → click, (d) below-hold-floor fast flick → click, (e) two-owner overlap → first wins.
- Assert cursor-freeze by checking the posted-delta accumulator stays zero during active tracking.
