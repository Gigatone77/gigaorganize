import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw
from pathlib import Path

from gigaorganize.utils.format import format_size, truncate_path


class FileRow(Adw.ActionRow):
    __gtype_name__ = "FileRow"

    def __init__(self, file_path: Path, size: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.file_path = file_path
        self.set_title(file_path.name)
        self.set_subtitle(truncate_path(file_path.parent, 50))
        self.set_icon_name(self._get_icon(file_path))

        size_label = Gtk.Label(label=format_size(size), css_classes=["dim-label"])
        self.add_suffix(size_label)

    def _get_icon(self, path: Path) -> str:
        ext = path.suffix.lower()
        icon_map = {
            ".pdf": "x-office-document",
            ".doc": "x-office-document", ".docx": "x-office-document",
            ".txt": "text-x-generic", ".md": "text-x-generic",
            ".jpg": "image-x-generic", ".jpeg": "image-x-generic",
            ".png": "image-x-generic", ".gif": "image-x-generic",
            ".svg": "image-x-generic",
            ".mp4": "video-x-generic", ".mkv": "video-x-generic",
            ".avi": "video-x-generic",
            ".mp3": "audio-x-generic", ".flac": "audio-x-generic",
            ".ogg": "audio-x-generic",
            ".zip": "application-x-archive", ".tar": "application-x-archive",
            ".gz": "application-x-archive", ".7z": "application-x-archive",
            ".py": "text-x-python", ".js": "text-x-javascript",
            ".sh": "application-x-executable",
        }
        return icon_map.get(ext, "text-x-generic")
