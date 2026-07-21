---
type: solution
category: correctness
date: 2026-07-21
slug: 2026-07-21-proportional-scroll-injection-rounding
title: "Proportional scroll injection: per-event int(round) silently drops fractional deltas"
status: draft
source_skill: cc:learn
tags: [scroll, injection, quartz, macos, rounding, proportional, event-tap, hscroll]
---

# Proportional scroll injection: per-event int(round) silently drops fractional deltas

## Problem

The horizontal-scroll hold modifier (issues 008–013) converts the vertical wheel
into horizontal scroll while a button is held, by injecting a synthetic scroll
event per wheel event. It felt fine at the default `hscroll_modifier_speed = 1.0`
but was **completely dead at `0.5`** — the wheel spun and nothing scrolled
sideways — and dropped input on hi-res / free-spin wheels.

The unit tests passed. The bug only surfaced in the adversarial `cc:review` pass,
because every test happened to use whole-number deltas.

## Root Cause

The injector rounded **each event independently** with no carry:

```python
amount = int(round(delta * scale))   # WRONG for proportional injection
if amount == 0:
    return False                     # ... but caller already swallowed the input
```

Two compounding facts made it a *dead* wheel, not just a coarse one:

1. **Banker's rounding.** `int(round(1 * 0.5))` == `int(round(0.5))` == **0** in
   Python (round-half-to-even). A normal ratchet notch is ~1.0, so at speed 0.5
   *every* notch rounded to 0.
2. **The caller had already committed.** The scroll diversion set
   `_hold_claim = "hscroll"` and did `return None` (swallowing the original
   vertical scroll) *before* calling the injector. So a rounded-to-0 event ate
   the input and produced no output — input consumed, zero motion.

Free-spin / high-resolution wheels emit a stream of sub-1.0 `FixedPtDeltaAxis1`
values; each rounded to 0 with no residual, so the fractions never summed into a
whole step.

The wrong assumption: *"round each delta to an int; small ones are negligible."*
For a proportional stream they are not negligible — they are the signal.

## Solution

Accumulate a fractional **residual** across events; only emit whole steps, and
carry the remainder:

```python
self._hscroll_residual += delta * scale
amount = int(self._hscroll_residual)   # truncate toward zero
if amount == 0:
    return False
self._hscroll_residual -= amount
```

Reset the residual when the hold ends (in the state-reset path) so it doesn't
leak across separate holds. `core/mouse_hook_macos.py::_inject_hscroll`, fixed in
the review-fix commit for this feature.

## Prevention

- **Rule:** any code that maps a *proportional input stream* to a *quantised
  output* (scroll lines/detents, pixel steps, integer API units) must keep a
  fractional residual — never `int(round(x))` per event. This applies to scroll
  injection, DPI/step scaling, animation stepping, rate limiters.
- **Test smell:** if every test for a scaling/injection path uses whole-number
  inputs, it cannot catch fractional-drop. Add a case with a **fractional scale**
  (e.g. 0.5) and assert that N sub-unit events produce ⌊N·scale⌋ outputs — proving
  the carry works, not just that whole numbers survive.
- **Watch the swallow-before-emit order:** when a handler consumes/blocks the
  original event *before* the emit can fail (return 0/None), a no-op emit becomes
  silent data loss. Either emit-then-swallow, or guarantee the emit can't no-op.
- **Grep:** `grep -rn "int(round(" core/` — audit each for a proportional stream.

## Related patterns from this feature (reusable techniques)

- **`_hold_claim` first-threshold-crossing kernel.** When one held control must
  disambiguate between two continuous inputs (wheel vs mouse-motion), a single
  latch — `None → "hscroll" | "gesture"`, set by whichever input crosses its
  threshold first, and reset on release/abort/arm — is a clean, testable state
  machine. Each site is gated `_gesture_active and _gesture_owner == owner`, so a
  `None` owner can never misfire. The loser is ignored until release.
- **Fake-Quartz test seam.** `core.mouse_hook_macos` is exercised objc-free by
  importing it against a minimal fake `Quartz`/`objc` in `sys.modules`
  (`tests/test_event_tap_gesture.py::_load_mouse_hook_macos`). Driving real
  `_event_tap_callback` with synthetic `_FakeCGEvent`s tests the actual kernel
  logic on any machine. Note: a fake missing a symbol (e.g.
  `CGEventCreateScrollWheelEvent`) must be added in the test's setUp, and every
  in-process fake hook must implement new hook-interface methods
  (`configure_hscroll_modifier`, `reset_hscroll_hold`) or unrelated engine tests
  break at `_setup_hooks`.

## Related

- Feature PRD: `docs/prds/2026-07-20-horizontal-scroll-modifier.md`
- Issues: `docs/issues/008`–`013`
- Review finding F1 (HIGH), F2/F3 — fixed in the same branch.
