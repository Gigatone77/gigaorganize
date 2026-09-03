import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw


class ProgressBanner(Gtk.Revealer):
    __gtype_name__ = "ProgressBanner"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.add_css_class("scan-overlay")
        self.set_child(box)

        self._status_label = Gtk.Label(label="Scanning...")
        self._status_label.set_xalign(0)
        box.append(self._status_label)

        self._progress_bar = Gtk.ProgressBar()
        self._progress_bar.set_show_text(True)
        box.append(self._progress_bar)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.END)
        box.append(btn_box)

        self._cancel_button = Gtk.Button(label="Cancel")
        self._cancel_button.add_css_class("destructive-action")
        btn_box.append(self._cancel_button)

    def set_progress(self, fraction: float, text: str = ""):
        self._progress_bar.set_fraction(fraction)
        if text:
            self._status_label.set_text(text)

    def set_cancel_handler(self, handler):
        self._cancel_button.connect("clicked", handler)

    def start(self, text: str = "Scanning..."):
        self._status_label.set_text(text)
        self._progress_bar.set_fraction(0.0)
        self.set_reveal_child(True)

    def stop(self):
        self.set_reveal_child(False)
