"""GTK3 picker window for mojify.

Renders a small, borderless, always-on-top floating window with a search
entry and a scrollable grid of emoji results. Selecting an emoji (by click or
Enter) copies it to the clipboard via ``wl-copy`` and closes the window.
"""

import shutil
import subprocess
import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402

from .emojis import CATEGORIES, search

# How many search results to show at once. Keeps the grid responsive on broad
# queries. Browsing a category always shows the whole category.
MAX_RESULTS = 200
# Number of emoji buttons per row in the grid.
COLUMNS = 6
# Stylesheet bundled alongside this module.
STYLE_FILE = "style.css"


def _load_css():
    """Return the bundled ``style.css`` as bytes (for ``load_from_data``)."""
    try:
        from importlib.resources import files

        return (files(__package__) / STYLE_FILE).read_bytes()
    except (ImportError, AttributeError, FileNotFoundError):
        # Python 3.8 (no importlib.resources.files) or a non-standard layout:
        # fall back to reading next to this module on disk.
        import os

        path = os.path.join(os.path.dirname(__file__), STYLE_FILE)
        with open(path, "rb") as handle:
            return handle.read()


def copy_to_clipboard(text):
    """Copy ``text`` to the Wayland clipboard using ``wl-copy``.

    Returns ``True`` on success. Falls back to printing a message if
    ``wl-copy`` is not installed.
    """
    wl_copy = shutil.which("wl-copy")
    if wl_copy is None:
        sys.stderr.write(
            "mojify: 'wl-copy' not found. Install it with:\n"
            "    sudo apt install wl-clipboard\n"
        )
        return False
    try:
        subprocess.run([wl_copy], input=text.encode("utf-8"), check=True)
        return True
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(f"mojify: wl-copy failed: {exc}\n")
        return False


