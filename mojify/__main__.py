"""Command-line entry point for mojify.

Usage:
    mojify                    Launch the emoji picker
    mojify --version          Print the version and exit
    mojify --list             Print every bundled emoji to stdout (for scripting)
    mojify --install-desktop  Register mojify in the GNOME app grid / dock
    mojify --uninstall-desktop Remove that registration
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__
from .emojis import EMOJIS

# Desktop entry installed by --install-desktop. `StartupWMClass` must match the
# app id the window advertises (see picker.run_picker) so GNOME maps the running
# window to this entry and shows the logo in the dock.
DESKTOP_ENTRY = """\
[Desktop Entry]
Type=Application
Version=1.0
Name=mojify
GenericName=Emoji Picker
Comment=Search emoji and copy to the clipboard (Wayland-native)
Exec={exec_cmd}
Icon=mojify
Terminal=false
Categories=Utility;GTK;
Keywords=emoji;emoticon;picker;clipboard;smiley;
StartupWMClass=mojify
"""


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
    parser.add_argument(
        "--install-desktop",
        action="store_true",
        help="register mojify in the GNOME app grid / dock with its icon",
    )
    parser.add_argument(
        "--uninstall-desktop",
        action="store_true",
        help="remove the desktop entry and icon installed by --install-desktop",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="print the chosen emoji to stdout instead of copying to the clipboard",
    )
    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="do not show a desktop notification after copying",
    )
    return parser


def print_list():
    """Print every emoji as a tab-separated line: char<TAB>name<TAB>keywords."""
    for char, name, keywords in EMOJIS:
        print(f"{char}\t{name}\t{keywords}")


def _data_home():
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))


def _desktop_path():
    return _data_home() / "applications" / "mojify.desktop"


def _icon_path():
    return _data_home() / "icons" / "hicolor" / "scalable" / "apps" / "mojify.svg"


def _refresh_caches():
    """Best-effort refresh of the desktop/icon caches (no-op if tools absent)."""
    commands = [
        ["update-desktop-database", str(_desktop_path().parent)],
        ["gtk-update-icon-cache", str(_data_home() / "icons" / "hicolor")],
    ]
    for cmd in commands:
        try:
            subprocess.run(cmd, check=False, capture_output=True)
        except FileNotFoundError:
            pass  # tool not installed; the entry still works


def install_desktop():
    """Install a .desktop file and icon so mojify appears as a desktop app."""
    icon_dst = _icon_path()
    desktop_dst = _desktop_path()
    icon_dst.parent.mkdir(parents=True, exist_ok=True)
    desktop_dst.parent.mkdir(parents=True, exist_ok=True)

    icon_src = Path(__file__).with_name("logo.svg")
    shutil.copyfile(icon_src, icon_dst)

    # Prefer an absolute path to the launcher so GNOME can run it regardless of
    # whether ~/.local/bin is on the session PATH.
    exec_cmd = shutil.which("mojify") or "mojify"
    desktop_dst.write_text(DESKTOP_ENTRY.format(exec_cmd=exec_cmd))

    _refresh_caches()
    print("Installed mojify desktop entry:")
    print(f"  {desktop_dst}")
    print(f"  {icon_dst}")
    print("\nIt should now appear in the app grid and dock. You may need to log")
    print("out/in (or restart GNOME Shell) for the icon to refresh.")
    return 0


def uninstall_desktop():
    """Remove the files installed by --install-desktop."""
    removed = False
    for path in (_desktop_path(), _icon_path()):
        if path.exists():
            path.unlink()
            print(f"Removed {path}")
            removed = True
    if not removed:
        print("Nothing to remove — mojify desktop entry was not installed.")
    _refresh_caches()
    return 0


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list:
        print_list()
        return 0

    if args.install_desktop:
        return install_desktop()

    if args.uninstall_desktop:
        return uninstall_desktop()

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

    run_picker(to_stdout=args.stdout, notify=not args.no_notify)
    return 0


if __name__ == "__main__":
    sys.exit(main())
