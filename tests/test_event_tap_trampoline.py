"""The ctypes event-tap trampoline must pass events through without keeping a
reference to them (PyObjC's own tap trampoline pinned every CGEvent)."""

import ctypes
import sys
import unittest

if sys.platform == "darwin":
    try:
        import Quartz
        from core import mouse_hook_macos
    except ImportError:  # pragma: no cover - PyObjC missing
        Quartz = None
else:
    Quartz = None


if Quartz is not None:
    _cf = ctypes.CDLL(
        "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
    )
    for _name in ("CFRetain", "CFRelease", "CFGetRetainCount"):
        getattr(_cf, _name).argtypes = [ctypes.c_void_p]
    _cf.CFRetain.restype = ctypes.c_void_p
    _cf.CFRelease.restype = None
    _cf.CFGetRetainCount.restype = ctypes.c_long


@unittest.skipUnless(Quartz is not None, "macOS with PyObjC only")
class EventTapTrampolineTests(unittest.TestCase):
    def setUp(self):
        self.hook = mouse_hook_macos.MouseHook()
        # Hold the event by a raw C reference only, as CoreGraphics does when
        # it calls the tap: with no live PyObjC proxy, a proxy the trampoline
        # leaves alive shows up as an extra retain.
        event = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventMouseMoved, (10, 10), 0
        )
        self.ptr = event.__c_void_p__().value
        _cf.CFRetain(self.ptr)
        del event
        self.seen = []

    def tearDown(self):
        self.seen.clear()
        _cf.CFRelease(self.ptr)

    def _stub(self, result):
        def callback(proxy, event_type, cg_event, refcon):
            self.seen.append(cg_event)
            if result == "event":
                return cg_event
            if result == "raise":
                raise RuntimeError("boom")
            return None
        self.hook._event_tap_callback = callback

    def test_pass_through_returns_the_original_pointer(self):
        self._stub("event")
        out = self.hook._raw_event_tap_callback(
            None, Quartz.kCGEventMouseMoved, self.ptr, None
        )
        self.assertEqual(out, self.ptr)
        self.assertEqual(self.seen[0].__c_void_p__().value, self.ptr)

    def test_swallow_returns_null(self):
        self._stub("none")
        out = self.hook._raw_event_tap_callback(
            None, Quartz.kCGEventMouseMoved, self.ptr, None
        )
        self.assertIsNone(out)

    def test_callback_error_passes_the_event_through(self):
        self._stub("raise")
        out = self.hook._raw_event_tap_callback(
            None, Quartz.kCGEventMouseMoved, self.ptr, None
        )
        self.assertEqual(out, self.ptr)

    def test_null_event_reaches_the_callback_as_none(self):
        # Tap-disabled notifications may carry no event; the callback must
        # still run so it can re-enable the tap.
        self._stub("event")
        out = self.hook._raw_event_tap_callback(
            None, mouse_hook_macos._kCGEventTapDisabledByTimeout, None, None
        )
        self.assertEqual(self.seen, [None])
        self.assertIsNone(out)

    def test_pass_through_keeps_no_reference_to_the_event(self):
        self._stub("event")
        before = _cf.CFGetRetainCount(self.ptr)
        for _ in range(1000):
            self.hook._raw_event_tap_callback(
                None, Quartz.kCGEventMouseMoved, self.ptr, None
            )
        self.seen.clear()
        self.assertEqual(_cf.CFGetRetainCount(self.ptr), before)

    def test_ctypes_callback_round_trip(self):
        # Through a real ctypes callback object, as CoreGraphics calls it.
        self._stub("event")
        cb = mouse_hook_macos._TAP_CALLBACK(self.hook._raw_event_tap_callback)
        before = _cf.CFGetRetainCount(self.ptr)
        out = cb(None, Quartz.kCGEventMouseMoved, self.ptr, None)
        self.assertEqual(out, self.ptr)
        self.seen.clear()
        self.assertEqual(_cf.CFGetRetainCount(self.ptr), before)


if __name__ == "__main__":
    unittest.main()
