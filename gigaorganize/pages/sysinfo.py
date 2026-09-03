import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from gigaorganize.widgets.scan_page import ScanPage
from gigaorganize.utils.thread import run_scanner
from gigaorganize.utils.sysinfo_collector import collect_sysinfo
from gigaorganize.utils.format import format_size, clear_children
from gigaorganize.models import SysInfoResult


class SysInfoPage(ScanPage):
    __gtype_name__ = "SysInfoPage"

    def __init__(self, **kwargs):
        super().__init__(title="System Info", **kwargs)
        self._result: SysInfoResult | None = None

        self._scan_button.set_label("Refresh")
        self._scan_button.connect("clicked", self._on_start_scan)

        self._status_label.set_text("Click Refresh to load system info")

    def _on_start_scan(self, *args):
        self._set_scanning(True)
        self._status_label.set_text("Collecting system info...")
        self._progress_bar.set_show_text(True)
        self._progress_bar.set_text("Starting...")

        self._task = run_scanner(
            collect_sysinfo,
            progress_callback=self._on_progress,
            done_callback=self._on_scan_done,
            error_callback=self._on_scan_error,
        )

    def _on_progress(self, info: dict):
        total = max(info["total"], 1)
        self._progress_bar.set_fraction(info["current"] / total)
        self._status_label.set_text(f"Collecting: {info['path']}")
        return False

    def _on_scan_done(self, result: SysInfoResult):
        self._set_scanning(False)
        self._result = result

        clear_children(self._results_area)

        hw = result.hardware

        hw_group = Adw.PreferencesGroup(title="Hardware")
        self._results_area.append(hw_group)

        for label, value in [
            ("CPU", f"{hw.cpu_model} ({hw.cpu_cores}C/{hw.cpu_threads}T @ {hw.cpu_freq_mhz:.0f} MHz)"),
            ("RAM", f"{hw.ram_total_gb:.1f} GB total, {hw.ram_used_gb:.1f} GB used"),
            ("GPU", hw.gpu_name),
            ("GPU Driver", hw.gpu_driver),
            ("Hostname", hw.hostname),
            ("Kernel", hw.kernel),
            ("Distro", hw.distro),
            ("Desktop", hw.desktop_env),
            ("Display", hw.display_server),
        ]:
            row = Adw.ActionRow(title=label)
            row.add_suffix(Gtk.Label(label=value, css_classes=["dim-label"]))
            hw_group.add(row)

        pkg_group = Adw.PreferencesGroup(title="Packages")
        self._results_area.append(pkg_group)

        brew_row = Adw.ActionRow(title="Homebrew")
        brew_row.add_suffix(Gtk.Label(
            label=f"{len(result.brew_packages)} packages",
            css_classes=["dim-label"]
        ))
        pkg_group.add(brew_row)

        flatpak_row = Adw.ActionRow(title="Flatpak")
        flatpak_row.add_suffix(Gtk.Label(
            label=f"{len(result.flatpak_apps)} apps",
            css_classes=["dim-label"]
        ))
        pkg_group.add(flatpak_row)

        svc_group = Adw.PreferencesGroup(title=f"Services ({len(result.services)})")
        self._results_area.append(svc_group)

        for svc in result.services[:30]:
            row = Adw.ActionRow(title=svc.name)
            row.set_subtitle(svc.description)

            state_label = Gtk.Label(label=svc.state)
            if svc.state == "active":
                state_label.add_css_class("success")
            elif svc.state == "failed":
                state_label.add_css_class("error")
            elif svc.state == "inactive":
                state_label.add_css_class("dim-label")
            else:
                state_label.add_css_class("accent")

            row.add_suffix(state_label)
            svc_group.add(row)

    def _on_scan_error(self, error: Exception):
        self._set_scanning(False)
        self._status_label.set_text(f"Error: {error}")
