# Per-button event-tap slide gestures (back/forward/middle)

Adds a working gesture path for mice that have no dedicated hardware gesture button.

## Problem

Mouser's gesture feature — hold a button, slide up/down/left/right, fire a per-direction
action — only *activates* when the device reports a diverted "gesture button held" event
over HID++. Only mice with a dedicated hardware gesture button (the MX Master thumb
button) ever emit that. Many Logitech mice — the MX Anywhere 2S among them — have no such
button, so they get zero working gestures today even though the direction-detection engine
underneath is already there and their side/middle buttons are ordinary mouse events on the
macOS event tap.

## Solution

An event-tap-driven arming path, per button: any of back/forward/middle can independently
own a 4-direction gesture. Holding an armed button and sliding past a deadzone runs the
existing direction engine and fires the bound action; a quick tap with no slide still fires
the button's normal mapping (dual-mode). No HID++ remap involved.

## Scope and caveats (read before merging)

1. **macOS only.** The event-tap arming path was added to `core/mouse_hook_macos.py` only.
   Windows/Linux have the identical gap (no dedicated gesture button on many mice) but
   share none of this wiring yet — a clean, separately-scoped follow-up.
2. **Per-device opt-in, not on by default for all mice.** A single catalog flag,
   `supports_event_tap_gestures`, gates which devices offer this. It is currently set on
   **one** device: the MX Anywhere 2S (`core/logi_device_catalog.py`) — the only mouse this
   was tested against. Any other mouse whose back/forward/middle buttons reach the event
   tap as standard `OtherMouseDown`/`Up` should work the same way, but each one is enabled
   by flipping this flag on its catalog entry only after someone verifies it on real
   hardware. No mouse is opted in implicitly.
3. **Off by default, no behavior change for existing users.** A button only arms a gesture
   if (a) the device's flag is set, (b) the user has bound at least one direction on it, and
   (c) the user has explicitly turned on gesture mode for that button in the UI. The
   existing MX Master HID++ gesture path is untouched — `core/hid_gesture.py` has a byte-for-byte
   empty diff in this branch.

## Reused vs. new

**Reused (~80%):** the direction-detection math (`decide_gesture`, deadzone/threshold/hold-floor,
`core/mouse_hook_base.py`), the delta-accumulation and cooldown machinery
(`_accumulate_gesture_delta`), the gesture-direction UI panel pattern in
`ui/qml/MousePage.qml` (now attached per-button instead of only to the HID gesture button),
and the existing action catalog (40+ actions, unchanged).

**New:** the event-tap arming mechanism itself — `OtherMouseDown`/`Up` handling in
`core/mouse_hook_macos.py` arms/releases a per-button gesture, decides click-vs-gesture on
release, and (on a tap) dispatches the button's own mapped click instead of a native replay
(macOS ignores synthetic clicks on button 3/4, so a native replay would be dead); plus the
12 namespaced `gesture_<owner>_<direction>` config binding keys, the `gesture_owners()` /
`gesture_bindings_for()` config helpers, the `supports_event_tap_gestures` capability flag,
and the per-owner routing in `core/engine.py` (`_make_owner_gesture_handler`, keyed on the
`gesture_owner` tag the kernel attaches rather than a namespaced event string).

## Testing

**Unit-tested (objc-free, runs in CI):**
- Direction decision logic (`decide_gesture`) — tap-vs-gesture, hold-floor boundary, deadzone,
  cross-axis ambiguity (`tests/test_event_tap_gesture.py`).
- Arming gate (`should_arm_gesture`) — first-held-wins, no-owners-configured off-switch.
- Config schema/migration for the 12 namespaced keys, `gesture_owners()`, `gesture_bindings_for()`
  (`tests/test_config_gestures.py`).
- Engine wiring: owner-gate (config-bound AND UI-enabled AND device-eligible), per-owner
  direction routing, no double-fire against the HID direction path (`tests/test_engine.py`).
- Two hardware-found regressions, now pinned: (1) the initial hook setup runs before the
  device connects, so arming must recompute on the HID-features-ready transition; (2) that
  recompute must reset bindings before re-registering, or a reconnect stacks a duplicate
  handler and the gesture action fires 2-3x.
- A fake-Quartz harness exercises the real macOS callback's arm/release/abort state machine,
  including that a tap dispatches the button's own (DOWN, UP) pair rather than any native
  CGEventPost replay.

**Hardware-verified (real MX Anywhere 2S, not automatable):**
- All 4 directions on back, forward, and middle fire their bound actions.
- A normal quick click of an armed button still performs its normal action — no misfire.
- Cursor does not drift during an active slide.
- No regression to MX Master HID++ gestures or normal remapping.

## Out of scope (this PR)

- Windows / Linux event-tap arming.
- Diagonal / 8-way gestures.
- Options+ config import / cloud sync.
