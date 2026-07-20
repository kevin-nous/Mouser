---
id: 008
title: macOS proportional horizontal-scroll injection primitive (re-entry-safe)
status: ready
depends_on: []
effort: M
# status transitions owned by /cc:build (§ Closing the Issue)
---

# macOS proportional horizontal-scroll injection primitive (re-entry-safe)

## What
Add a single macOS function that injects a **proportional horizontal** scroll event
given a delta, using the existing `inject_scroll(HWHEEL, ...)` /
`CGEventCreateScrollWheelEvent(None, 0, 2, 0, delta)` path. The injected event MUST be
stamped with a marker (mirroring `_SCROLL_INVERT_MARKER`) and the scroll handler MUST
short-circuit on that marker so the re-injected event is not re-processed by our own tap.
No debounce, no threshold, no cooldown — the delta is passed straight through (× a scale
factor arg, default 1.0). This is the foundational output primitive; nothing user-facing
yet.

## Why
PRD "Solution" + "Horizontal scroll output — proportional, uncapped" + Implementation
directive "Mark injected events to avoid tap re-entry." There is currently **no** bindable
path that emits horizontal scroll (verified: `inject_scroll(HWHEEL)`'s only caller is the
Windows re-injection path).

## Acceptance Criteria
- [ ] A function (e.g. `_inject_hscroll(delta, scale=1.0)`) on the macOS hook injects a
      horizontal scroll event via axis-2 with `delta * scale`.
- [ ] The injected event carries a distinct marker (new constant, same mechanism as
      `_SCROLL_INVERT_MARKER`).
- [ ] The `kCGEventScrollWheel` handler short-circuits (returns/ignores) an event bearing
      that marker — no double-processing, no feedback loop.
- [ ] Passing delta `0` injects nothing (no-op).
- [ ] Proportionality: output delta scales linearly with input delta × scale (no clamp).

## Technical Approach
- Files: `core/mouse_hook_macos.py` (add the injector + marker + short-circuit),
  `core/key_simulator.py` (reuse existing `inject_scroll` HWHEEL branch, macOS `:759`).
- Pattern to mirror: `_post_inverted_scroll_event` / `_SCROLL_INVERT_MARKER`
  (`core/mouse_hook_macos.py:54, :108–158, :131`) and its re-entry short-circuit at `:634`.
- Do **not** route through `_make_hscroll_handler` (`core/engine.py:432–460`) — that path
  is debounced and would destroy proportional feel.

## Test Plan
- Unit: calling the injector builds a CGEvent with axis-2 delta == input × scale (mock/spy
  on the CGEvent creation).
- Unit: a marked event fed to the scroll handler is short-circuited (not dispatched).
- Edge: delta 0 → no event; large delta → passed through uncapped (no clamp applied).
