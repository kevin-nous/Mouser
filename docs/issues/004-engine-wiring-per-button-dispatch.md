---
id: 004
title: Engine wiring — per-owner configure_gestures + direction dispatch
status: ready
depends_on: [001, 002, 003]
effort: M
---

# Engine wiring — per-owner configure_gestures + direction dispatch

## What
Thread the per-button gesture config from `core/config.py` through the engine into the hook, and route
a detected `gesture_swipe_<dir>` to the **active owner's** namespaced binding
(`gesture_<owner>_<dir>`), so the right action fires for the button that was held.

## Why
Connects issues 001/002/003 into a working feature. Satisfies D5 (right action per direction per
button) and the "only gesture-enabled buttons defer" latency criterion.

## Technical Approach
- Extend `configure_gestures` (`core/mouse_hook_base.py:87-103` + contract
  `core/mouse_hook_contract.py:23`) to accept the **owner set** and **`hold_floor_ms`** (plus the
  existing thresholds). Store on the hook for the kernel (003) to read.
- In `MouseEngine._setup_hooks` (`core/engine.py:98-142`): compute owners via `gesture_owners(cfg)`
  (issue 001), pass `hold_floor_ms=settings.gesture_hold_floor_ms`, and register the per-owner
  direction bindings so that when the kernel emits `gesture_swipe_<dir>` for active owner X, the
  action mapped to `gesture_X_<dir>` runs.
  - Simplest routing: the kernel tags the emitted gesture event with the active owner; the engine
    registers callbacks keyed on `(owner, direction)` → action. Reuse `BUTTON_TO_EVENTS` /
    `get_active_mappings` (`core/config.py:54-59, 197-202`) with the namespaced keys from issue 001.
- Enable gestures on the hook only when `gesture_owners(cfg)` is non-empty (mirrors the current
  `enabled=any(...)` at `:109-111`).

## Acceptance Criteria
- [ ] With `gesture_forward_up=mission_control` mapped, holding forward + slide up fires Mission Control.
- [ ] Two owners with different bindings each fire their own action for the same physical direction.
- [ ] Zero owners ⇒ `configure_gestures(enabled=False)` and no deferral anywhere.
- [ ] MX Master HID gesture path still routes correctly (regression guard).

## Test Plan
- Extend `tests/test_engine.py`: build a config with per-owner bindings, run `_setup_hooks` against a
  fake hook, assert `configure_gestures` received the right owner set + hold_floor, and that a
  simulated `gesture_swipe_up` while "forward" is the active owner dispatches to the forward-up action.
