import os
import shutil
from pathlib import Path

from gigaorganize.utils.format import format_size


def safe_trash(path: Path) -> bool:
    try:
        from send2trash import send2trash
        send2trash(str(path))
        return True
    except ImportError:
        try:
            trash_dir = Path.home() / ".local" / "share" / "Trash"
            files_dir = trash_dir / "files"
            info_dir = trash_dir / "info"
            files_dir.mkdir(parents=True, exist_ok=True)
            info_dir.mkdir(parents=True, exist_ok=True)

            dest = files_dir / path.name
            if dest.exists():
                base = path.stem
                ext = path.suffix
                i = 1
                while dest.exists():
                    dest = files_dir / f"{base} {i}{ext}"
                    i += 1

            shutil.move(str(path), str(dest))

            info_content = f"[Trash Info]\nPath={path}\nDeletionDate={Path().cwd()}\n"
            info_file = info_dir / (dest.name + ".trashinfo")
            with open(info_file, "w") as f:
                f.write(info_content)
            return True
        except Exception:
            return False
    except Exception:
        return False


RECOVERABLE_BIN = ".gigaorganize-trash"


def bin_path(path: Path, name: str) -> Path:
    """Return the recoverable-bin path for a given source path/name.

    The hidden bin lives next to the source (in-folder) so nothing is ever
    moved across volumes or permanently deleted.
    """
    path = Path(path)
    parent = path.parent if path.is_dir() else path.parent
    # Put the bin at the same level as the item being "cleaned" (its parent),
    # giving a stable, in-folder location for both files and directories.
    return parent / RECOVERABLE_BIN / (name or path.name)


def move_to_recoverable_bin(source: Path, name: str = "") -> bool:
    """Move `source` into a hidden, restorable bin WITHOUT deleting it.

    This is the no-delete alternative to shutil.rmtree / os.remove: the item is
    relocated to <parent>/.gigaorganize-trash/<name>/ so it can be restored by
    hand. The source's own empty parent directory (if any) is recreated so the
    original layout still exists.
    """
    try:
        source = Path(source)
        dest = bin_path(source, name)
        dest.mkdir(parents=True, exist_ok=True)
        # Move the contents (or the item itself) into the bin.
        if source.is_dir():
            for child in source.iterdir():
                target = dest / child.name
                if target.exists():
                    target = _unique_path(target)
                shutil.move(str(child), str(target))
            # Recreate the now-empty source dir so callers keep their layout.
            source.mkdir(parents=True, exist_ok=True)
        else:
            target = dest / source.name
            if target.exists():
                target = _unique_path(target)
            shutil.move(str(source), str(target))
        return True
    except Exception:
        return False


def _unique_path(path: Path) -> Path:
    base = path.stem
    ext = path.suffix
    i = 1
    while path.exists():
        path = path.with_name(f"{base} ({i}){ext}")
        i += 1
    return path


def open_file(path: Path) -> bool:
    try:
        from gi.repository import Gio
        Gio.AppInfo.launch_default_for_uri(
            f"file://{path}",
            None,
        )
        return True
    except Exception:
        return False


def reveal_in_manager(path: Path) -> bool:
    try:
        from gi.repository import Gio
        parent = path if path.is_dir() else path.parent
        Gio.AppInfo.launch_default_for_uri(
            f"file://{parent}",
            None,
        )
        return True
    except Exception:
        return False


def get_dir_size(path: Path) -> int:
    total = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat(follow_symlinks=False).st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += get_dir_size(Path(entry.path))
            except (OSError, PermissionError):
                pass
    except (OSError, PermissionError):
        pass
    return total
