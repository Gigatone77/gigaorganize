import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from gigaorganize.pages.disk_usage import DiskUsagePage
from gigaorganize.pages.duplicates import DuplicatesPage
from gigaorganize.pages.cleanup import CleanupPage
from gigaorganize.pages.file_organizer import FileOrganizerPage
from gigaorganize.pages.sysinfo import SysInfoPage
from gigaorganize.constants import WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT


class MainWindow(Adw.ApplicationWindow):
    __gtype_name__ = "MainWindow"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("GigaOrganize")
        self.set_default_size(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        toolbar = Adw.ToolbarView()
        self.set_content(toolbar)

        header = Adw.HeaderBar()
        toolbar.add_top_bar(header)

        split = Adw.NavigationSplitView()
        split.set_min_sidebar_width(180)
        split.set_max_sidebar_width(220)

        sidebar_page = Adw.NavigationPage()
        sidebar_page.set_title("Navigation")

        sidebar_list = Gtk.ListBox()
        sidebar_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        sidebar_list.add_css_class("navigation-sidebar")
        sidebar_list.add_css_class("compact-sidebar")

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(200)

        pages = [
            ("disk-usage", "Disk Usage", "drive-harddisk-symbolic", DiskUsagePage),
            ("duplicates", "Duplicates", "edit-find-replace-symbolic", DuplicatesPage),
            ("cleanup", "Cleanup", "user-trash-symbolic", CleanupPage),
            ("organizer", "File Organizer", "folder-download-symbolic", FileOrganizerPage),
            ("sysinfo", "System Info", "info-symbolic", SysInfoPage),
        ]

        for page_id, title, icon_name, page_class in pages:
            row = Adw.ActionRow(title=title, icon_name=icon_name)
            row.set_activatable(True)
            row._page_id = page_id
            sidebar_list.append(row)

            page = page_class()
            self.stack.add_named(page, page_id)

        def on_row_activated(listbox, row):
            if hasattr(row, "_page_id"):
                self.stack.set_visible_child_name(row._page_id)

        sidebar_list.connect("row-activated", on_row_activated)

        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_scroll.set_child(sidebar_list)
        sidebar_scroll.set_vexpand(True)
        sidebar_page.set_child(sidebar_scroll)
        split.set_sidebar(sidebar_page)

        content_page = Adw.NavigationPage()
        content_page.set_title("GigaOrganize")
        content_page.set_child(self.stack)
        split.set_content(content_page)

        toolbar.set_content(split)
        self.stack.set_visible_child_name("disk-usage")
        sidebar_list.select_row(sidebar_list.get_row_at_index(0))
