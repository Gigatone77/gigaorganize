import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from gigaorganize.widgets.scan_page import ScanPage
from gigaorganize.widgets.category_card import CategoryCard
from gigaorganize.utils.thread import run_scanner
from gigaorganize.utils.cleaner import scan_caches
from gigaorganize.utils.format import format_size, clear_children
from gigaorganize.utils.file_utils import (
    safe_trash,
    move_to_recoverable_bin,
    RECOVERABLE_BIN,
)
from gigaorganize.models import CleanupScanResult


class CleanupPage(ScanPage):
    __gtype_name__ = "CleanupPage"

    def __init__(self, **kwargs):
        super().__init__(title="System Cleanup", **kwargs)
        self._result: CleanupScanResult | None = None
        self._category_cards: list[CategoryCard] = []

        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._outer.append(action_box)

        self._clean_button = Gtk.Button(label="Clean Selected")
        self._clean_button.add_css_class("suggested-action")
        self._clean_button.set_visible(False)
        self._clean_button.connect("clicked", self._on_clean)
        action_box.append(self._clean_button)

        self._clean_all_button = Gtk.Button(label="Clean All")
        self._clean_all_button.add_css_class("destructive-action")
        self._clean_all_button.set_visible(False)
        self._clean_all_button.connect("clicked", self._on_clean_all)
        action_box.append(self._clean_all_button)

        self._summary_label = Gtk.Label(label="", css_classes=["dim-label"])
        self._summary_label.set_xalign(0)
        self._outer.append(self._summary_label)

        self._categories_list = Gtk.ListBox()
        self._categories_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll = Gtk.ScrolledWindow()
        scroll.set_child(self._categories_list)
        scroll.set_vexpand(True)
        self._results_area.append(scroll)

    def _on_start_scan(self, *args):
        self._set_scanning(True)
        self._summary_label.set_text("Preparing cleanup scan...")
        self._progress_bar.set_show_text(True)
        self._progress_bar.set_text("Preparing...")

        self._task = run_scanner(
            scan_caches,
            progress_callback=self._on_progress,
            done_callback=self._on_scan_done,
            error_callback=self._on_scan_error,
        )

    def _on_progress(self, info: dict):
        phase = info.get("phase", "")
        current = info.get("current", 0)
        total = info.get("total", 0)
        path = info.get("path", "")

        if total > 0:
            frac = min(current / total, 1.0)
            self._progress_bar.set_fraction(frac)
            self._progress_bar.set_text(f"{current:05d}/{total:05d}")

        if phase == "caches":
            self._summary_label.set_text("Scanning caches...")
        elif phase == "logs":
            self._summary_label.set_text("Scanning logs...")
        elif phase == "done":
            self._progress_bar.set_fraction(1.0)
            self._progress_bar.set_text(f"{total:05d}/{total:05d}")
            self._summary_label.set_text("Scan complete, loading results...")
        return False

    def _on_scan_done(self, result: CleanupScanResult):
        self._set_scanning(False)
        self._result = result
        self._category_cards.clear()

        clear_children(self._categories_list)

        self._summary_label.set_text(
            f"Cleanable: {format_size(result.total_cleanable)} "
            f"across {len(result.caches)} categories"
        )

        self._clean_button.set_visible(True)
        self._clean_all_button.set_visible(True)

        for cache in result.caches:
            card = CategoryCard(
                name=cache.name,
                description=cache.description,
                size_bytes=cache.size_bytes,
                needs_root=cache.needs_root,
            )
            self._categories_list.append(card)
            self._category_cards.append(card)

        if result.trash_size > 0:
            trash_card = CategoryCard(
                name="Trash",
                description="Files in system trash",
                size_bytes=result.trash_size,
            )
            self._categories_list.append(trash_card)
            self._category_cards.append(trash_card)

    def _on_scan_error(self, error: Exception):
        self._set_scanning(False)
        self._summary_label.set_text(f"Error: {error}")

    def _on_clean(self, *args):
        # NO-DELETE POLICY: caches are MOVED into a hidden, restorable bin
        # (.gigaorganize-trash/), never deleted. The OS "Trash" card is
        # informational only - emptying the system trash is left to the user.
        moved = 0
        for card in self._category_cards:
            if not card.is_checked:
                continue
            name = card.get_child().get_first_child().get_first_child().get_label()
            if name == "Trash":
                self._summary_label.set_text(
                    "System trash is left for you to empty manually - "
                    "GigaOrganize does not delete."
                )
                self._on_start_scan()
                return
            for cache in self._result.caches:
                if cache.name == name and cache.deletable:
                    for path in cache.paths:
                        if path.exists():
                            if move_to_recoverable_bin(path, name):
                                moved += 1

        if moved > 0:
            self._summary_label.set_text(
                f"Moved {moved} cache item(s) to the hidden '{RECOVERABLE_BIN}/' "
                f"bin (nothing deleted - restore by hand)."
            )
        else:
            self._summary_label.set_text("Nothing was deleted or moved.")
        self._on_start_scan()

    def _on_clean_all(self, *args):
        for card in self._category_cards:
            card.set_checked(True)
        self._on_clean()
