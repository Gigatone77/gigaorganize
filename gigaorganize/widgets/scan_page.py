import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw


class ScanPage(Adw.NavigationPage):
    __gtype_name__ = "ScanPage"

    def __init__(self, title: str = "Scan", **kwargs):
        super().__init__(**kwargs)
        self.set_title(title)
        self._task = None

        self._outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._outer.set_margin_top(12)
        self._outer.set_margin_bottom(12)
        self._outer.set_margin_start(12)
        self._outer.set_margin_end(12)
        self.set_child(self._outer)

        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False)
        header.set_show_start_title_buttons(False)
        self._outer.append(header)

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._controls = controls
        self._outer.append(controls)

        self._scan_button = Gtk.Button(label="Scan")
        self._scan_button.add_css_class("suggested-action")
        self._scan_button.connect("clicked", self._on_start_scan)
        controls.append(self._scan_button)

        self._cancel_button = Gtk.Button(label="Cancel")
        self._cancel_button.add_css_class("destructive-action")
        self._cancel_button.set_visible(False)
        self._cancel_button.connect("clicked", self._on_cancel)
        controls.append(self._cancel_button)

        self._status_label = Gtk.Label(label="", css_classes=["dim-label"])
        self._status_label.set_hexpand(True)
        self._status_label.set_xalign(0)
        self._status_label.set_ellipsize(3)
        controls.append(self._status_label)

        self._progress_bar = Gtk.ProgressBar()
        self._progress_bar.set_visible(False)
        self._progress_bar.set_hexpand(True)
        self._progress_bar.set_size_request(300, -1)
        self._outer.append(self._progress_bar)

        self._results_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._results_area.set_vexpand(True)
        self._outer.append(self._results_area)

    def _set_scanning(self, scanning: bool):
        self._scan_button.set_visible(not scanning)
        self._cancel_button.set_visible(scanning)
        self._progress_bar.set_visible(scanning)
        if not scanning:
            self._progress_bar.set_fraction(0.0)

    def _on_start_scan(self, *args):
        pass

    def _on_cancel(self, *args):
        if self._task:
            self._task.cancel()
        self._task = None
        self._set_scanning(False)
