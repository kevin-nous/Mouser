---
id: 012
title: Guardrails S0–S3 — stale-hold clearing (no stuck horizontal mode)
status: ready
depends_on: [010]
effort: M
# status transitions owned by /cc:build (§ Closing the Issue)
---

# Guardrails S0–S3 — stale-hold clearing (no stuck horizontal mode)

## What
Ensure horizontal-scroll mode can never get stuck (which would silently kill vertical
scrolling). Clear the mode on any of:
- **S0** — modifier button's normal button-up (by construction: derive mode from the
  event-tap held-button state rather than a separate latch).
- **S1** — event-tap re-enable after OS disable (`kCGEventTapDisabledByTimeout` /
  `...ByUserInput`).
- **S2** — any other button or key going down.
- **S3** — focus change / app deactivate.

No idle-timeout watchdog (S4 rejected — a legit finger-down-not-yet-scrolling hold must not
be yanked).

## Why
PRD "Guardrails — stale-hold clearing (bundle: S0–S3)". A stuck horizontal-modifier is a
five-star "your app broke my mouse" bug; S1 is the #1 real dropper.

## Acceptance Criteria
- [ ] S0: button-up clears horizontal mode; next wheel event is vertical again.
- [ ] S1: simulated tap disable→re-enable mid-hold clears the mode (vertical restored
      without re-clicking the modifier).
- [ ] S2: any other button/key down while mode is active clears it.
- [ ] S3: app deactivate / focus change while held clears it.
- [ ] No timer-based clearing exists (an idle hold with no scroll is NOT cleared).

## Technical Approach
- Files: `core/mouse_hook_macos.py`.
- S0: derive-from-hold — `_reset_event_tap_gesture_state` (`:274–288`) already nulls the
  owner hold; hang mode-clear off the same teardown.
- S1: hook `_event_tap_callback` (`:450–464`) which handles the disable constants and calls
  `_abort_event_tap_gesture` → `_reset_event_tap_gesture_state`. Verified to exist.
- S2/S3: clear in the button/key-down path and on app-deactivate / focus-change
  notification.

## Test Plan
- Unit: enter hscroll mode, then invoke each of S0–S3's trigger → assert mode cleared and
  a subsequent wheel event is vertical.
- Unit: enter mode, advance simulated time with no events → assert mode still active (no S4).
