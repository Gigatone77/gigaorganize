import time
from pathlib import Path


def clear_children(widget):
    child = widget.get_first_child()
    while child:
        next_child = child.get_next_sibling()
        widget.remove(child)
        child = next_child


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    for unit in ("KiB", "MiB", "GiB", "TiB", "PiB"):
        size_bytes /= 1024
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
    return f"{size_bytes:.1f} EiB"


def format_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.0f}s"


def format_date(timestamp: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp))


def truncate_path(path: Path, max_len: int = 40) -> str:
    s = str(path)
    if len(s) <= max_len:
        return s
    parts = path.parts
    if len(parts) <= 2:
        return s[:max_len - 3] + "..."
    return str(Path(parts[0]) / "..." / parts[-1])


def truncate(text: str, max_len: int = 30) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
