import os
import time
from pathlib import Path

from gigaorganize.models import (
    HardwareInfo, PackageInfo, ServiceInfo, SysInfoResult,
)


def _read_file(path: str, default: str = "Unknown") -> str:
    try:
        with open(path) as f:
            return f.read().strip()
    except (OSError, PermissionError):
        return default


def _get_cpu_info() -> tuple[str, int, int, float]:
    model = "Unknown"
    cores = 0
    threads = 0
    freq = 0.0
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name") and model == "Unknown":
                    model = line.split(":", 1)[1].strip()
                if line.startswith("cpu cores"):
                    cores = int(line.split(":", 1)[1].strip())
                if line.startswith("siblings"):
                    threads = int(line.split(":", 1)[1].strip())
    except (OSError, ValueError):
        pass
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("cpu MHz"):
                    freq = float(line.split(":", 1)[1].strip())
                    break
    except (OSError, ValueError):
        pass
    return model, cores, threads, freq


def _get_ram_info() -> tuple[float, float]:
    total = 0.0
    used = 0.0
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    total = int(line.split()[1]) / 1048576
                elif line.startswith("MemAvailable:"):
                    avail = int(line.split()[1]) / 1048576
                    used = total - avail
    except (OSError, ValueError):
        pass
    return total, used


def _get_gpu_info() -> tuple[str, str]:
    name = "Unknown"
    driver = "Unknown"
    try:
        import subprocess
        result = subprocess.run(
            ["lspci", "-v"], capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            if "VGA" in line or "3D" in line:
                parts = line.split(": ", 1)
                if len(parts) > 1:
                    name = parts[1].strip()
                break
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            driver = result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return name, driver


def _get_distro() -> str:
    name = _read_file("/etc/os-release", "")
    for line in name.splitlines():
        if line.startswith("PRETTY_NAME="):
            return line.split("=", 1)[1].strip('"')
    return "Unknown Linux"


def _get_desktop_env() -> str:
    return os.environ.get("XDG_CURRENT_DESKTOP", "Unknown")


def _get_display_server() -> str:
    if os.environ.get("WAYLAND_DISPLAY"):
        return "Wayland"
    if os.environ.get("DISPLAY"):
        return "X11"
    return "Unknown"


def _get_brew_packages() -> list[PackageInfo]:
    packages = []
    try:
        import subprocess
        result = subprocess.run(
            ["brew", "list", "--formula", "--json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            for name, info in data.get("formulae", {}).items():
                ver = info.get("versions", {}).get("stable", "unknown")
                packages.append(PackageInfo(name=name, version=ver, source="homebrew"))
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    return packages


def _get_flatpak_packages() -> list[PackageInfo]:
    packages = []
    try:
        import subprocess
        result = subprocess.run(
            ["flatpak", "list", "--columns=application,version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                parts = line.split("\t")
                if len(parts) >= 2:
                    packages.append(PackageInfo(
                        name=parts[0], version=parts[1], source="flatpak"
                    ))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return packages


def _get_services() -> list[ServiceInfo]:
    services = []
    try:
        import subprocess
        result = subprocess.run(
            ["systemctl", "list-units", "--type=service", "--all",
             "--no-legend", "--no-pager"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                parts = line.split(None, 4)
                if len(parts) >= 4:
                    name = parts[0].replace(".service", "")
                    state = parts[2]
                    desc = parts[4] if len(parts) > 4 else ""
                    services.append(ServiceInfo(
                        name=name, state=state, description=desc,
                        user_level="system"
                    ))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return services


def collect_sysinfo(*, progress=None, cancellable=None) -> SysInfoResult:
    start = time.monotonic()

    if progress:
        progress({"current": 0, "total": 5, "path": "CPU"})

    cpu_model, cpu_cores, cpu_threads, cpu_freq = _get_cpu_info()
    ram_total, ram_used = _get_ram_info()
    gpu_name, gpu_driver = _get_gpu_info()

    if cancellable and cancellable.is_cancelled():
        return SysInfoResult(hardware=HardwareInfo(), packages=[], services=[],
                             flatpak_apps=[], brew_packages=[], collect_time_seconds=0)

    if progress:
        progress({"current": 1, "total": 5, "path": "Packages"})

    brew_pkgs = _get_brew_packages()
    flatpak_pkgs = _get_flatpak_packages()

    if progress:
        progress({"current": 3, "total": 5, "path": "Services"})

    services = _get_services()

    if progress:
        progress({"current": 5, "total": 5, "path": "Done"})

    return SysInfoResult(
        hardware=HardwareInfo(
            cpu_model=cpu_model,
            cpu_cores=cpu_cores,
            cpu_threads=cpu_threads,
            cpu_freq_mhz=cpu_freq,
            ram_total_gb=round(ram_total, 1),
            ram_used_gb=round(ram_used, 1),
            gpu_name=gpu_name,
            gpu_driver=gpu_driver,
            hostname=os.uname().nodename,
            kernel=os.uname().release,
            distro=_get_distro(),
            desktop_env=_get_desktop_env(),
            display_server=_get_display_server(),
        ),
        packages=[],
        services=services,
        flatpak_apps=flatpak_pkgs,
        brew_packages=brew_pkgs,
        collect_time_seconds=time.monotonic() - start,
    )
