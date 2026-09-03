# GigaOrganize

Linux system organizer built with GTK4 + libadwaita.

## Features

- **Disk Usage** — see how space is split across your folders.
- **Duplicate Detection** — find duplicate files (optional fast `xxhash` mode).
- **Cleanup** — move caches to a recoverable `.gigaorganize-trash` bin (nothing
  is hard-deleted; you empty the bin yourself).
- **File Organizer** — sort files into folders.
- **System Info** — quick system details.

## Safety

GigaOrganize **never permanently deletes user data**. Cleanup moves items to a
hidden recoverable bin, and it never auto-empties the system trash. You control
what gets removed.

## Install

```sh
pip install --user .
```

Launch with:

```sh
gigaorganize
```

## Requirements

- Python 3.12+
- PyGObject (GTK4 / libadwaita)
- send2trash

Optional: `xxhash` for faster duplicate detection.

## Development

```sh
pip install -e .
```

## License

MIT — see [LICENSE](LICENSE).
