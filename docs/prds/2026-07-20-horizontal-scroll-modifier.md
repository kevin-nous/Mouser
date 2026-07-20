---
title: Horizontal Scroll via Hold Modifier (macOS)
date: 2026-07-20
status: draft
---

# Horizontal Scroll via Hold Modifier (macOS)

## Problem

Mice without a dedicated horizontal-scroll control — notably the **MX Anywhere 2S**
— have no comfortable way to scroll sideways. The 2S wheel *can* tilt left/right, but
that tilt is already spoken for (default: browser back/forward) and is being reserved
for the tilt slide-gesture feature; overloading it with horizontal scroll collides
head-on with that feature (see Out of Scope). Meanwhile Mouser has **no bindable action
that emits horizontal scroll at all** — the low-level injectors exist on every platform
but nothing user-facing ever calls them for horizontal output. So a user who lives in
wide content (timelines, spreadsheets, Figma, code with long lines) simply cannot scroll
horizontally from the mouse.

## Solution

Add a **momentary hold modifier**: the user binds a new *"Horizontal scroll (hold)"*
item to **one** button of their choice (an event-tap gesture-owner button — back /
forward / middle on the 2S). While that button is physically held, rolling the normal
vertical wheel emits **proportional horizontal scroll** instead of vertical — like a
real mouse's thumb wheel, streaming pixel-for-pixel with no debounce and no velocity
cap. Release the button and the wheel returns to normal vertical scrolling. This reuses
the existing macOS event-tap per-button hold-state (the same machinery behind event-tap
slide gestures), so it adds an interaction concept, not a new input-tracking subsystem.
**macOS only for v1.**

## User Stories

- As an MX Anywhere 2S user, I want to hold a button and roll the wheel to scroll a
  wide timeline sideways, so that I can navigate horizontal content without a thumb wheel.
- As a user, I want to pick *which* button is my horizontal-scroll modifier, so that it
  fits my grip and leaves my other buttons alone.
- As a user with "natural scrolling" preferences, I want a dedicated invert toggle for
  horizontal scroll, so that sideways direction feels right regardless of my vertical setting.
- As a user, I want the modifier to never get "stuck," so that my normal vertical
  scrolling is never silently broken.

## Behavior Specification

### Activation
- A new assignable item, **"Horizontal scroll (hold)"**, is bound to exactly **one**
  button via the existing remap UI. Only that button becomes the modifier.
- The eligible buttons are the device's **event-tap gesture-owner** buttons (back /
  forward / middle on the 2S) — the buttons whose held-state the event tap already tracks.
- Activation is **momentary**: horizontal mode is live only while the button is held.
  There is no toggle/latch.
- **Binding this does NOT disable the button's existing slide gesture or normal tap
  action** — all three coexist on the one button, disambiguated by first-threshold-crossing
  (below): quick tap → normal action; hold + **mouse flick** → slide gesture (unchanged);
  hold + **wheel roll** → horizontal scroll. The button keeps everything it had; horizontal
  scroll is added on top of the same hold.

### While the modifier button is held — first-threshold-crossing wins
The held button is "unclaimed" on button-down. The **first** secondary input to cross
its own threshold claims the hold for the remainder of that press:
- **Any nonzero accumulated wheel delta** → claims **horizontal-scroll mode**. (Expressed
  in delta units, **not** detents — SmartShift free-spin is detent-less, and free-spin is a
  primary target case; a detent-based threshold would be undefined there.) Mouse motion is
  ignored until release. The wheel emits **pure horizontal** scroll (no vertical leaks), and
  **the claiming delta itself is emitted as horizontal scroll** — it is used to decide *and*
  scrolled, never consumed/dropped (a lost first tick would feel like a dead spot).
- **Cursor travel ≥ the existing slide-gesture threshold** → claims **slide-gesture
  mode** (unchanged behavior). Wheel input is ignored until release.
- **Neither before release** → the button's **normal bound tap action** fires (unchanged).

Only one mode per hold; no mixing. **Accepted misfire:** if a stray wheel tick crosses
the wheel threshold a hair before an intended flick crosses the motion threshold, the
hold locks to horizontal-scroll and the gesture does not fire. This is accepted (no
motion-grace window in v1).

### Horizontal scroll output — proportional, uncapped
- Wheel deltas are passed **proportionally** to the horizontal injector — no debounce,
  no threshold accumulation, no cooldown. It must feel like a real mouse.
- **No velocity cap.** SmartShift free-spin flings horizontally by design.
- A single **"horizontal scroll speed"** scale factor is exposed (default **1:1** with
  the vertical wheel). Deltas are multiplied by this factor before injection.

