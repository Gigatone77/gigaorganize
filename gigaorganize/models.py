from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class DirEntry:
    path: Path
    size: int
    is_dir: bool
    file_count: int = 0
    child_count: int = 0
    largest_child: Optional[Path] = None

    @property
    def size_human(self) -> str:
        from gigaorganize.utils.format import format_size
        return format_size(self.size)


@dataclass(slots=True)
class DiskScanResult:
    root: Path
    entries: list[DirEntry]
    total_size: int
    scan_time_seconds: float
    files_scanned: int
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DuplicateGroup:
    hash_value: str
    hash_type: str
    file_size: int
    files: list[Path]
    total_wasted: int

    @property
    def count(self) -> int:
        return len(self.files)


@dataclass(slots=True)
class DuplicateScanResult:
    groups: list[DuplicateGroup]
    total_duplicates: int
    total_wasted_bytes: int
    scan_time_seconds: float
    files_scanned: int
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CacheEntry:
    name: str
    paths: list[Path]
    size_bytes: int
    deletable: bool
    needs_root: bool
    description: str

    @property
    def size_human(self) -> str:
        from gigaorganize.utils.format import format_size
        return format_size(self.size_bytes)


@dataclass(slots=True)
class LogEntry:
    path: Path
    size_bytes: int
    modified: float
    deletable: bool


@dataclass(slots=True)
class CleanupScanResult:
    caches: list[CacheEntry]
    logs: list[LogEntry]
    trash_size: int
    total_cleanable: int
    scan_time_seconds: float
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class OrganizeAction:
    source: Path
    destination: Path
    rule_name: str
    action_type: str
    reason: str


@dataclass(slots=True)
class OrganizePlan:
    actions: list[OrganizeAction]
    source_dir: Path
    file_count: int
    conflicts: list[OrganizeAction] = field(default_factory=list)


@dataclass(slots=True)
class OrganizeResult:
    moved: int
    skipped: int
    errors: list[tuple[Path, str]]
    actions_taken: list[OrganizeAction]


@dataclass(slots=True)
class HardwareInfo:
    cpu_model: str = "Unknown"
    cpu_cores: int = 0
    cpu_threads: int = 0
    cpu_freq_mhz: float = 0.0
    ram_total_gb: float = 0.0
    ram_used_gb: float = 0.0
    gpu_name: str = "Unknown"
    gpu_driver: str = "Unknown"
    gpu_vram_gb: float = 0.0
    hostname: str = "Unknown"
    kernel: str = "Unknown"
    distro: str = "Unknown"
    desktop_env: str = "Unknown"
    display_server: str = "Unknown"


@dataclass(slots=True)
class PackageInfo:
    name: str
    version: str
    source: str
    size_bytes: Optional[int] = None


@dataclass(slots=True)
class ServiceInfo:
    name: str
    state: str
    description: str
    user_level: str


@dataclass(slots=True)
class SysInfoResult:
    hardware: HardwareInfo
    packages: list[PackageInfo]
    services: list[ServiceInfo]
    flatpak_apps: list[PackageInfo]
    brew_packages: list[PackageInfo]
    collect_time_seconds: float
