"""mojify — a Wayland-native emoji picker for Ubuntu/GNOME.

Press a keyboard shortcut, search for an emoji, hit Enter, and it's copied
to your clipboard ready to paste with Ctrl+V.
"""

# Version comes from git tags via setuptools-scm. Prefer the file it generates
# at build time; fall back to installed package metadata; finally a dev default
# (e.g. running from a checkout with no tags / before a build).
try:
    from ._version import version as __version__
except ImportError:
    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            __version__ = version("mojify")
        except PackageNotFoundError:
            __version__ = "0.0.0+unknown"
    except ImportError:  # pragma: no cover - Python < 3.8
        __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
