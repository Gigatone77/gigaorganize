import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from gigaorganize.utils.format import format_size


class CategoryCard(Gtk.ListBoxRow):
    __gtype_name__ = "CategoryCard"

    def __init__(self, name: str, description: str, size_bytes: int,
                 needs_root: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.set_activatable(False)
        self._needs_root = needs_root

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.add_css_class("category-card")
        self.set_child(box)

        self._checkbox = Gtk.CheckButton()
        self._checkbox.set_active(not needs_root)
        self._checkbox.set_sensitive(not needs_root)
        box.append(self._checkbox)

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_hexpand(True)
        box.append(info_box)

        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        info_box.append(title_box)

        name_label = Gtk.Label(label=name)
        name_label.set_xalign(0)
        name_label.set_markup(f"<b>{name}</b>")
        title_box.append(name_label)

        if needs_root:
            root_badge = Gtk.Label(label="needs root")
            root_badge.add_css_class("caption")
            root_badge.add_css_class("dim-label")
            title_box.append(root_badge)

        desc_label = Gtk.Label(label=description, css_classes=["dim-label"])
        desc_label.set_xalign(0)
        info_box.append(desc_label)

        size_label = Gtk.Label(label=format_size(size_bytes))
        size_label.set_halign(Gtk.Align.END)
        size_label.set_valign(Gtk.Align.CENTER)
        box.append(size_label)

    @property
    def is_checked(self) -> bool:
        return self._checkbox.get_active()

    def set_checked(self, active: bool):
        self._checkbox.set_active(active)