### Direction & inversion
- **Default mapping:** wheel **up → content scrolls left**; wheel down → right.
- A **dedicated** horizontal-scroll invert toggle (separate from the vertical/existing
  scroll-inversion setting), **default off**.
- The toggle is defined by the **observable final scroll direction** — it must not be a
  raw sign-flip stacked on top of macOS's natural-scroll transform, or it will
  double-invert. Implementation must route through / account for the existing inversion
  handling so a natural-scrolling user gets the direction the toggle promises.
- Consequence accepted: because the toggle is independent, horizontal and vertical
  direction *can* disagree for a given user. That is the intended cost of independent control.

### Guardrails — stale-hold clearing (bundle: S0–S3)
Horizontal-scroll mode is cleared (returned to normal vertical) on **any** of:
- **S0** — the modifier button's normal button-up (the 99% path).
- **S1** — event-tap **re-enable** after the OS disables it
  (`kCGEventTapDisabledByTimeout` / `...ByUserInput`).
- **S2** — **any other button or key going down.**
- **S3** — **focus change / app deactivate.**

No idle-timeout watchdog (S4 rejected): a legitimate finger-down-not-yet-scrolling hold
must not be yanked out from under the user. Preferred implementation: derive
horizontal-mode from the event tap's existing held-button state rather than a separate
latch, so button-up clears it by construction; layer S1–S3 as explicit force-clears on
top because a stuck horizontal-modifier kills vertical scrolling (far worse symptom than
a stuck-but-invisible slide gesture).

## Acceptance Criteria

- [ ] A new "Horizontal scroll (hold)" assignable item is offered in the remap UI **only**
      when `platform == macOS` AND the device exposes event-tap gesture owners; it is
      **absent** on Windows/Linux and on devices without event-tap gesture owners.
- [ ] Binding it to a button and holding that button while rolling the wheel produces
      **horizontal** scrolling in a test app (e.g. a wide table / timeline / browser page
      with a horizontal scrollbar).
- [ ] Releasing the button restores normal **vertical** scrolling on the very next wheel event.
- [ ] Horizontal scroll is **proportional**: fast wheel motion (incl. SmartShift free-spin)
      produces fast horizontal motion; slow produces slow. No fixed step/debounce.
- [ ] With the modifier held, a qualifying **mouse motion first** produces the button's
      slide gesture (unchanged) and **no** horizontal scroll; a **wheel tick first**
      produces horizontal scroll and **no** gesture — for the same single hold.
- [ ] A quick tap of the modifier button (no wheel, no qualifying motion) still fires the
      button's normal bound action.
- [ ] The **first** wheel delta while held both claims horizontal mode **and** scrolls —
      no dropped/dead first tick.
- [ ] Tilting the wheel while the modifier is held fires **tilt's own binding** (default
      browser back/forward) — the modifier does not reroute tilt.
- [ ] Default direction: wheel-up scrolls content left; the dedicated invert toggle
      reverses it; the observed direction is correct for **both** natural-scrolling-on and
      -off users (no double-inversion).
- [ ] The "horizontal scroll speed" factor scales output; 1:1 is the default.
- [ ] Guardrail S0: button-up clears horizontal mode.
- [ ] Guardrail S1: simulating an event-tap disable/re-enable mid-hold clears horizontal
      mode (vertical scrolling is restored without re-clicking the modifier).
- [ ] Guardrail S2: pressing any other button while the modifier is "stuck on" clears it.
- [ ] Guardrail S3: switching focus to another app while held clears it.
- [ ] Vertical scrolling for users who never bind the modifier is **byte-for-byte
      unchanged** (no regression on the hot scroll path).

## Edge Cases

- **Dropped button-up under OS tap-disable** → covered by S1 (and S2/S3 as backstops).
- **Stray wheel tick during an intended gesture** → accepted misfire (locks to scroll).
- **SmartShift free-spin** → flings horizontally, uncapped (by design).
- **Natural scrolling on** → dedicated invert toggle must still yield the promised
  observable direction (no double-invert).
- **Modifier button also has a slide gesture bound** → both live on that one button;
  disambiguated by first-threshold-crossing. Concentrated (not spread) misfire, accepted.
