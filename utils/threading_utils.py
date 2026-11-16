"""Thread execution helpers to prevent Tkinter UI freezes during computation."""

import threading
from typing import Callable, Any, Optional

def run_async(
    target_func: Callable[[], Any],
    on_success: Optional[Callable[[Any], None]] = None,
    on_error: Optional[Callable[[Exception], None]] = None
) -> threading.Thread:
    """Runs a CPU-intensive operation in a background thread and dispatches callbacks."""
    def worker():
        try:
            result = target_func()
            if on_success:
                on_success(result)
        except Exception as exc:
            if on_error:
                on_error(exc)
            else:
                raise exc

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread
