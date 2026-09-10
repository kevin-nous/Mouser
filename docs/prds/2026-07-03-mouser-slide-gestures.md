---
title: Event-Tap Slide Gestures (hold a button + slide → directional action), per-button
date: 2026-07-03
status: draft — decisions resolved; Phase 2 (grill-me) optional before decompose
repo: TomBadash/Mouser (MIT) — building on branch feat/event-tap-slide-gestures at /Users/kevin/Mouser
target_hardware: Logitech MX Anywhere 2S on macOS (Apple Silicon)
---

# Event-Tap Slide Gestures for Mouser (per-button)

## Problem

Mouser's **gesture** feature — hold a button, slide up/down/left/right, fire a different action per
direction — only *activates* when the device reports a diverted "gesture button held" event over
HID++. Only mice with a **dedicated hardware gesture button** (the MX Master thumb button) emit that.

The **MX Anywhere 2S has no such button**, so it gets **zero working gestures today**, even though its
macOS event tap already sees the side/middle buttons as ordinary mouse events and Mouser's
direction-detection engine is already built and tested. This is the top missed Options+ feature after
switching to Mouser.

## Solution

Add an **event-tap-driven gesture activation path** and make it **per-button**: for each non-primary
button (back / forward / middle), the user can turn on "gesture mode" and bind an action to each of the
four directions. Holding a gesture-enabled button and sliding past a deadzone runs Mouser's existing
direction engine and fires the bound action; a quick click with no slide still performs the button's
normal (remapped) function. Reuses ~80% of the existing gesture code and **avoids the HID++ remap
path entirely** (the path that fails on some devices — issue #187). v1 ships on macOS for the 2S; the
design generalises to any gesture-button-less mouse and to Windows/Linux later.

## Decisions (all confirmed by the user 2026-07-03 unless marked)

| ID | Decision | Resolution |
|----|----------|------------|
| **D1** | Which buttons can own gestures | **Per-button**: every non-primary button (back, forward, middle) can independently enable gesture mode with its own 4 direction bindings. *(Primary left/right click excluded — deferring them would break normal clicking. Assumed boundary; see OQ-A.)* |
| **D2** | Button behavior | **Dual-mode**: quick tap = the button's normal/remapped action; hold + slide = gesture. ✅ |
| **D3** | Direction set | 4 cardinal (up/down/left/right). No diagonals in v1. |
| **D4** | What arms a gesture | Slide **past deadzone** while held, gated by a **very short hold floor (~60–100 ms, tunable)** so a fast click with a hair of drift never misfires. Direction commits on release. ✅ |
| **D5** | Actions per direction | Chosen **in the UI**, per direction per button, from Mouser's existing action catalog (40+). ✅ |
| **D6** | Capability model | New **"event-tap gesture button"** kind. Do NOT abuse `gesture_cids`; relax the `gesture_directions` gate so an event-tap owner offers 4 directions without a device RawXY flag. |
| **D7** | Motion source | macOS **event-tap deltas** (`OtherMouseDragged`) while active — reuse `_accumulate_gesture_delta(..., "event_tap")`. |
| **D8** | Cursor during gesture | **Freeze** the pointer while a gesture is active (no cursor drift while sliding). ✅ |
| **D9** | Platform scope v1 | **macOS only**, tested on the real 2S. Design kept general. |
| **D10** | UI | Per eligible button: a "gesture mode" toggle + a 4-direction binding panel (reuse the existing gesture-direction panel, attached to the chosen button). Add a gesture hotspot to the 2S layout. |
| **D11** | Delivery | **Personal build first** (build + test on the 2S), **then tidy and PR upstream** to main. ✅ |
| **D12** | Working copy | Permanent clone created at **/Users/kevin/Mouser**, branch `feat/event-tap-slide-gestures`, remote `upstream` = TomBadash/Mouser (a personal GitHub fork becomes `origin` at PR time). ✅ |

## User Stories

- As a 2S owner, I hold my **forward** button and flick up/down/left/right, and each direction does a
  different thing (e.g. Mission Control / App Exposé / desktop switch) — chosen by me in the UI.
- I get the **same on my back and middle** buttons independently, each with its own four actions.
- A **quick tap** of any of those buttons still does its normal job — I don't lose the button.
- The **cursor doesn't drift** while I'm sliding out a gesture.

## Acceptance Criteria

- [ ] Per eligible button (back/forward/middle) a persisted config toggle enables gesture mode + stores 4 direction→action bindings in `config.json`.
- [ ] With gesture mode on for a button, **hold + slide > deadzone** fires the bound action for that direction on release.
- [ ] A **quick tap** of a gesture-enabled button performs its normal/remapped action, verified to reach the foreground app.
- [ ] A **hold with sub-deadzone movement** performs the normal action, not a random gesture.
- [ ] The very-short **hold floor** prevents a fast click-with-tiny-drag from firing a gesture (tune the ms on real hardware).
- [ ] Each eligible button shows an editable **4-direction binding panel** in the UI; bindings save and reload.
- [ ] **Cursor does not visibly move** during an active gesture (assert no net pointer delta reaches the OS).
- [ ] Buttons with gesture mode **off** fire immediately (no added latency); only gesture-enabled buttons defer their click to release.
- [ ] No regression to MX Master HID++ gestures (existing gesture tests stay green; HID path untouched).
- [ ] Degrades to "no gestures" (not a crash) when the event tap can't be created (no Accessibility).
- [ ] Feature **off by default** — no behavior change until a button opts in.

## Edge Cases

- Quick tap, no movement → normal action.
- Hold + micro-jitter under deadzone → normal action.
- Diagonal slide → existing cross-axis reject (0.35) picks the dominant axis; ambiguous → no-op (decide: no-op vs normal action).
- Very fast flick → still detected (accumulation already handles it).
- **Two gesture-enabled buttons held at once** → one active gesture at a time; first-held wins, second passes through (v1 rule).
- Gesture-enabled button is also an app shortcut (Forward in a browser) → fine; tap still = Forward, only hold+slide diverts.
- **App-profile switch mid-hold** → gesture state must survive a foreground-app change during one hold (don't reset `_gesture_active` on profile reload).
- **Middle button as a gesture owner** → middle-click is higher-stakes to defer (paste / open-in-new-tab); surface a gentle UI note when enabling gesture mode on middle.
- Injected replay click into an elevated/secure window → macOS may drop synthetic events (documented Mouser caveat); acknowledge as a known limitation.

## Out of Scope (v1)

- Windows / Linux activation paths (same gap; shared base wiring → clean follow-up).
- Diagonal / 8-way gestures.
- Gesture on scroll-tilt or DPI/mode-toggle buttons.
- Primary left/right click as a gesture owner.
- Re-plumbing the MX Master HID++ path (stays exactly as-is).
- Options+ config import / cloud sync.

## Technical Considerations

**Mechanism (confirmed from code):** direction is computed in software from accumulated deltas
(`core/mouse_hook_base.py:225-248`), but activation is gated on an HID++ notification
(`core/mouse_hook_macos.py:422-432` `_on_hid_gesture_down` is the sole `_gesture_active = True`
setter, called only from the HID listener `core/hid_gesture.py:1629-1647`). The event tap already
sees the 2S side/middle buttons (`core/mouse_hook_macos.py:329-346`) and the event-tap delta path
already runs once `_gesture_active` is set (`:289-327`). **Missing wire: nothing arms a gesture from
a normal button-down.**

**Primary change — `core/mouse_hook_macos.py`, `OtherMouseDown`/`OtherMouseUp` (`:329-366`):**
- On **down of a gesture-enabled button**: set `_gesture_active`, start tracking (mirror
  `_start_gesture_tracking` / `_on_hid_gesture_down` `:422-432`), **defer** the normal down.
- Enforce the **hold floor** (D4): only treat as a gesture if held ≥ floor AND slid > deadzone;
  otherwise on release synthesize the normal click.
- On **up**: `_finish_gesture_tracking`; gesture fired → swallow; else → synthesize normal click
  (mirror `should_click = not self._gesture_triggered` `:434-450`). Injection machinery exists
  (`_INJECTED_EVENT_MARKER` `:46`; synthetic CGEvents for scroll inversion `:83-133`).
- **Move branch unchanged** (`:289-327`); for D8, suppress net pointer delivery while active.

**Supporting changes:**
- **Config + engine:** per-button gesture-mode flag + 4 bindings; thread through
  `MouseEngine._setup_hooks` (`core/engine.py:98-142`) and `configure_gestures(...)` (`:109-116`).
- **Capability model** (`core/logi_devices.py:297-314, 685-695`): add the event-tap gesture kind so
  an event-tap-owned button advertises 4 directions without a device RawXY flag.
- **Catalog + layout** (`core/logi_device_catalog.py:191-203, 689-738`): add a gesture affordance to
  the 2S layout so the direction panel is reachable per button.
- **UI** (`ui/qml/MousePage.qml:1349-1545`): per eligible button, a gesture-mode toggle + the
  direction-binding panel.

**Per-button implications (from self-stress-test):**
- Only **gesture-enabled** buttons defer their click; normal-mode buttons stay instant → no global
  latency tax.
- **One active gesture at a time**; define two-button-hold precedence (first wins).
- **Middle-click** deferral is the highest-stakes; keep it opt-in with a note.

**Prior art:** OpenLogi (AprilNEA/OpenLogi, Rust) has the exact "pick which button owns the gesture
role" UX, but its gesture capture is *pending/unbuilt* — only the concept is liftable, not code.

**Build/test loop:** Python + QML; run from source (`python main_qml.py`) on the real 2S — unit tests
can't prove the tap-level UX. Add `tests/test_event_tap_gesture.py`.

## Open Questions

- **OQ-A:** Confirm the boundary "non-primary buttons only" (exclude primary left/right click). *(Assumed; low-risk.)*
- **OQ-tune:** Deadzone distance (px) and hold-floor (ms) — **calibrated during build on the 2S**, not blocking decisions.
- Everything else is resolved. Optional: run **`grill-me`** to adversarially harden before `/cc:decompose`.

---
*Next: (optional) grill-me stress-test → `/cc:decompose` → `/cc:build` (TDD) → test on the 2S → tidy → upstream PR.*
