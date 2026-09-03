import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib
from pathlib import Path
from collections import defaultdict

from gigaorganize.widgets.scan_page import ScanPage
from gigaorganize.widgets.treemap import TreemapWidget
from gigaorganize.widgets.dir_row import DirRow
from gigaorganize.utils.thread import run_scanner
from gigaorganize.utils.scanner import scan_disk_usage
from gigaorganize.utils.format import format_size, format_duration, clear_children
from gigaorganize.models import DiskScanResult
from gigaorganize.constants import HOME


class DiskUsagePage(ScanPage):
    __gtype_name__ = "DiskUsagePage"

    def __init__(self, **kwargs):
        super().__init__(title="Disk Usage", **kwargs)
        self._results_area.set_visible(False)
        self._current_path = HOME
        self._path_history: list[Path] = []

        path_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._controls.insert_child_after(path_box, self._cancel_button)

        self._folder_button = Gtk.Button(label="Select Folder...")
        self._folder_button.connect("clicked", self._on_select_folder)
        path_box.append(self._folder_button)

        self._path_label = Gtk.Label(label=str(self._current_path))
        self._path_label.set_hexpand(True)
        self._path_label.set_xalign(0)
        self._path_label.set_ellipsize(3)
        path_box.append(self._path_label)

        self._back_button = Gtk.Button(label="Back")
        self._back_button.set_visible(False)
        self._back_button.connect("clicked", self._on_back)
        path_box.append(self._back_button)

        self._summary_label = Gtk.Label(label="", css_classes=["dim-label"])
        self._summary_label.set_xalign(0)
        self._outer.append(self._summary_label)

        self._notebook = Gtk.Notebook()
        self._notebook.set_vexpand(True)
        self._notebook.set_visible(False)
        self._outer.append(self._notebook)

        self._treemap = TreemapWidget()
        self._treemap.set_hexpand(True)
        self._treemap.set_vexpand(True)
        self._treemap.set_size_request(400, 300)
        self._treemap.set_activated_callback(self._on_treemap_click)
        self._notebook.append_page(self._treemap, Gtk.Label(label="Treemap"))

        self._bar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self._notebook.append_page(
            Gtk.ScrolledWindow(child=self._bar_box),
            Gtk.Label(label="Bar Chart")
        )

        self._entries_list = Gtk.ListBox()
        self._entries_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self._notebook.append_page(
            Gtk.ScrolledWindow(child=self._entries_list),
            Gtk.Label(label="Directory List")
        )

        self._result: DiskScanResult | None = None

    def _on_select_folder(self, *args):
        dialog = Gtk.FileDialog()
        dialog.set_title("Select folder to scan")
        folder = Gio.File.new_for_path(str(self._current_path))
        dialog.select_folder(self.get_root(), None, self._on_folder_selected, folder)

    def _on_folder_selected(self, dialog, result):
        try:
            file = dialog.select_folder_finish(result)
            if file:
                self._current_path = Path(file.get_path())
                self._path_label.set_text(str(self._current_path))
                self._on_start_scan()
        except GLib.Error:
            pass

    def _on_start_scan(self, *args):
        self._set_scanning(True)
        self._notebook.set_visible(False)
        self._path_label.set_text(str(self._current_path))
        self._progress_bar.set_show_text(True)
        self._progress_bar.set_text("Preparing...")
        self._summary_label.set_text("Preparing scan...")

        self._task = run_scanner(
            scan_disk_usage,
            self._current_path,
            progress_callback=self._on_progress,
            done_callback=self._on_scan_done,
            error_callback=self._on_scan_error,
        )

    def _on_progress(self, info: dict):
        phase = info.get("phase", "")
        current = info.get("current", 0)
        total = info.get("total", 0)
        path = info.get("path", "")

        if phase == "counting":
            self._progress_bar.set_pulse_step(0.05)
            self._progress_bar.pulse()
            self._progress_bar.set_text("Counting files...")
            self._status_label.set_text("Counting files...")
        elif phase == "scanning":
            if total > 0:
                frac = min(current / total, 1.0)
                self._progress_bar.set_fraction(frac)
                self._progress_bar.set_text(f"{current:05d}/{total:05d}")
            else:
                self._progress_bar.set_pulse_step(0.05)
                self._progress_bar.pulse()
                self._progress_bar.set_text(f"{current:05d}/?????")
        elif phase == "indexing":
            self._progress_bar.set_fraction(1.0)
            self._progress_bar.set_text(f"{current:05d}/{current:05d}")
            self._status_label.set_text("Indexing...")
        return False

    def _on_scan_done(self, result: DiskScanResult):
        self._set_scanning(False)
        self._result = result
        self._notebook.set_visible(True)
        self._summary_label.set_text(
            f"Scanned {result.files_scanned} files in {format_duration(result.scan_time_seconds)} "
            f"\u2014 {format_size(result.total_size)} total"
        )

        top_dirs = [e for e in result.entries if e.path != result.root][:50]
        if top_dirs:
            self._treemap.set_data(top_dirs)

        clear_children(self._bar_box)
        max_size = top_dirs[0].size if top_dirs else 1
        for entry in top_dirs[:20]:
            bar_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            bar_row.set_margin_top(2)
            bar_row.set_margin_bottom(2)

            name_label = Gtk.Label(label=entry.path.name)
            name_label.set_size_request(150, -1)
            name_label.set_xalign(0)
            name_label.set_ellipsize(3)
            bar_row.append(name_label)

            bar_area = Gtk.DrawingArea()
            bar_area.set_content_width(200)
            bar_area.set_content_height(14)
            bar_area.set_draw_func(self._draw_bar, entry.size, max_size)
            bar_row.append(bar_area)

            size_label = Gtk.Label(label=format_size(entry.size), css_classes=["dim-label"])
            size_label.set_size_request(80, -1)
            size_label.set_xalign(1)
            bar_row.append(size_label)

            self._bar_box.append(bar_row)

        clear_children(self._entries_list)
        for entry in top_dirs:
            row = DirRow(entry.path, entry.size, max_size, entry.file_count)
            row.connect("activated", self._on_entry_activated, entry)
            self._entries_list.append(row)

    def _draw_bar(self, area, cr, w, h, size, max_size):
        fraction = size / max_size if max_size > 0 else 0
        cr.set_source_rgba(0.25, 0.25, 0.25, 1)
        cr.rectangle(0, 0, w, h)
        cr.fill()
        cr.set_source_rgba(0.2, 0.53, 0.82, 1)
        cr.rectangle(0, 0, w * fraction, h)
        cr.fill()

    def _on_scan_error(self, error: Exception):
        self._set_scanning(False)
        self._summary_label.set_text(f"Error: {error}")

    def _on_entry_activated(self, row, entry):
        if entry.path.is_dir():
            self._path_history.append(self._current_path)
            self._current_path = entry.path
            self._back_button.set_visible(True)
            self._on_start_scan()

    def _on_back(self, *args):
        if self._path_history:
            self._current_path = self._path_history.pop()
            if not self._path_history:
                self._back_button.set_visible(False)
            self._on_start_scan()

    def _on_treemap_click(self, widget, label: str):
        if self._result:
            for entry in self._result.entries:
                if entry.path.name == label and entry.path.is_dir():
                    self._path_history.append(self._current_path)
                    self._current_path = entry.path
                    self._back_button.set_visible(True)
                    self._on_start_scan()
                    break
