import os
import time
from pathlib import Path

from gigaorganize.models import CacheEntry, LogEntry, CleanupScanResult
from gigaorganize.constants import CACHE_LOCATIONS, LOG_LOCATIONS


def _dir_size(path: Path) -> int:
    total = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat(follow_symlinks=False).st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += _dir_size(Path(entry.path))
            except (OSError, PermissionError):
                pass
    except (OSError, PermissionError):
        pass
    return total


def _file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except (OSError, PermissionError):
        return 0


def scan_caches(*, progress=None, cancellable=None) -> CleanupScanResult:
    start = time.monotonic()
    caches: list[CacheEntry] = []
    logs: list[LogEntry] = []
    total_cleanable = 0
    trash_size = 0
    errors: list[str] = []
    total_steps = len(CACHE_LOCATIONS) + len(LOG_LOCATIONS)

    for i, (name, paths, desc) in enumerate(CACHE_LOCATIONS):
        if cancellable and cancellable.is_cancelled():
            return CleanupScanResult(caches=[], logs=[], trash_size=0,
                                     total_cleanable=0, scan_time_seconds=0)
        if progress:
            progress({
                "phase": "caches",
                "current": i,
                "total": total_steps,
                "path": name,
            })

        size = 0
        existing_paths = []
        needs_root = False
        for p in paths:
            if p.exists():
                existing_paths.append(p)
                if os.access(p, os.W_OK):
                    size += _dir_size(p) if p.is_dir() else _file_size(p)
                else:
                    needs_root = True
                    size += _dir_size(p) if p.is_dir() else _file_size(p)

        if existing_paths:
            deletable = not needs_root
            caches.append(CacheEntry(
                name=name,
                paths=existing_paths,
                size_bytes=size,
                deletable=deletable,
                needs_root=needs_root,
                description=desc,
            ))
            if deletable:
                total_cleanable += size
            if name == "trash":
                trash_size = size

    for j, log_path in enumerate(LOG_LOCATIONS):
        if cancellable and cancellable.is_cancelled():
            break
        if progress:
            progress({
                "phase": "logs",
                "current": len(CACHE_LOCATIONS) + j,
                "total": total_steps,
                "path": str(log_path),
            })
        if log_path.exists():
            try:
                for entry in os.scandir(log_path):
                    try:
                        st = entry.stat()
                        if entry.is_file():
                            logs.append(LogEntry(
                                path=Path(entry.path),
                                size_bytes=st.st_size,
                                modified=st.st_mtime,
                                deletable=os.access(entry.path, os.W_OK),
                            ))
                    except (OSError, PermissionError):
                        pass
            except (OSError, PermissionError):
                pass

    logs.sort(key=lambda l: l.modified)

    if progress:
        progress({
            "phase": "done",
            "current": total_steps,
            "total": total_steps,
            "path": "",
        })

    return CleanupScanResult(
        caches=caches,
        logs=logs,
        trash_size=trash_size,
        total_cleanable=total_cleanable,
        scan_time_seconds=time.monotonic() - start,
        errors=errors,
    )
