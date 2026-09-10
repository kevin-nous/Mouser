# Mouser fork — backlog (Kevin)

Personal working copy at `/Users/kevin/Mouser`. Upstream = TomBadash/Mouser (MIT).

## Queued follow-up fixes (small, upstream-worthy)

### FIX-1 — Menu-bar icon perceptibly drops on left-click
- **Symptom:** clicking the NSStatusItem to open the window makes the menu-bar icon
  momentarily vanish. Especially jarring when the icon lives on a **secondary monitor**
  (window opens on primary; icon blinks out → reads as "app closed").
- **Root cause (confirmed):** left-click → `show_main_window` → window becomes visible →
  `_set_macos_activation_policy(regular=True)` (`main_qml.py:648`, driven at `:1144`/`:1166`).
  The Accessory→Regular activation-policy flip makes macOS rebuild the status bar, tearing
  down + re-adding the custom `NSStatusItem` (`_install_native_macos_status_item` `:692`).
  App does NOT quit (same PID survives the click — verified 2026-07-03).
- **Fix direction:** keep the status item stable across the policy flip — e.g. re-install /
  retain the NSStatusItem after promotion, or avoid the full teardown. Cosmetic, low-risk,
  self-contained in `main_qml.py`.
- **Ship:** small standalone PR, ideally alongside the gesture PR.

## Main feature
- `docs/prds/2026-07-03-mouser-slide-gestures.md` — per-button event-tap slide gestures.
