#!/usr/bin/env python3
"""GigaOrganize — Linux system organizer (package entry point)."""

import sys

from gi.repository import Gio

from gigaorganize.app import GigaOrganizeApp


def main():
    app = GigaOrganizeApp(
        application_id="com.gigaorganize.app",
        flags=Gio.ApplicationFlags.FLAGS_NONE,
    )
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
