---
id: 013
title: UI surface + macOS/device gate + localization + hardware E2E
status: ready
depends_on: [009, 011, 012]
effort: L
# status transitions owned by /cc:build (§ Closing the Issue)
---

# UI surface + macOS/device gate + localization + hardware E2E

> **Build status (2026-07-20): PARTIAL — status stays `ready`.**
> Done + tested: backend `hscrollModifierEligible` gate, `hscrollModifierSpeed`/
> `hscrollModifierInvert` properties + persisting setters (5 backend tests); the
> invert toggle in `ui/qml/ScrollPage.qml` (gated, offscreen-compile-validated);
> en/zh-CN/zh-TW locale keys.
> Open: (1) speed-factor **slider** UI (setter exists, no control yet);
> (2) per-button action-picker hiding of `horizontal_scroll_hold` — functionally
> safe today (the engine won't arm the modifier on an ineligible device/platform),
> just not visually hidden per-button; (3) **hardware E2E on the real 2S**,
> including calibrating `_HSCROLL_DIRECTION_SIGN` (mouse_hook_macos.py) for the
> PRD default "wheel up → content left", and confirming no double-inversion under
> macOS natural scrolling. These need the physical device and a running app.

## What
Expose the feature in the app and gate it correctly, then verify end-to-end on the real 2S:
- Remap UI: the new "Horizontal scroll (hold)" assignable item for gesture-owner buttons,
  a dedicated horizontal invert toggle, and a horizontal-scroll speed control.
- **Gate:** the item/controls appear **only** when `platform == macOS` AND the device
  exposes event-tap gesture owners — absent on Windows/Linux and on ineligible devices.
- Localization strings (reuse existing `mouse.horizontal_scroll`).
- Hardware E2E on the physical MX Anywhere 2S.

## Why
PRD acceptance criteria: gated availability, invert toggle + speed control present and
persisting, localized; and the overall "produces horizontal scrolling in a real app" +
"vertical unchanged for non-users" verification.

## Acceptance Criteria
- [ ] The assignable item + invert toggle + speed control appear in the remap UI only on
      macOS + event-tap-gesture-owner devices; absent otherwise.
- [ ] Binding it and holding + rolling scrolls horizontally in a real app (wide table /
      timeline / browser with a horizontal scrollbar).
- [ ] Releasing restores vertical scrolling on the next wheel event.
- [ ] Invert toggle and speed control persist and take effect live.
- [ ] Tilt while held still fires tilt's own binding (browser back/forward) — unchanged.
- [ ] Vertical scrolling for users who never bind the modifier is unchanged (no regression).
- [ ] Direction correct on this machine for the tester's natural-scroll setting (record the
      observed result for issue 011's empirical check).

## Technical Approach
- Files: `ui/qml/MousePage.qml`, `ui/qml/ScrollPage.qml`, `ui/backend.py` (new properties +
  setters, mirror `tiltGestureEligibleOwners` ~565–573, `tiltGestureOwnerBindings`
  ~1508–1552), `ui/locale_manager.py` (strings exist at `:46`, `:690–692`).
- Gate: mirror `_gate_owner_eligibility` (`core/engine.py:116–138`) + the
  `supports_event_tap_gestures` catalog flag (`core/logi_device_catalog.py:222–239`).

## Test Plan
- UI/gate: on macOS+2S the controls render; simulate a non-macOS / ineligible device →
  controls absent.
- Persistence: set invert + speed via UI → reload → values retained.
- Hardware E2E: manual run-through of every acceptance criterion on the real 2S; record
  the natural-scroll direction result.
