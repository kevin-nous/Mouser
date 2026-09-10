---
id: 002
title: Add "event-tap gesture button" capability kind
status: ready
depends_on: []
effort: M
---

# Add "event-tap gesture button" capability kind

## What
Introduce a capability concept for gestures driven by the macOS event tap (an ordinary button held +
mouse slide) that is **independent of the HID++ RawXY gesture control**, so a device without a
dedicated hardware gesture button (the MX Anywhere 2S) can still advertise the four gesture
directions per eligible button.

## Why
Satisfies PRD D6. Today `DeviceCapabilityInventory` strips all gesture keys unless the device exposes
a divertable gesture control (`gesture_click`) with RawXY (`gesture_directions`)
(`core/logi_devices.py:297-314, 685-695`). The 2S has neither, so gestures are removed at runtime.
The event-tap path needs neither — direction is computed in software.

## Technical Approach
- Add a device/spec flag, e.g. `supports_event_tap_gestures` (default False), on `LogiDeviceSpec`
  (`core/logi_devices.py`, near `gesture_cids:116`).
- In `DeviceCapabilityInventory.supported_buttons` / `.gesture_directions`
  (`core/logi_devices.py:297-314, 685-695`): allow the (owner-namespaced) gesture direction keys to
  survive when `supports_event_tap_gestures` is True, **without** requiring a divertable RawXY control.
- Keep the existing HID gesture path exactly as-is: when a real HID gesture control IS present, nothing
  changes. The two kinds are additive, not exclusive.
- Do NOT touch `gesture_cids` or repurpose a normal button's CID.
- `backend.supportsGestureDirections` (`ui/backend.py:603-605`) stays a platform check; per-device
  gating remains the capability narrowing here.

## Acceptance Criteria
- [ ] A spec with `supports_event_tap_gestures=True` and NO HID gesture control keeps the per-button
      gesture direction keys in `supported_buttons`.
- [ ] A spec with neither flag still strips gesture keys (unchanged behavior).
- [ ] A spec with a real HID gesture control is unaffected (MX Master regression guard).

## Test Plan
- Extend `tests/test_logi_devices.py`: three fixtures (event-tap-only, none, HID-gesture) asserting the
  gesture keys survive/strip correctly for each.