- **Held across an app switch** → S3 clears the mode (exotic "scroll into another window
  while held" workflow is intentionally not supported).
- **User holds the modifier but never scrolls, then releases** → normal tap action fires;
  no watchdog interferes.
- **Wheel *tilt* while the modifier is held** → unchanged; tilt keeps its own binding
  (default browser back/forward). Tilt is a distinct physical input from wheel-roll and is
  intentionally **not** rerouted by the modifier. Documented so the "I was in scroll mode
  and a tilt fired browser-back" surprise is a known, accepted behavior rather than a bug.

## Out of Scope

- **Path B (tilt → horizontal scroll):** dropped. The 2S tilt pulse stream is consumed by
  the existing tilt slide-gesture feature; making tilt emit *proportional* horizontal
  scroll is mutually exclusive with tilt slide-gestures (can't time-share via tap/slide
  once proportional). Tilt keeps its current behavior (default browser back/forward).
- **Windows and Linux:** no Path A. Those hooks lack the per-button event-tap hold the 2S
  needs (their `_gesture_active` is HID-gesture-button-driven, which the 2S doesn't have).
  A future effort could build the equivalent hold-tracking there.
- **Toggle/latch activation:** momentary only.
- **Velocity cap / momentum smoothing:** not in v1.
- **Changing the 2S default mapping:** defaults untouched; horizontal scroll is strictly opt-in.
- **A per-app or per-direction sensitivity curve:** single global speed factor only.

## Technical Considerations

Existing patterns to follow / touch points (verified against the code):
- **New output action / injection:** the horizontal injector already exists —
  `inject_scroll(HWHEEL, ...)` in `core/key_simulator.py` (macOS: `CGEventCreateScroll
  WheelEvent(None, 0, 2, 0, delta)`). Today its only caller is the Windows re-injection
  path; v1 wires a macOS hold-path caller. Do **not** route horizontal output through
  `_make_hscroll_handler` (`core/engine.py` ~432–460) — that path is debounced
  (threshold + cooldown) and would destroy the proportional feel.
- **Held-state reuse:** piggyback the event-tap gesture-owner hold in
  `core/mouse_hook_macos.py` — the macOS-only fields `_gesture_owner` / `_gesture_owner_btn`
  (`:80–81`), whose macOS teardown is `_reset_event_tap_gesture_state` (`:274–288`; note
  `_finish_gesture_tracking` itself is a shared base-class method in
  `core/mouse_hook_base.py`, not macOS-specific — hook the macOS reset, not the base
  method), plus the owner gesture-move accumulation (~487–507). The scroll handler
  (`kCGEventScrollWheel`, ~629–674) reads wheel deltas (axis-2 horizontal via
  `kCGScrollWheelEventFixedPtDeltaAxis2`, `:641–642`) and is where the held+claimed branch
  converts vertical → horizontal.
- **Inversion:** account for the existing `_post_inverted_scroll_event` /
  `_SCROLL_INVERT_MARKER` path (`core/mouse_hook_macos.py` ~108–158) so the dedicated
  invert toggle produces the correct *observable* direction rather than double-inverting.
- **Tap re-enable guardrail (S1) — hook point verified to exist:**
  `_event_tap_callback` (`core/mouse_hook_macos.py:450–464`) already handles
  `kCGEventTapDisabledByTimeout` / `...ByUserInput` by calling `_abort_event_tap_gesture`
  then re-enabling the tap; `_reset_event_tap_gesture_state` (`:274–288`) nulls the owner
  hold-state. Force-clear horizontal mode from that same path.
- **Device/platform gate:** catalog entry `mx_anywhere_2s` sets
  `supports_event_tap_gestures: True` (`core/logi_device_catalog.py` ~222). Gate the new
  binding on macOS + event-tap-gesture-owner presence, mirroring how tilt-owner UI
  eligibility is gated (`ui/backend.py` `tiltGestureEligibleOwners` ~565–573;
  `core/engine.py` `_gate_owner_eligibility` ~116–138).
- **UI/config surface:** new binding item + dedicated invert toggle + speed factor need
  config keys, backend properties (`ui/backend.py`), and QML controls
  (`ui/qml/MousePage.qml` / `ScrollPage.qml`). Localization strings for
  `mouse.horizontal_scroll` already exist (`ui/locale_manager.py`).

### Implementation directives (verified facts, not open questions)
- **Mark injected events to avoid tap re-entry.** Re-injecting horizontal scroll as an
  axis-2 event will re-enter the event tap. Follow the existing inversion pattern: the
  inversion path stamps `_SCROLL_INVERT_MARKER` (`core/mouse_hook_macos.py:54, :131`) and
  short-circuits on re-entry at `:634`. Stamp the horizontal-scroll injection the same way
  and short-circuit it, or it will double-process.
- **The "natural scrolling" rationale is inference, not a code fact.** The code
  demonstrably self-inverts scroll (C4 confirmed), but no comment states *why* injected
  events need it. Treat "injected events don't inherit macOS natural scrolling" as the
  working hypothesis behind the dedicated invert toggle; validate the actual observed
  direction on a natural-scrolling machine during build rather than assuming the mechanism.

## Open Questions

_None._ All design decisions were resolved during discovery + stress-test. Remaining
items are implementation-verification tasks captured under **"Implementation directives"**
above, to be confirmed in `/cc:build`, not product decisions.
