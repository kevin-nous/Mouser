"""Import main_qml without writing to the live Mouser log.

main_qml calls setup_logging() at import time, which attaches a rotating
handler on the real log directory (~/Library/Logs/Mouser on macOS) and
redirects stdout into it. Point the log directory at a temp dir for the
duration of the import so a test run never pollutes the live log.
"""
import atexit
import os
import shutil
import sys
import tempfile

_TEST_LOG_DIR = None


def import_main_qml():
    """Return the main_qml module; raises what the import raises."""
    global _TEST_LOG_DIR
    if "main_qml" in sys.modules:
        return sys.modules["main_qml"]
    if _TEST_LOG_DIR is None:
        _TEST_LOG_DIR = tempfile.mkdtemp(prefix="mouser-test-logs-")
        atexit.register(shutil.rmtree, _TEST_LOG_DIR, ignore_errors=True)
    previous = os.environ.get("MOUSER_LOG_DIR")
    os.environ["MOUSER_LOG_DIR"] = _TEST_LOG_DIR
    try:
        import main_qml
        return main_qml
    finally:
        if previous is None:
            os.environ.pop("MOUSER_LOG_DIR", None)
        else:
            os.environ["MOUSER_LOG_DIR"] = previous
