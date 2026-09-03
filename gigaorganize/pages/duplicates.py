import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio
from pathlib import Path
import os
from collections import defaultdict

from gigaorganize.widgets.scan_page import ScanPage
from gigaorganize.widgets.file_row import FileRow
from gigaorganize.utils.thread import run_scanner
from gigaorganize.utils.hasher import partial_hash, full_hash
from gigaorganize.utils.format import format_size, format_duration, clear_children
from gigaorganize.utils.file_utils import safe_trash, open_file, reveal_in_manager
from gigaorganize.models import DuplicateGroup, DuplicateScanResult
from gigaorganize.constants import HOME, MIN_DUPLICATE_SIZE


def _count_files(root: Path, *, skip_hidden: bool = True, cancellable=None) -> int:
    count = 0
    for dirpath, _, filenames in os.walk(root):
        if cancellable and cancellable.is_cancelled():
            return 0
        for fname in filenames:
            if skip_hidden and fname.startswith("."):
                continue
            count += 1
    return count


def _safe_full_hash(fp: Path) -> str | None:
    try:
        return full_hash(fp)
    except (OSError, PermissionError, ValueError):
        return None


def scan_duplicates(root: Path, *, progress=None, cancellable=None,
                    min_size: int = MIN_DUPLICATE_SIZE,
                    skip_hidden: bool = True) -> DuplicateScanResult:
    import time
    start = time.monotonic()

    if progress:
        progress({"phase": "counting", "current": 0, "total": 0, "path": str(root)})
    total_files = _count_files(root, skip_hidden=skip_hidden, cancellable=cancellable)
    if cancellable and cancellable.is_cancelled():
        return DuplicateScanResult(groups=[], total_duplicates=0,
                                   total_wasted_bytes=0, scan_time_seconds=0,
                                   files_scanned=0)

    size_groups: dict[tuple, list[Path]] = defaultdict(list)
    file_count = 0
    errors: list[str] = []

    for dirpath, _, filenames in os.walk(root):
        if cancellable and cancellable.is_cancelled():
            return DuplicateScanResult(groups=[], total_duplicates=0,
                                       total_wasted_bytes=0, scan_time_seconds=0,
                                       files_scanned=file_count)
        for fname in filenames:
            if skip_hidden and fname.startswith("."):
                continue
            fp = Path(dirpath) / fname
            try:
                sz = fp.stat().st_size
                if sz < min_size:
                    continue
                partial = partial_hash(fp)
                size_groups[(sz, partial)].append(fp)
                file_count += 1
                if progress and file_count % 25 == 0:
                    progress({
                        "phase": "hashing",
                        "current": file_count,
                        "total": total_files,
                        "path": str(fp),
                    })
            except (OSError, PermissionError):
                continue

    candidate_count = sum(len(v) for v in size_groups.values() if len(v) > 1)
    if progress:
        progress({
            "phase": "comparing",
            "current": 0,
            "total": candidate_count,
            "path": f"Found {candidate_count} potential duplicates, verifying...",
        })

    groups: list[DuplicateGroup] = []

    def _hash_all(files, sz, done_counter):
        import concurrent.futures
        full_groups: dict[str, list[Path]] = defaultdict(list)
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            futures = {ex.submit(_safe_full_hash, fp): fp for fp in files}
            for fut in concurrent.futures.as_completed(futures):
                if cancellable and cancellable.is_cancelled():
                    ex.shutdown(wait=False, cancel_futures=True)
                    return ("__cancelled__", done_counter)
                try:
                    h = fut.result()
                except (OSError, PermissionError):
                    continue
                if h is not None:
                    full_groups[h].append(futures[fut])
                done_counter[0] += 1
                if progress and done_counter[0] % 10 == 0:
                    progress({
                        "phase": "comparing",
                        "current": done_counter[0],
                        "total": candidate_count,
                        "path": f"Verifying: {futures[fut].name}",
                    })
        return (full_groups, done_counter)

    done_counter = [0]
    for (sz, _), candidates in size_groups.items():
        if len(candidates) < 2 or (cancellable and cancellable.is_cancelled()):
            continue
        full_groups, done_counter = _hash_all(candidates, sz, done_counter)
        if full_groups == "__cancelled__":
            return DuplicateScanResult(groups=[], total_duplicates=0,
                                       total_wasted_bytes=0, scan_time_seconds=0,
                                       files_scanned=file_count)
        for h, files in full_groups.items():
            if len(files) >= 2:
                groups.append(DuplicateGroup(
                    hash_value=h, hash_type="full", file_size=sz,
                    files=sorted(files),
                    total_wasted=sz * (len(files) - 1),
                ))

    groups.sort(key=lambda g: g.total_wasted, reverse=True)
    total_dupes = sum(g.count for g in groups)
    total_wasted = sum(g.total_wasted for g in groups)

    return DuplicateScanResult(
        groups=groups,
        total_duplicates=total_dupes,
        total_wasted_bytes=total_wasted,
        scan_time_seconds=time.monotonic() - start,
        files_scanned=file_count,
        errors=errors,
    )


