---
id: 006
title: QML UI — per-button gesture toggle + 4-direction binding panel
status: ready
depends_on: [001, 005]
effort: L
---

# QML UI — per-button gesture toggle + 4-direction binding panel

## What
In the mouse config UI, each eligible button (back/forward/middle) gets a "Gesture mode" toggle and,
when on, a four-direction binding panel (up/down/left/right → pick any action). Wire it to the
namespaced config keys from issue 001 via `ui/backend.py`.

## Why
Satisfies D5 + D10: the user selects, in the UI, what each direction on each button does. Without this
the feature isn't usable.

## Technical Approach
- Reuse the existing gesture-direction panel (`ui/qml/MousePage.qml:1349-1545`) — today it's only
  reachable via the MX Master "gesture" hotspot. Generalize it to attach to whichever button is
  selected, reading/writing the `gesture_<owner>_<dir>` keys.
- Add a per-button "Gesture mode" toggle; when off, the button shows its normal single-action mapping;
  when on, show the 4-direction panel.
- `ui/backend.py`: expose get/set for the namespaced gesture bindings + the per-button enabled flag +
  `gesture_hold_floor_ms`; emit `settingsChanged` so the engine re-runs `_setup_hooks`.
- For the **middle** button, show the PRD's gentle note that middle-click is deferred while gesture
  mode is on.
- Gate visibility on the device capability (issue 002/005) so non-eligible devices don't show it.

## Acceptance Criteria
- [ ] Each eligible button shows a Gesture-mode toggle; toggling persists to config.
- [ ] With it on, 4 direction slots are editable and bind to any action; saved + reloaded correctly.
- [ ] Turning it off restores the button's normal single-action mapping (no lost data on toggle).
- [ ] Middle-button gesture mode surfaces the deferral note.
- [ ] Panel hidden on devices without `supports_event_tap_gestures` / HID gesture.

## Test Plan
- `ui/backend.py` logic unit-tested (`tests/test_backend.py`): set/get round-trip of namespaced
  bindings + enabled flag + hold_floor; `settingsChanged` emitted.
- QML itself verified in the hardware run (issue 007) — no headless QML test harness in-repo.
