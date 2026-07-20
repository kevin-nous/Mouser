---
id: 010
title: Hold-modifier kernel — first-threshold-crossing claim (wheel→hscroll vs motion→gesture)
status: shipped
shipped_at: 2026-07-20
shipped_commit: 63a619f60f34
depends_on: [008, 009]
effort: L
# status transitions owned by /cc:build (§ Closing the Issue)
---

# Hold-modifier kernel — first-threshold-crossing claim (wheel→hscroll vs motion→gesture)

## What
The heart of the feature. When the configured modifier button (issue 009) is held,
piggyback the existing event-tap gesture-owner hold-state and add first-threshold-crossing
disambiguation:
- Button-down → hold is **unclaimed**.
- **First** nonzero accumulated wheel delta → claim **horizontal-scroll mode**; route wheel
  deltas through the injector (issue 008); ignore mouse motion until release. The claiming
  delta itself is scrolled (not dropped).
- **First** cursor travel ≥ existing slide threshold → claim **slide-gesture mode**
  (unchanged behavior); ignore wheel until release.
- Neither before release → the button's **normal tap action** fires (unchanged).
- One mode per hold; no mixing. Vertical wheel is fully suppressed in horizontal-scroll mode
  (pure horizontal).

## Why
PRD "While the modifier button is held — first-threshold-crossing wins" + "Binding this does
NOT disable the button's existing slide gesture or normal tap action."

## Acceptance Criteria
- [ ] Hold modifier + roll wheel → horizontal scroll; no vertical leaks.
- [ ] Hold modifier + mouse flick (≥ slide threshold) → slide gesture fires; **no** hscroll.
- [ ] The first wheel delta both claims and scrolls (no dead first tick).
- [ ] Quick tap (neither input) → normal bound action fires.
- [ ] Once a mode is claimed, the other input is ignored until button release.
- [ ] Accepted misfire documented/tested: a wheel tick crossing before a slide-threshold
      crossing locks to hscroll (no motion-grace window).

## Technical Approach
- Files: `core/mouse_hook_macos.py` (claim state on the owner hold; scroll handler branch),
  `core/engine.py` (recognize the button bound to `horizontal_scroll_hold` as the modifier;
  pass it to the hook, mirroring how tilt/owner eligibility is wired ~116–138, 223–239).
- Reuse: `_gesture_owner` / `_gesture_owner_btn` hold (`:80–81`), owner gesture-move
  accumulation (~487–507), scroll handler (`kCGEventScrollWheel` ~629–674, axis read `:641`).
- Call issue 008's injector for output. Keep direction/scale/invert OUT of this issue
  (issue 011 owns them) — here, emit with scale 1.0 / default direction.

## Test Plan
- Unit/integration with synthesized events: down → wheel → assert hscroll injected, no vertical.
- down → motion → assert slide gesture path taken, no hscroll.
- down → up (nothing) → assert normal action.
- down → wheel → motion → assert motion ignored (still hscroll mode).
- down → motion → wheel → assert wheel ignored (still gesture mode).
