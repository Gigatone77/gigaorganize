import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib
from pathlib import Path

from gigaorganize.widgets.scan_page import ScanPage
from gigaorganize.utils.thread import run_async
from gigaorganize.utils.organizer import plan_organize, apply_plan, undo_plan
from gigaorganize.utils.format import format_size, clear_children
from gigaorganize.models import OrganizePlan, OrganizeResult
from gigaorganize.constants import HOME, EXT_TO_CATEGORY


class FileOrganizerPage(ScanPage):
    __gtype_name__ = "FileOrganizerPage"

    def __init__(self, **kwargs):
        super().__init__(title="File Organizer", **kwargs)
        self._current_path = HOME / "Downloads"
        self._plan: OrganizePlan | None = None
        self._last_result: OrganizeResult | None = None

        path_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._outer.append(path_box)

        path_box.append(Gtk.Label(label="Organize folder:"))

        self._folder_button = Gtk.Button(label="Select Folder...")
        self._folder_button.connect("clicked", self._on_select_folder)
        path_box.append(self._folder_button)

        self._path_label = Gtk.Label(label=str(self._current_path))
        self._path_label.set_hexpand(True)
        self._path_label.set_xalign(0)
        path_box.append(self._path_label)

        expander = Gtk.Expander(label="Sorting Rules")
        self._outer.append(expander)

        rules_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        rules_box.set_margin_start(12)
        expander.set_child(rules_box)

        type_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        rules_box.append(type_box)
        type_box.append(Gtk.Label(label="Sort by file type:"))
        self._sort_type = Gtk.Switch()
        self._sort_type.set_active(True)
        type_box.append(self._sort_type)

        date_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        rules_box.append(date_box)
        date_box.append(Gtk.Label(label="Sort by date (year/month):"))
        self._sort_date = Gtk.Switch()
        date_box.append(self._sort_date)

        target_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        rules_box.append(target_box)
        target_box.append(Gtk.Label(label="Target base:"))
        self._target_label = Gtk.Label(
            label=str(HOME / "Documents" / "GigaOrganize")
        )
        self._target_label.set_hexpand(True)
        self._target_label.set_xalign(0)
        target_box.append(self._target_label)

        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._outer.append(action_box)

        self._preview_button = Gtk.Button(label="Preview")
        self._preview_button.add_css_class("suggested-action")
        self._preview_button.connect("clicked", self._on_preview)
        action_box.append(self._preview_button)

        self._apply_button = Gtk.Button(label="Apply")
        self._apply_button.add_css_class("suggested-action")
        self._apply_button.set_visible(False)
        self._apply_button.connect("clicked", self._on_apply)
        action_box.append(self._apply_button)

        self._undo_button = Gtk.Button(label="Undo")
        self._undo_button.set_visible(False)
        self._undo_button.connect("clicked", self._on_undo)
        action_box.append(self._undo_button)

        self._result_label = Gtk.Label(label="", css_classes=["dim-label"])
        self._result_label.set_xalign(0)
        self._outer.append(self._result_label)

        self._actions_list = Gtk.ListBox()
        self._actions_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll = Gtk.ScrolledWindow()
        scroll.set_child(self._actions_list)
        scroll.set_vexpand(True)
        self._results_area.append(scroll)

    def _on_select_folder(self, *args):
        dialog = Gtk.FileDialog()
        dialog.set_title("Select folder to organize")
        folder = Gio.File.new_for_path(str(self._current_path))
        dialog.select_folder(self.get_root(), None, self._on_folder_selected, folder)

    def _on_folder_selected(self, dialog, result):
        try:
            file = dialog.select_folder_finish(result)
            if file:
                self._current_path = Path(file.get_path())
                self._path_label.set_text(str(self._current_path))
        except GLib.Error:
            pass

    def _on_start_scan(self, *args):
        self._on_preview()

    def _on_preview(self, *args):
        clear_children(self._actions_list)

        self._plan = plan_organize(
            self._current_path,
            sort_by_type=self._sort_type.get_active(),
            sort_by_date=self._sort_date.get_active(),
        )

        total_actions = len(self._plan.actions)
        total_conflicts = len(self._plan.conflicts)

        self._result_label.set_text(
            f"Preview: {total_actions} files will be moved"
            + (f", {total_conflicts} conflicts" if total_conflicts else "")
        )

        for action in self._plan.actions[:100]:
            row = Gtk.ListBoxRow()
            row.set_activatable(False)
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            hbox.set_margin_top(4)
            hbox.set_margin_bottom(4)
            hbox.set_margin_start(8)
            hbox.set_margin_end(8)
            row.set_child(hbox)

            source_label = Gtk.Label(label=action.source.name, xalign=0)
            source_label.set_hexpand(True)
            source_label.set_ellipsize(3)
            hbox.append(source_label)

            hbox.append(Gtk.Label(label="\u2192", css_classes=["dim-label"]))

            rel_dest = action.destination.relative_to(
                HOME / "Documents" / "GigaOrganize"
            )
            dest_label = Gtk.Label(label=str(rel_dest), css_classes=["dim-label"], xalign=0)
            dest_label.set_ellipsize(3)
            hbox.append(dest_label)

            cat_label = Gtk.Label(label=action.rule_name, css_classes=["caption"])
            hbox.append(cat_label)

            self._actions_list.append(row)

        if total_conflicts > 0:
            for action in self._plan.conflicts[:20]:
                row = Gtk.ListBoxRow()
                row.set_activatable(False)
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                hbox.set_margin_top(4)
                hbox.set_margin_bottom(4)
                hbox.set_margin_start(8)
                hbox.set_margin_end(8)
                row.set_child(hbox)

                cb = Gtk.CheckButton()
                cb.set_active(False)
                hbox.append(cb)

                source_label = Gtk.Label(label=action.source.name, xalign=0)
                source_label.set_hexpand(True)
                hbox.append(source_label)

                hbox.append(Gtk.Label(label="(conflict)", css_classes=["error", "caption"]))

                self._actions_list.append(row)

        self._apply_button.set_visible(total_actions > 0)
        self._scan_button.set_visible(False)

    def _on_apply(self, *args):
        if not self._plan:
            return
        self._set_scanning(True)
        self._status_label.set_text("Applying changes...")

        def do_apply():
            return apply_plan(self._plan)

        run_async(
            do_apply,
            callback=self._on_apply_done,
            error_callback=self._on_apply_error,
        )

    def _on_apply_done(self, result: OrganizeResult):
        self._set_scanning(False)
        self._last_result = result
        self._result_label.set_text(
            f"Moved {result.moved} files, skipped {result.skipped}"
            + (f", {len(result.errors)} errors" if result.errors else "")
        )
        self._apply_button.set_visible(False)
        self._undo_button.set_visible(result.moved > 0)
        self._scan_button.set_visible(True)

    def _on_apply_error(self, error: Exception):
        self._set_scanning(False)
        self._result_label.set_text(f"Error: {error}")

    def _on_undo(self, *args):
        if self._last_result:
            undone = undo_plan(self._last_result)
            self._result_label.set_text(f"Undone {undone} moves")
            self._undo_button.set_visible(False)
