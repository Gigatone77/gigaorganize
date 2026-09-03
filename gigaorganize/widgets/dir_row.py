import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk, GObject
from pathlib import Path

from gigaorganize.utils.format import format_size, truncate


class DirRow(Adw.ActionRow):
    __gtype_name__ = "DirRow"

    def __init__(self, dir_path: Path, size: int, max_size: int,
                 file_count: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.dir_path = dir_path
        self.set_title(dir_path.name)
        self.set_subtitle(f"{file_count} files" if file_count else "")
        self.set_icon_name("folder")
        self.set_activatable(True)

        bar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        bar_bg = Gtk.DrawingArea()
        bar_bg.set_content_width(120)
        bar_bg.set_content_height(8)
        bar_bg.set_draw_func(self._draw_bar, size, max_size)
        bar_box.append(bar_bg)

        size_label = Gtk.Label(label=format_size(size), css_classes=["dim-label"])
        size_label.set_size_request(80, -1)
        size_label.set_xalign(1)
        bar_box.append(size_label)

        self.add_suffix(bar_box)

    def _draw_bar(self, area, cr, w, h, size, max_size):
        fraction = size / max_size if max_size > 0 else 0
        cr.set_source_rgba(0.3, 0.3, 0.3, 1)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        cr.set_source_rgba(0.2, 0.5, 0.8, 1)
        cr.rectangle(0, 0, w * fraction, h)
        cr.fill()
