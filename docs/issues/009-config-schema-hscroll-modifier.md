---
id: 009
title: Config schema — hscroll-modifier binding, speed factor, dedicated invert toggle
status: shipped
shipped_at: 2026-07-20
shipped_commit: a5933c07c5a3
depends_on: []
effort: S
# note: settings named hscroll_modifier_speed / hscroll_modifier_invert (prefixed to
# avoid confusion with the pre-existing invert_hscroll, which inverts tilt INPUT).
# status transitions owned by /cc:build (§ Closing the Issue)
---

# Config schema — hscroll-modifier binding, speed factor, dedicated invert toggle

## What
Add the persisted config surface for the feature, with no behavior wired yet:
1. A way to designate **which button** is the horizontal-scroll modifier — model as a new
   assignable pseudo-action `horizontal_scroll_hold` selectable for gesture-owner buttons
   (fits the existing "assign action to button" binding model; the engine will later
   interpret a button bound to it as the modifier).
2. `hscroll_speed` scale factor (float, default **1.0**).
3. `hscroll_invert` dedicated toggle (bool, default **False**) — independent of the
   existing vertical scroll-inversion setting.

Defaults must leave the 2S untouched (not bound by default).

## Why
PRD "Activation" (new assignable item, one button), "Direction & inversion" (dedicated
invert toggle, default off), "Horizontal scroll output" (speed factor default 1:1),
"Out of Scope" (2S defaults untouched, strictly opt-in).

## Acceptance Criteria
- [ ] `horizontal_scroll_hold` exists as an assignable action id (present in the actions /
      binding vocabulary), bindable to a button.
- [ ] `hscroll_speed` and `hscroll_invert` config keys exist with defaults `1.0` / `False`.
- [ ] All three round-trip through save/load unchanged.
- [ ] Default 2S config binds **none** of them (no behavior change for existing users).

## Technical Approach
- Files: `core/config.py` (defaults, `BUTTON_TO_EVENTS` / action vocabulary, new keys),
  and wherever config persistence is centralized.
- Follow the pattern of existing scroll/gesture config keys (e.g. tilt release ms
  `TILT_GESTURE_RELEASE_MS_DEFAULT`, `core/config.py:85`).
- No engine/hook behavior in this issue — schema + defaults + persistence only.

## Test Plan
- Unit: defaults are `hscroll_speed==1.0`, `hscroll_invert==False`, no modifier bound.
- Unit: set → save → load returns identical values for all three.
- Unit: `horizontal_scroll_hold` is a recognized assignable action id.