class PickerWindow(Gtk.Window):
    """The floating emoji picker window."""

    def __init__(self):
        super().__init__(title="mojify")

        # Borderless, centered, always-on-top floating window.
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_default_size(600, 480)
        self.set_border_width(0)

        self._set_window_icon()
        self._apply_styles()

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        outer.get_style_context().add_class("mojify-root")
        self.add(outer)

        # Search entry at the top.
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search emoji — e.g. fire, smile, heart")
        self.search_entry.get_style_context().add_class("mojify-search")
        self.search_entry.connect("search-changed", self._on_search_changed)
        self.search_entry.connect("activate", self._on_search_activate)
        outer.pack_start(self.search_entry, False, False, 0)

        # Category tab bar. Browsing a tab shows that whole category; typing
        # in the search box temporarily overrides the tabs and searches all.
        self.current_category = next(iter(CATEGORIES))
        self._tab_buttons = {}
        outer.pack_start(self._build_tabs(), False, False, 0)

        # Scrollable area holding the results grid.
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        # Disable overlay (fading) scrollbars so the purple bar stays visible.
        scrolled.set_overlay_scrolling(False)
        outer.pack_start(scrolled, True, True, 0)

        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_min_children_per_line(COLUMNS)
        self.flowbox.set_max_children_per_line(COLUMNS)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.flowbox.set_homogeneous(True)
        self.flowbox.get_style_context().add_class("mojify-grid")
        self.flowbox.connect("child-activated", self._on_child_activated)
        scrolled.add(self.flowbox)

        # Global key handling (Escape to close, arrows to navigate).
        self.connect("key-press-event", self._on_key_press)
        self.connect("destroy", Gtk.main_quit)

        self._populate("")

    def _build_tabs(self):
        """A horizontally-scrolling row of one toggle button per category.

        The button label is just the category's leading emoji (the dict keys
        are like ``"😀  Smileys"``), with the full name shown as a tooltip.
        """
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        scroller.get_style_context().add_class("mojify-tabs")

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        scroller.add(row)

        for name in CATEGORIES:
            icon, _, label = name.partition("  ")
            btn = Gtk.ToggleButton(label=icon)
            btn.set_tooltip_text(label or icon)
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.get_style_context().add_class("mojify-tab")
            btn.set_active(name == self.current_category)
            btn.connect("clicked", self._on_tab_clicked, name)
            self._tab_buttons[name] = btn
            row.pack_start(btn, False, False, 0)

        return scroller

    def _sync_tab_buttons(self, active_name):
        """Visually mark ``active_name`` as the selected tab (or none if None)."""
        for name, btn in self._tab_buttons.items():
            btn.handler_block_by_func(self._on_tab_clicked)
            btn.set_active(name == active_name)
            btn.handler_unblock_by_func(self._on_tab_clicked)

    def _on_tab_clicked(self, _button, name):
        self.current_category = name
        # Switching tabs clears any active search so the category is visible.
        if self.search_entry.get_text():
            self.search_entry.set_text("")  # triggers _populate via search-changed
        else:
            self._sync_tab_buttons(name)
            self._populate("")
        self.search_entry.grab_focus()

    def _set_window_icon(self):
        """Use the bundled logo as the window/taskbar icon.

        Purely cosmetic — if the SVG loader (librsvg) is unavailable, silently
        carry on rather than blocking the picker.
        """
        import os

        path = os.path.join(os.path.dirname(__file__), "logo.svg")
        try:
            self.set_icon_from_file(path)
        except Exception:
            pass

    def _apply_styles(self):
        """Load the bundled ``style.css`` and apply it to the whole screen."""
        provider = Gtk.CssProvider()
        provider.load_from_data(_load_css())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _make_cell(self, char, name):
        """Build a single emoji cell (large glyph above its name)."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.get_style_context().add_class("mojify-cell")

        emoji_label = Gtk.Label(label=char)
        emoji_label.get_style_context().add_class("mojify-emoji")
        box.pack_start(emoji_label, False, False, 0)

        name_label = Gtk.Label(label=name)
        name_label.get_style_context().add_class("mojify-name")
        name_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        name_label.set_max_width_chars(12)
        box.pack_start(name_label, False, False, 0)

        return box

    def _populate(self, query):
        """Refresh the grid.

        With a query, show search results across all categories. With an empty
        query, browse the currently-selected category tab.
        """
        for child in self.flowbox.get_children():
            self.flowbox.remove(child)

        if query.strip():
            results = search(query, limit=MAX_RESULTS)
        else:
            results = CATEGORIES[self.current_category]

        for char, name, _keywords in results:
            child = Gtk.FlowBoxChild()
            child.emoji_char = char  # stash for later retrieval
            child.add(self._make_cell(char, name))
            self.flowbox.add(child)

        self.flowbox.show_all()

        # Pre-select the first result so Enter works immediately.
        first = self.flowbox.get_child_at_index(0)
        if first is not None:
            self.flowbox.select_child(first)

    def _on_search_changed(self, entry):
        # While a search is active no tab is "current"; clear the highlight so
        # it's obvious results span all categories. Restore it when cleared.
        self._sync_tab_buttons(None if entry.get_text().strip() else self.current_category)
        self._populate(entry.get_text())

    def _on_search_activate(self, _entry):
        """Enter pressed in the search box: pick the selected/first result."""
        selected = self.flowbox.get_selected_children()
        if selected:
            self._select_and_close(selected[0])
        else:
            first = self.flowbox.get_child_at_index(0)
            if first is not None:
                self._select_and_close(first)

    def _on_child_activated(self, _flowbox, child):
        self._select_and_close(child)

    def _select_and_close(self, child):
        char = getattr(child, "emoji_char", None)
        if char:
            copy_to_clipboard(char)
        self.close()

    def _on_key_press(self, _widget, event):
        keyval = event.keyval
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True

        # Let arrow keys drive the grid even while typing in the search box.
        if keyval in (
            Gdk.KEY_Up,
            Gdk.KEY_Down,
            Gdk.KEY_Left,
            Gdk.KEY_Right,
        ):
            if self.search_entry.has_focus():
                self.flowbox.child_focus(self._direction(keyval))
                return True
        return False

    @staticmethod
    def _direction(keyval):
        if keyval == Gdk.KEY_Up:
            return Gtk.DirectionType.UP
        if keyval == Gdk.KEY_Down:
            return Gtk.DirectionType.DOWN
        if keyval == Gdk.KEY_Left:
            return Gtk.DirectionType.LEFT
        return Gtk.DirectionType.RIGHT


def run_picker():
    """Launch the picker window and run the GTK main loop."""
    win = PickerWindow()
    win.connect("focus-out-event", lambda *_: win.close())
    win.show_all()
    win.search_entry.grab_focus()
    # Ensure the window paints promptly on Wayland.
    GLib.idle_add(win.present)
    Gtk.main()
