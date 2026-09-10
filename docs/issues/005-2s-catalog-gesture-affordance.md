---
id: 005
title: MX Anywhere 2S catalog + layout gesture affordance
status: ready
depends_on: []
effort: S
---

# MX Anywhere 2S catalog + layout gesture affordance

## What
Mark the MX Anywhere 2S as `supports_event_tap_gestures` and give its interactive hotspot layout a way
to reach the per-button gesture panel, so the UI (issue 006) can expose gesture mode on the 2S's
back/forward/middle buttons.

## Why
Today the 2S entry inherits MX-Master thumb gesture CIDs but its hotspot layout has **no gesture
hotspot** (`core/logi_device_catalog.py:191-203, 689-738`), so the gesture config panel is unreachable.
Satisfies D10 for the 2S.

## Technical Approach
- Set `supports_event_tap_gestures=True` on the 2S catalog entry (`:191-203`) — pairs with issue 002's
  spec flag.
- In the 2S hotspot layout (`:689-738`), ensure back/forward/middle hotspots can surface a
  "gesture mode" affordance. Prefer a per-button toggle in the button's own config panel (issue 006)
  over a separate "gesture" hotspot, since the 2S has no dedicated gesture button — confirm which the
  UI expects and keep them consistent.
- Do NOT point the 2S at MX-Master `gesture_cids` (leave the HID path inert for this device).

## Acceptance Criteria
- [ ] 2S spec reports `supports_event_tap_gestures=True`.
- [ ] The 2S's back/forward/middle are reachable as gesture owners in the capability model (with issue 002).
- [ ] No change to any MX Master layout.

## Test Plan
- Extend `tests/test_device_layouts.py` / `tests/test_logi_devices.py`: assert the 2S exposes the
  per-button gesture direction keys once 002+005 are in, and that MX Master layouts are byte-identical.
