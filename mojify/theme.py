"""Theme helpers: bundled fonts, OS light/dark detection, and the stylesheet.

Kept free of GTK imports at module level so the decision logic is testable
headlessly. ``Gio``/``Gtk`` are imported lazily by the functions that need a
running desktop session.

The stylesheet is split in two:

* ``colors-light.css`` / ``colors-dark.css`` — one ``@define-color`` palette
  per scheme (GTK3 CSS has no custom properties, so named colours stand in).
* ``style.css`` — the rules, which only reference those ``@names``.

``build_css(scheme)`` concatenates the matching palette with ``style.css`` so a
single ``Gtk.CssProvider`` can be reloaded in place when the OS scheme flips.
"""

import ctypes
import ctypes.util
import os
import re

LIGHT = "light"
DARK = "dark"

# Debug-only override (e.g. for screenshots): MOJIFY_COLOR_SCHEME=light|dark.
ENV_OVERRIDE = "MOJIFY_COLOR_SCHEME"

# Values of org.freedesktop.appearance color-scheme (XDG desktop portal).
PORTAL_NO_PREFERENCE = 0
PORTAL_PREFER_DARK = 1
PORTAL_PREFER_LIGHT = 2

PORTAL_BUS_NAME = "org.freedesktop.portal.Desktop"
PORTAL_OBJECT_PATH = "/org/freedesktop/portal/desktop"
PORTAL_SETTINGS_IFACE = "org.freedesktop.portal.Settings"
APPEARANCE_NAMESPACE = "org.freedesktop.appearance"
COLOR_SCHEME_KEY = "color-scheme"
# Keep startup snappy even if the portal is wedged.
PORTAL_TIMEOUT_MS = 500

FONT_DIR = "fonts"
STYLE_FILE = "style.css"
PALETTE_FILES = {LIGHT: "colors-light.css", DARK: "colors-dark.css"}


# --------------------------------------------------------------------------
# Fonts
# --------------------------------------------------------------------------

def _package_dir():
    return os.path.dirname(os.path.abspath(__file__))


def bundled_font_files(font_dir=None):
    """Return the absolute paths of the bundled ``.ttf``/``.otf`` files."""
    font_dir = font_dir or os.path.join(_package_dir(), FONT_DIR)
    try:
        names = sorted(os.listdir(font_dir))
    except OSError:
        return []
    return [
        os.path.join(font_dir, name)
        for name in names
        if name.lower().endswith((".ttf", ".otf"))
    ]


def _load_fontconfig():
    """Load libfontconfig via ctypes, or return ``None`` if unavailable."""
    candidates = ["libfontconfig.so.1"]
    found = ctypes.util.find_library("fontconfig")
    if found and found not in candidates:
        candidates.append(found)
    for name in candidates:
        try:
            return ctypes.CDLL(name)
        except OSError:
            continue
    return None


def register_fonts(font_dir=None, loader=_load_fontconfig):
    """Make the bundled fonts available to this process only.

    Uses fontconfig's ``FcConfigAppFontAddFile`` on the current config, so
    nothing is installed system-wide. Must run before the first widget is
    created (i.e. before Pango builds its font map). Never raises: on any
    failure the picker simply falls back to system fonts.

    Returns the number of font files registered.
    """
    files = bundled_font_files(font_dir)
    if not files:
        return 0
    try:
        lib = loader()
        if lib is None:
            return 0
        add_file = lib.FcConfigAppFontAddFile
        add_file.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        add_file.restype = ctypes.c_int
        added = 0
        for path in files:
            # NULL config = the current (default) configuration.
            if add_file(None, os.fsencode(path)):
                added += 1
        return added
    except Exception:  # noqa: BLE001 - cosmetic, must never block the picker
        return 0


# --------------------------------------------------------------------------
# Colour scheme decision
# --------------------------------------------------------------------------

def _unwrap(value):
    """Peel nested 1-tuples / GLib variants down to a plain value."""
    for _ in range(4):
        if hasattr(value, "unpack"):
            value = value.unpack()
        elif isinstance(value, (tuple, list)) and len(value) == 1:
            value = value[0]
        else:
            break
    return value


def decide_scheme(portal_value=None, gtk_prefer_dark=False, gtk_theme_name=None,
                  override=None):
    """Pick ``"light"`` or ``"dark"``.

    Order: explicit ``override`` (debug env var) -> portal ``color-scheme``
    (1 dark, 2 light) -> GTK's prefer-dark setting -> a GTK theme name ending
    in ``-dark`` -> light.
    """
    if override:
        override = str(override).strip().lower()
        if override in (LIGHT, DARK):
            return override

    portal_value = _unwrap(portal_value)
    try:
        portal_value = int(portal_value) if portal_value is not None else None
    except (TypeError, ValueError):
        portal_value = None
    if portal_value == PORTAL_PREFER_DARK:
        return DARK
    if portal_value == PORTAL_PREFER_LIGHT:
        return LIGHT

    if gtk_prefer_dark:
        return DARK
    if gtk_theme_name and str(gtk_theme_name).strip().lower().endswith("-dark"):
        return DARK
    return LIGHT


