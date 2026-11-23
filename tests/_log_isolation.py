"""Import main_qml without writing to the live Mouser log.

main_qml calls setup_logging() at import time, which attaches a rotating
handler on the real log directory (~/Library/Logs/Mouser on macOS) and
redirects stdout into it. Point the log directory at a temp dir for the
duration of the import so a test run never pollutes the live log.
"""
import os
import tempfile


def import_main_qml():
    """Return the main_qml module; raises what the import raises."""
    previous = os.environ.get("MOUSER_LOG_DIR")
    os.environ["MOUSER_LOG_DIR"] = tempfile.mkdtemp(prefix="mouser-test-logs-")
    try:
        import main_qml
        return main_qml
    finally:
        if previous is None:
            os.environ.pop("MOUSER_LOG_DIR", None)
        else:
            os.environ["MOUSER_LOG_DIR"] = previous
