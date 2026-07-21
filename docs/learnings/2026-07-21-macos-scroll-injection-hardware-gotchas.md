---
type: solution
category: integration-issues
date: 2026-07-21
slug: 2026-07-21-macos-scroll-injection-hardware-gotchas
title: "macOS scroll injection: hi-res wheels report continuous, and injected events need delta fields"
status: draft
source_skill: cc:learn
tags: [scroll, injection, quartz, macos, hi-res-wheel, smartshift, trackpad, event-tap, hardware]
---

# macOS scroll injection: two hardware-only gotchas

## Problem

The horizontal-scroll hold modifier passed every unit test and worked in no app.
On the real MX Anywhere 2S, holding the button and rolling the wheel did
**nothing** — twice, for two independent reasons, neither visible without the
physical device. Each cost ~an afternoon.

## Root Cause

### Bug 1 — the hi-res wheel reports as a trackpad (`is_continuous = 1`)

Mouser has `ignore_trackpad = True` (default) so it doesn't fight the MacBook
trackpad / Magic Mouse. The guard, near the top of the scroll handler:

```python
if self.ignore_trackpad:
    if Quartz.CGEventGetIntegerValueField(cg_event, 88):  # kCGScrollWheelEventIsContinuous
        return cg_event                                    # <-- bails here
```

The 2S's SmartShift / hi-res wheel emits its scroll events with
`is_continuous = 1` — **the same flag a trackpad sets**. So every wheel event
returned at the guard *before* the hold-modifier diversion (added lower down) ever
ran. Vertical scrolling still worked (the event passed through untouched); the new
horizontal logic was simply never reached. On-device logging showed `cont=1` on
every wheel event — the tell.

### Bug 2 — a bare injected scroll event moves nothing

The injector created the event and set only the wheel-count arg:

```python
event = Quartz.CGEventCreateScrollWheelEvent(None, 0, 2, 0, amount)  # amount as wheel2
Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
```

The diversion fired (confirmed: 318 injections logged), but the page never moved.
Apps read the scroll **delta fields** (`kCGScrollWheelEventPointDeltaAxis2`,
`...FixedPtDeltaAxis2`, `...DeltaAxis2`) — and `CGEventCreateScrollWheelEvent`'s
wheel arg alone doesn't populate them the way a real device event does. The
injected event carried a wheel count but empty delta fields → zero movement.

## Solution

**Bug 1:** run the hold-modifier diversion *before* the trackpad guard, gated so
it only acts when the modifier button is held (normal scrolling is untouched):

```python
if self._try_hscroll_modifier_divert(cg_event):   # gated on _gesture_active + owner
    return None
if self.ignore_trackpad:
    if ...is_continuous...: return cg_event
```

**Bug 2:** build the event the way the proven inversion path does — copy the
*source wheel event's* axis-1 delta fields onto axis-2, scaled, so the injected
event is structurally identical to the real one that already scrolls vertically:

```python
new = Quartz.CGEventCreateScrollWheelEvent(None, Quartz.kCGScrollEventUnitPixel, 2, 0, 0)
for f1, f2 in ((DeltaAxis1, DeltaAxis2), (FixedPtDeltaAxis1, FixedPtDeltaAxis2),
               (PointDeltaAxis1, PointDeltaAxis2)):
    v = Quartz.CGEventGetIntegerValueField(cg_event, f1)
    Quartz.CGEventSetIntegerValueField(new, f2, int(v * scale))
Quartz.CGEventPost(Quartz.kCGHIDEventTap, new)
```

`_try_hscroll_modifier_divert` / `_post_hscroll_from_vertical` in
`core/mouse_hook_macos.py`.

## Prevention

- **`is_continuous` is not "trackpad" — it's "hi-res".** Any feature that consumes
  or transforms *mouse-wheel* input on macOS must not assume a physical wheel is
  discrete. Modern Logitech wheels (SmartShift / MagSpeed) report continuous.
  Grep the risk: `grep -rn "IsContinuous\|is_continuous\|field, 88\|ignore_trackpad" core/`.
- **To inject scroll that apps actually honor, set the delta fields — don't rely on
  the `CGEventCreateScrollWheelEvent` wheel arg.** Reuse a real event's fields
  (cross-axis copy) when you have one; it's the only way to guarantee the shape
  matches. The working reference is `_post_inverted_scroll_event`.
- **These are hardware-only failure modes. A fake-Quartz unit harness that doesn't
  model `is_continuous` or real event *delivery* will pass while the feature is
  100% broken.** Two consequences:
  1. Add tests that set `is_continuous = 1` (regression: a held modifier must still
     divert; see `test_continuous_hires_wheel_still_diverts`).
  2. For any injection feature, **on-device E2E is not optional** — unit green ≠
     works. Budget a hardware pass before calling it done.
- **When "it fires but nothing happens," log the injected magnitude AND question the
  event *shape*, not just the trigger.** Bug 2 hid for a while because the diversion
  was obviously firing; the defect was one layer down, in what the event contained.

## Related

- [[2026-07-21-proportional-scroll-injection-rounding]] — the F1 rounding gotcha in the same injector
- Feature PRD: `docs/prds/2026-07-20-horizontal-scroll-modifier.md`; issues 008–013
- Fix commit: `4533ac3` (fix(macos): make hscroll modifier actually scroll on real 2S hardware)