def read_portal_color_scheme(bus=None):
    """Read the portal's ``color-scheme`` value, or ``None`` if unavailable."""
    try:
        from gi.repository import Gio, GLib

        if bus is None:
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        args = GLib.Variant("(ss)", (APPEARANCE_NAMESPACE, COLOR_SCHEME_KEY))
        # ReadOne (portal v2+) first, then the deprecated Read.
        for method in ("ReadOne", "Read"):
            try:
                reply = bus.call_sync(
                    PORTAL_BUS_NAME, PORTAL_OBJECT_PATH, PORTAL_SETTINGS_IFACE,
                    method, args, None, Gio.DBusCallFlags.NONE,
                    PORTAL_TIMEOUT_MS, None,
                )
            except Exception:  # noqa: BLE001
                continue
            value = _unwrap(reply)
            return int(value)
    except Exception:  # noqa: BLE001
        pass
    return None


def _gtk_fallback():
    """Return ``(prefer_dark, theme_name)`` from ``Gtk.Settings``."""
    try:
        from gi.repository import Gtk

        settings = Gtk.Settings.get_default()
        if settings is None:
            return False, None
        return (
            bool(settings.get_property("gtk-application-prefer-dark-theme")),
            settings.get_property("gtk-theme-name"),
        )
    except Exception:  # noqa: BLE001
        return False, None


def current_scheme(bus=None):
    """Resolve the scheme from the environment, the portal, then GTK."""
    override = os.environ.get(ENV_OVERRIDE)
    if override and override.strip().lower() in (LIGHT, DARK):
        return override.strip().lower()
    prefer_dark, theme_name = _gtk_fallback()
    return decide_scheme(read_portal_color_scheme(bus), prefer_dark, theme_name)


class SchemeWatcher:
    """Calls ``callback(scheme)`` whenever the effective OS scheme changes.

    Listens to the portal's ``SettingChanged`` signal plus the GTK settings
    used as fallbacks. Inert when the debug override is set.
    """

    def __init__(self, callback, initial=None):
        self._callback = callback
        self._scheme = initial
        self._bus = None
        self._sub_id = None
        self._gtk_handlers = []
        if os.environ.get(ENV_OVERRIDE):
            return
        try:
            from gi.repository import Gio

            self._bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            self._sub_id = self._bus.signal_subscribe(
                PORTAL_BUS_NAME, PORTAL_SETTINGS_IFACE, "SettingChanged",
                PORTAL_OBJECT_PATH, None, Gio.DBusSignalFlags.NONE,
                self._on_portal_signal,
            )
        except Exception:  # noqa: BLE001
            self._bus = None
        try:
            from gi.repository import Gtk

            settings = Gtk.Settings.get_default()
            if settings is not None:
                for prop in ("gtk-application-prefer-dark-theme", "gtk-theme-name"):
                    self._gtk_handlers.append(
                        (settings, settings.connect(f"notify::{prop}", self._refresh))
                    )
        except Exception:  # noqa: BLE001
            pass

    def _on_portal_signal(self, _conn, _sender, _path, _iface, _signal, params):
        try:
            namespace, key, value = params.unpack()
        except Exception:  # noqa: BLE001
            return
        if namespace != APPEARANCE_NAMESPACE or key != COLOR_SCHEME_KEY:
            return
        prefer_dark, theme_name = _gtk_fallback()
        self._emit(decide_scheme(value, prefer_dark, theme_name))

    def _refresh(self, *_args):
        self._emit(current_scheme(self._bus))

    def _emit(self, scheme):
        if scheme != self._scheme:
            self._scheme = scheme
            self._callback(scheme)

    def close(self):
        if self._bus is not None and self._sub_id is not None:
            self._bus.signal_unsubscribe(self._sub_id)
        self._sub_id = None
        for settings, handler in self._gtk_handlers:
            settings.disconnect(handler)
        self._gtk_handlers = []


# --------------------------------------------------------------------------
# Stylesheet
# --------------------------------------------------------------------------

def _read_resource(name):
    try:
        from importlib.resources import files

        return (files(__package__) / name).read_bytes()
    except (ImportError, AttributeError, FileNotFoundError, TypeError):
        # Python 3.8 or a non-standard layout: read next to this module.
        with open(os.path.join(_package_dir(), name), "rb") as handle:
            return handle.read()


def build_css(scheme):
    """Return the palette for ``scheme`` followed by ``style.css``, as bytes."""
    palette = PALETTE_FILES.get(scheme, PALETTE_FILES[LIGHT])
    return _read_resource(palette) + b"\n" + _read_resource(STYLE_FILE)


_DEFINE_COLOR = re.compile(r"@define-color\s+([\w-]+)\s+#([0-9a-fA-F]{6})\s*;")


def palette_rgb(scheme, name):
    """Return ``(r, g, b)`` for a ``#rrggbb`` ``@define-color`` in a palette.

    Lets Python-drawn assets (the tinted tab icons) share the CSS palette.
    """
    text = _read_resource(PALETTE_FILES.get(scheme, PALETTE_FILES[LIGHT]))
    for match in _DEFINE_COLOR.finditer(text.decode("utf-8")):
        if match.group(1) == name:
            hexval = match.group(2)
            return tuple(int(hexval[i:i + 2], 16) for i in (0, 2, 4))
    raise KeyError(name)
