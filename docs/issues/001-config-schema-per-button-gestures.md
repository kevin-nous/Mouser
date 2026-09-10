---
id: 001
title: Config schema for per-button slide gestures
status: ready
depends_on: []
effort: M
---

# Config schema for per-button slide gestures

## What
Extend `core/config.py` so each non-primary button (back / forward / middle) can independently own a
slide-gesture with its own four direction→action bindings, plus a global `gesture_hold_floor_ms`
tuning setting. Off by default; existing configs load unchanged.

## Why
Satisfies PRD D1 (per-button), D5 (UI-bound actions), D4 (hold-floor), and the "off by default /
no behavior change" acceptance criteria. Every other issue reads this schema.

## Technical Approach
- Today `mappings` is a flat `button_key → action_id` dict; gesture directions are FOUR global keys
  `gesture_left/right/up/down` (`core/config.py:38-42, 47-59`) fed by the single HID thumb button.
- **Namespace direction keys by owner** to go per-button — add these 12 keys to the constants:
  `gesture_{back,forward,middle}_{left,right,up,down}`. This reuses the existing flat-mappings model,
  `BUTTON_TO_EVENTS`, `get_active_mappings`, and dispatch untouched.
- Add matching human labels to the label map (`core/config.py:47-50` pattern).
- Add `settings.gesture_hold_floor_ms` (default e.g. 80) alongside the existing
  `gesture_threshold/deadzone/timeout_ms/cooldown_ms` settings.
- Add helper(s): `gesture_owners(cfg)` → set of owner buttons with ≥1 direction mapped ≠ "none";
  `gesture_bindings_for(cfg, owner)` → `{swipe_left: action_id, ...}`.
- **Back-compat:** if a legacy config carries the old global `gesture_left/right/up/down` keys, keep
  reading them (map them onto a default owner, or leave as the HID-thumb path's keys) — do NOT drop
  MX Master behavior. Document the chosen migration in a comment.
- Keep `DEFAULT_CONFIG` gesture-owner-free (feature off by default).

## Acceptance Criteria
- [ ] The 12 namespaced gesture direction keys + labels exist and validate.
- [ ] `settings.gesture_hold_floor_ms` exists with a sane default and is clamped ≥ 0.
- [ ] `gesture_owners()` / `gesture_bindings_for()` return correct sets/dicts for hand-built configs.
- [ ] A pre-existing config (no gesture-owner keys) loads with **no owners enabled** and no error.
- [ ] A legacy config with old global `gesture_*` keys still resolves to working bindings (no MX Master regression).

## Test Plan
- New `tests/test_config_gestures.py`: default config → zero owners; a config mapping
  `gesture_forward_up=mission_control` → `gesture_owners()=={"forward"}` and bindings dict correct;
  hold-floor default + clamp; legacy-key back-compat.
