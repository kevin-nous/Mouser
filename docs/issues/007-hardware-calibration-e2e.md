---
id: 007
title: Hardware calibration + end-to-end verification on the real 2S
status: ready
depends_on: [003, 004, 006]
effort: M
---

# Hardware calibration + end-to-end verification on the real 2S

## What
Run Mouser from source on Kevin's actual MX Anywhere 2S, calibrate `gesture_deadzone` (px) and
`gesture_hold_floor_ms` to a good feel, and verify the full experience end-to-end. **Requires Kevin
present** to hold buttons and slide.

## Why
Unit tests can't prove the tap-level feel or that synthetic click replay reaches real apps. This is
the acceptance gate before tidy-up + upstream PR (PRD D11).

## Technical Approach
- `python main_qml.py` from `/Users/kevin/Mouser` (Accessibility already granted to the source
  interpreter, or grant on prompt). Ensure the packaged /Applications Mouser is quit first (single-
  instance guard + HID contention).
- Assign a distinctive test action to each of the 4 directions on forward (e.g. show a notification /
  4 different shortcuts) and confirm each fires.
- Tune loop: adjust `gesture_deadzone` + `gesture_hold_floor_ms` until a normal click never misfires a
  gesture and an intentional flick always registers. Record the chosen defaults back into
  `DEFAULT_CONFIG` (issue 001) if they differ.
- Repeat sanity on back and middle (watch middle-click deferral feel).
- Confirm cursor doesn't drift during a slide (D8) and dual-mode tap still clicks.

## Acceptance Criteria
- [ ] All 4 directions on forward fire their bound actions reliably on the real 2S.
- [ ] A normal quick click of a gesture-owner button still performs its normal action (no misfire) at the tuned settings.
- [ ] Cursor stays put during a gesture.
- [ ] Chosen `deadzone` / `hold_floor_ms` defaults recorded.
- [ ] No crash / no regression to normal remapping or MX Master behavior.

## Test Plan
- Manual, hardware-in-the-loop with Kevin. Capture the final tuned values + a short "how it feels"
  note in `docs/BACKLOG.md` or the PRD before opening the PR.

## Residual findings carried in from the adversarial review (2026-07-03) — address during calibration
- **LOW #1 — missed button-up freezes cursor up to `gesture_timeout_ms` (default 3000ms) before self-heal.**
  The timeout abort is correct but 3s is a long dead-cursor window on a dropped up. During calibration,
  consider a shorter dedicated freeze cap independent of the gesture timeout, or lower `gesture_timeout_ms`.
  (`core/mouse_hook_macos.py` move-swallow branch.)
- **LOW #2 — after a timeout-abort, a later real button-up flows to the normal up-path with no matching
  down** (its down was swallowed at arm time). Harmless / no stuck state; only the pathological dropped-up
  case. Keep an eye during hardware testing.
- **INFO — review the full 13-file diff, not just the "5 files" the fix report named.** `core/config.py`
  (+63: the 12 namespaced keys + migration + helpers) and `core/mouse_hook_base.py` (+62: `decide_gesture`,
  `should_arm_gesture`) carry substantial gesture logic and must be reviewed before the upstream PR.

## Pre-PR cleanup (noted earlier, do before opening upstream PR)
- Dead machinery: Wave-1's namespaced `gesture_<owner>_swipe_<dir>` events + their `BUTTON_TO_EVENTS`
  entries went unused (the kernel emits the generic event + `raw_data["gesture_owner"]` tag instead).
  Either remove the dead entries or simplify to one mechanism before the PR — a maintainer will flag it.
