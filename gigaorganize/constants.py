from pathlib import Path

APP_ID = "com.gigaorganize.app"
APP_NAME = "GigaOrganize"
APP_VERSION = "1.0.0"

HOME = Path.home()

MAX_SCAN_DEPTH = 10
MAX_ENTRIES_DISPLAY = 200
PROGRESS_EMIT_INTERVAL = 50

PARTIAL_HASH_SIZE = 16384
CHUNK_SIZE = 65536
MIN_DUPLICATE_SIZE = 1024

CACHE_LOCATIONS = [
    ("pip", [HOME / ".cache" / "pip"], "Python pip cache"),
    ("npm", [HOME / ".cache" / "npm"], "npm cache"),
    ("yarn", [HOME / ".cache" / "yarn"], "yarn cache"),
    ("Homebrew", [HOME / ".cache" / "Homebrew"], "Homebrew cache"),
    ("Flatpak", [
        Path("/var/lib/flatpak"),
        HOME / ".local" / "share" / "flatpak",
    ], "Flatpak app/runtime data"),
    ("cargo", [HOME / ".cache" / "cargo"], "Rust cargo cache"),
    ("gradle", [HOME / ".cache" / "gradle"], "Gradle build cache"),
    ("google-chrome", [HOME / ".cache" / "google-chrome"], "Google Chrome cache"),
    ("spotify", [HOME / ".cache" / "spotify"], "Spotify cache"),
    ("mozilla", [HOME / ".cache" / "mozilla"], "Mozilla/Firefox cache"),
    ("dconf", [HOME / ".cache" / "dconf"], "dconf cache"),
    ("thumbnails", [HOME / ".cache" / "thumbnail"], "Thumbnail cache"),
    ("mesa_shader", [HOME / ".cache" / "mesa_shader_cache"], "Mesa shader cache"),
    ("fontconfig", [HOME / ".cache" / "fontconfig"], "Fontconfig cache"),
    ("trash", [HOME / ".local" / "share" / "Trash"], "Trash"),
]

LOG_LOCATIONS = [
    Path("/var/log"),
    HOME / ".local" / "share" / "journal",
]

FILE_CATEGORIES = {
    "Documents": {".pdf", ".docx", ".doc", ".txt", ".odt", ".rtf", ".epub",
                  ".xlsx", ".xls", ".csv", ".pptx", ".ppt", ".tex", ".md"},
    "Images":    {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp",
                  ".ico", ".tiff", ".raw", ".heic", ".avif"},
    "Videos":    {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv",
                  ".m4v", ".3gp"},
    "Music":     {".mp3", ".flac", ".ogg", ".aac", ".wav", ".wma", ".opus",
                  ".m4a", ".aiff"},
    "Archives":  {".zip", ".tar", ".gz", ".xz", ".7z", ".rar", ".bz2",
                  ".tgz"},
    "Installers":{".deb", ".rpm", ".flatpak", ".flatpakref", ".appimage",
                  ".snap"},
    "Code":      {".py", ".js", ".ts", ".rs", ".go", ".c", ".cpp", ".h",
                  ".java", ".sh", ".bash", ".zsh", ".lua", ".rb"},
}

EXT_TO_CATEGORY = {}
for cat, exts in FILE_CATEGORIES.items():
    for ext in exts:
        EXT_TO_CATEGORY[ext] = cat

DEFAULT_ORGANIZE_TARGET = HOME / "Documents" / "GigaOrganize"

WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 600