class DuplicatesPage(ScanPage):
    __gtype_name__ = "DuplicatesPage"

    def __init__(self, **kwargs):
        super().__init__(title="Duplicate Finder", **kwargs)
        self._current_path = HOME
        self._result: DuplicateScanResult | None = None
        self._group_widgets: list[tuple[DuplicateGroup, Gtk.Box]] = []
        self._render_gen = 0

        path_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._outer.append(path_box)

        self._folder_button = Gtk.Button(label="Select Folder...")
        self._folder_button.connect("clicked", self._on_select_folder)
        path_box.append(self._folder_button)

        self._path_label = Gtk.Label(label=str(self._current_path))
        self._path_label.set_hexpand(True)
        self._path_label.set_xalign(0)
        path_box.append(self._path_label)

        opts_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self._outer.append(opts_box)

        hidden_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        opts_box.append(hidden_box)
        hidden_box.append(Gtk.Label(label="Skip hidden files:"))
        self._skip_hidden_switch = Gtk.Switch()
        self._skip_hidden_switch.set_active(True)
        hidden_box.append(self._skip_hidden_switch)

        self._summary_label = Gtk.Label(label="", css_classes=["dim-label"])
        self._summary_label.set_xalign(0)
        self._outer.append(self._summary_label)

        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._outer.append(action_box)

        self._trash_button = Gtk.Button(label="Move Selected to Trash")
        self._trash_button.add_css_class("destructive-action")
        self._trash_button.set_visible(False)
        self._trash_button.connect("clicked", self._on_trash_selected)
        action_box.append(self._trash_button)

        self._select_all_button = Gtk.Button(label="Select All Duplicates")
        self._select_all_button.set_visible(False)
        self._select_all_button.connect("clicked", self._on_select_all)
        action_box.append(self._select_all_button)

        self._groups_list = Gtk.ListBox()
        self._groups_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll = Gtk.ScrolledWindow()
        scroll.set_child(self._groups_list)
        scroll.set_vexpand(True)
        self._results_area.append(scroll)

    def _on_select_folder(self, *args):
        dialog = Gtk.FileDialog()
        dialog.set_title("Select folder to scan for duplicates")
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
        self._render_gen += 1
        self._set_scanning(True)
        self._summary_label.set_text("Preparing duplicate scan...")
        self._progress_bar.set_show_text(True)
        self._progress_bar.set_text("Preparing...")

        self._task = run_scanner(
            scan_duplicates,
            self._current_path,
            progress_callback=self._on_progress,
            done_callback=self._on_scan_done,
            error_callback=self._on_scan_error,
            min_size=MIN_DUPLICATE_SIZE,
            skip_hidden=self._skip_hidden_switch.get_active(),
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
        elif phase == "hashing":
            if total > 0:
                frac = min(current / total, 1.0)
                self._progress_bar.set_fraction(frac)
                self._progress_bar.set_text(f"{current:05d}/{total:05d}")
            else:
                self._progress_bar.set_pulse_step(0.05)
                self._progress_bar.pulse()
                self._progress_bar.set_text(f"{current:05d}/?????")
            self._status_label.set_text("Hashing files...")
        elif phase == "comparing":
            if total > 0:
                frac = min(current / total, 1.0)
                self._progress_bar.set_fraction(frac)
                self._progress_bar.set_text(f"{current:05d}/{total:05d}")
            else:
                self._progress_bar.set_pulse_step(0.1)
                self._progress_bar.pulse()
                self._progress_bar.set_text("Comparing hashes...")
            self._status_label.set_text("Verifying duplicates...")
        return False

    def _on_scan_done(self, result: DuplicateScanResult):
        self._set_scanning(False)
        self._result = result
        self._group_widgets.clear()

        self._summary_label.set_text(
            f"Found {len(result.groups)} duplicate groups ({result.total_duplicates} files) "
            f"\u2014 {format_size(result.total_wasted_bytes)} wasted "
            f"in {format_duration(result.scan_time_seconds)}"
        )

        clear_children(self._groups_list)

        if not result.groups:
            self._summary_label.set_text("No duplicates found!")
            return

        self._trash_button.set_visible(True)
        self._select_all_button.set_visible(True)

        self._render_chunk(iter(result.groups), render_gen=self._render_gen, chunk_size=50)

    def _render_chunk(self, groups_iter, render_gen, chunk_size=50):
        if render_gen != self._render_gen:
            return False
        rendered = 0
        try:
            while rendered < chunk_size:
                group = next(groups_iter)
                self._append_group(group)
                rendered += 1
        except StopIteration:
            groups_iter = None

        if groups_iter is not None:
            GLib.idle_add(self._render_chunk, groups_iter, self._render_gen, chunk_size)
            return True
        return False

    def _append_group(self, group):
        expander = Gtk.Expander(
            label=f"{group.count} copies \u2014 {format_size(group.file_size)} each  "
                  f"[Wasted: {format_size(group.total_wasted)}]"
        )
        expander.set_margin_top(4)
        expander.set_margin_bottom(4)

        file_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        checkboxes: list[Gtk.CheckButton] = []

        for i, fp in enumerate(group.files):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row.set_margin_top(2)
            row.set_margin_bottom(2)

            cb = Gtk.CheckButton()
            cb.set_active(i > 0)
            checkboxes.append(cb)
            row.append(cb)

            file_label = Gtk.Label(label=str(fp), xalign=0)
            file_label.set_ellipsize(3)
            file_label.set_hexpand(True)
            row.append(file_label)

            open_btn = Gtk.Button(label="Open")
            open_btn.add_css_class("flat")
            open_btn.set_size_request(60, -1)
            open_btn.connect("clicked", lambda b, p=fp: open_file(p))
            row.append(open_btn)

            reveal_btn = Gtk.Button(label="Folder")
            reveal_btn.add_css_class("flat")
            reveal_btn.set_size_request(60, -1)
            reveal_btn.connect("clicked", lambda b, p=fp: reveal_in_manager(p))
            row.append(reveal_btn)

            file_box.append(row)

        expander.set_child(file_box)
        self._groups_list.append(expander)
        self._group_widgets.append((group, expander, checkboxes))

    def _on_scan_error(self, error: Exception):
        self._set_scanning(False)
        self._summary_label.set_text(f"Error: {error}")

    def _on_select_all(self, *args):
        for group, expander, checkboxes in self._group_widgets:
            for cb in checkboxes[1:]:
                cb.set_active(True)

    def _on_trash_selected(self, *args):
        removed = 0
        for group, expander, checkboxes in self._group_widgets:
            for i, cb in enumerate(checkboxes):
                if cb.get_active() and i > 0:
                    if safe_trash(group.files[i]):
                        removed += 1
        if removed > 0:
            self._summary_label.set_text(f"Moved {removed} files to trash")
            self._on_start_scan()
