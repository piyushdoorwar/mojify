"""Command-line entry point for mojify.

Usage:
    mojify             Launch the emoji picker
    mojify --version   Print the version and exit
    mojify --list      Print every bundled emoji to stdout (for scripting)
"""

import argparse
import sys

from . import __version__
from .emojis import EMOJIS


def build_parser():
    parser = argparse.ArgumentParser(
        prog="mojify",
        description="A Wayland-native emoji picker for Ubuntu/GNOME. "
        "Search, select, and it's copied to your clipboard — paste with Ctrl+V.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"mojify {__version__}",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="print all bundled emojis (character, name, keywords) to stdout",
    )
    return parser


def print_list():
    """Print every emoji as a tab-separated line: char<TAB>name<TAB>keywords."""
    for char, name, keywords in EMOJIS:
        print(f"{char}\t{name}\t{keywords}")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list:
        print_list()
        return 0

    # Default action: launch the picker. Import lazily so that --list and
    # --version work even on a machine without PyGObject/GTK installed.
    try:
        from .picker import run_picker
    except (ImportError, ValueError) as exc:
        sys.stderr.write(
            "mojify: could not load the GTK interface.\n"
            f"  {exc}\n\n"
            "The picker needs PyGObject + GTK3, which ship with Ubuntu's GNOME\n"
            "desktop. If missing, install them with:\n"
            "    sudo apt install python3-gi gir1.2-gtk-3.0\n"
        )
        return 1

    run_picker()
    return 0


if __name__ == "__main__":
    sys.exit(main())
