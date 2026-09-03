import threading
from gi.repository import GLib
from typing import Callable


def run_async(
    func: Callable,
    *args,
    callback: Callable | None = None,
    error_callback: Callable | None = None,
):
    def _worker():
        try:
            result = func(*args)
            if callback:
                GLib.idle_add(callback, result)
        except Exception as e:
            if error_callback:
                GLib.idle_add(error_callback, e)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t


def run_scanner(
    scan_func: Callable,
    *args,
    progress_callback: Callable | None = None,
    done_callback: Callable | None = None,
    error_callback: Callable | None = None,
    cancellable=None,
    **kwargs,
):
    cancelled = threading.Event()

    class CancelProxy:
        def is_cancelled(self):
            return cancelled.is_set()

    proxy = CancelProxy()

    def _emit(info):
        if not cancelled.is_set() and progress_callback:
            GLib.idle_add(progress_callback, info)

    def _worker():
        try:
            result = scan_func(*args, progress=_emit, cancellable=proxy, **kwargs)
            if not cancelled.is_set():
                if done_callback:
                    GLib.idle_add(done_callback, result)
        except Exception as e:
            if not cancelled.is_set():
                if error_callback:
                    GLib.idle_add(error_callback, e)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()

    class Task:
        def cancel(self):
            cancelled.set()

    return Task()
