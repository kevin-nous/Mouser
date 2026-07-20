---
id: 011
title: Direction default, dedicated invert toggle (no double-invert), speed factor
status: ready
depends_on: [010]
effort: M
# status transitions owned by /cc:build (§ Closing the Issue)
---

# Direction default, dedicated invert toggle (no double-invert), speed factor

## What
Apply the direction/scale semantics to the horizontal output produced by the kernel
(issue 010):
- Default mapping: wheel **up → content scrolls left**; down → right.
- Apply `hscroll_speed` (issue 009) as a multiplier.
- Apply `hscroll_invert` (issue 009) defined by **observable final direction** — it must NOT
  be a raw sign-flip stacked on macOS's natural-scroll transform (would double-invert).
  Account for the existing inversion path so the observed direction matches the toggle's
  promise for both natural-scrolling-on and -off users.

## Why
PRD "Direction & inversion" + the Implementation directive flagging the natural-scroll
rationale as inference (validate observed direction empirically).

## Acceptance Criteria
- [ ] Default (invert off): wheel-up scrolls content left, wheel-down right.
- [ ] `hscroll_invert == True` reverses the observed direction.
- [ ] Observed direction is correct with macOS "natural scrolling" both ON and OFF — no
      double-inversion in either state.
- [ ] `hscroll_speed` scales output magnitude; `1.0` is 1:1; larger = faster; no clamp.

## Technical Approach
- Files: `core/mouse_hook_macos.py` (direction/scale/invert applied at the injection call
  site from issue 010).
- Reference the inversion machinery `_post_inverted_scroll_event` / `_SCROLL_INVERT_MARKER`
  (`:108–158`) to decide whether the toggle routes through inversion or negates delta, such
  that the *observable* result is single-inverted.
- **Empirical check required:** verify on a machine with natural scrolling ON that the
  toggle produces the promised direction (the "injected events don't inherit natural
  scrolling" premise is a hypothesis — confirm the actual behavior during build).

## Test Plan
- Unit: sign of injected delta for (up, invert off) vs (up, invert on).
- Unit: speed factor 2.0 → double magnitude; 1.0 → unchanged.
- Manual/hardware: natural-scroll ON and OFF each yield the promised observable direction
  (documented result recorded in issue 013's E2E notes).
