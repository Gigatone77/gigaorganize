import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
import os
from pathlib import Path
from gi.repository import Adw, Gio, Gtk, Gdk

from gigaorganize.window import MainWindow
from gigaorganize import APP_ID

_BASE_DIR = Path(__file__).resolve().parent.parent


class GigaOrganizeApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect("activate", self._on_activate)
        self.connect("startup", self._on_startup)

    def _on_startup(self, app):
        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)

        css_path = _BASE_DIR / "resources" / "style.css"
        if css_path.exists():
            css = Gtk.CssProvider()
            css.load_from_path(str(css_path))
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

    def _on_activate(self, app):
        win = self.props.active_window
        if win is None:
            win = MainWindow(application=app)
        win.present()
