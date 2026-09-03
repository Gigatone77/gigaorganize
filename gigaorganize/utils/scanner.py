import os
import time
from pathlib import Path
from collections import defaultdict

from gigaorganize.models import DirEntry, DiskScanResult


def count_files_fast(root: Path, *, cancellable=None) -> int:
    count = 0
    for _, _, filenames in os.walk(root):
        if cancellable and cancellable.is_cancelled():
            return 0
        count += len(filenames)
    return count


def scan_disk_usage(root: Path, *, progress=None, cancellable=None) -> DiskScanResult:
    start = time.monotonic()

    if progress:
        progress({"phase": "counting", "current": 0, "total": 0, "path": str(root)})
    total_files = count_files_fast(root, cancellable=cancellable)
    if cancellable and cancellable.is_cancelled():
        return DiskScanResult(root=root, entries=[], total_size=0,
                              scan_time_seconds=0, files_scanned=0)

    entries: list[DirEntry] = []
    dir_sizes: dict[Path, int] = defaultdict(int)
    dir_file_counts: dict[Path, int] = defaultdict(int)
    dir_child_counts: dict[Path, int] = defaultdict(int)
    file_count = 0
    errors: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root):
        if cancellable and cancellable.is_cancelled():
            return DiskScanResult(root=root, entries=[], total_size=0,
                                  scan_time_seconds=0, files_scanned=file_count)
        dp = Path(dirpath)
        for fname in filenames:
            fp = dp / fname
            try:
                sz = fp.stat().st_size
                dir_sizes[dp] += sz
                dir_file_counts[dp] += 1
                file_count += 1
                parent = dp.parent
                while parent != dp:
                    dir_sizes[parent] += sz
                    dp = parent
                    parent = dp.parent
                dp = Path(dirpath)
                if progress and file_count % 25 == 0:
                    progress({
                        "phase": "scanning",
                        "current": file_count,
                        "total": total_files,
                        "path": str(fp),
                    })
            except (OSError, PermissionError) as e:
                errors.append(str(e))

        for d in dirnames:
            dir_child_counts[dp] += 1

    if progress:
        progress({
            "phase": "indexing",
            "current": total_files,
            "total": total_files,
            "path": "Building directory index...",
        })

    for dirpath in dir_sizes:
        p = Path(dirpath)
        largest = None
        largest_size = 0
        try:
            for entry in os.scandir(p):
                if entry.is_file():
                    try:
                        sz = entry.stat().st_size
                        if sz > largest_size:
                            largest_size = sz
                            largest = Path(entry.path)
                    except OSError:
                        pass
        except OSError:
            pass

        entries.append(DirEntry(
            path=p,
            size=dir_sizes[p],
            is_dir=True,
            file_count=dir_file_counts.get(p, 0),
            child_count=dir_child_counts.get(p, 0),
            largest_child=largest,
        ))

    entries.sort(key=lambda e: e.size, reverse=True)

    return DiskScanResult(
        root=root,
        entries=entries,
        total_size=dir_sizes.get(root, 0),
        scan_time_seconds=time.monotonic() - start,
        files_scanned=file_count,
        errors=errors,
    )
