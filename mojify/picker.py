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
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk  # noqa: E402

from . import recents
from .emojis import BY_CHAR, CATEGORIES, display_name, search

# How many search results to show at once. Keeps the grid responsive on broad
# queries. Browsing a category always shows the whole category.
MAX_RESULTS = 200
# Number of emoji buttons per row in the grid. Fewer columns => larger cells
# and bigger glyphs.
COLUMNS = 7
# Fixed pixel size of the scrollable emoji grid. Pinning it keeps the window a
# constant size no matter how many emojis a tab/search shows.
GRID_WIDTH = 560
GRID_HEIGHT = 360
# Stylesheet bundled alongside this module.
STYLE_FILE = "style.css"
# Label of the synthetic, always-first "recently used" tab.
RECENT_KEY = "🕒  Recent"
# Maps a category's display name to its outline tab icon (mojify/icons/<x>.svg).
TAB_ICONS = {
    "Recent": "recent",
    "Smileys": "smileys",
    "Gestures": "gestures",
    "People": "people",
    "Animals": "animals",
    "Food": "food",
    "Travel": "travel",
    "Activities": "activities",
    "Objects": "objects",
    "Symbols": "symbols",
    "Arrows": "arrows",
    "Flags": "flags",
}
# Pixel size the tab icons are rendered at.
TAB_ICON_SIZE = 22
# Single colour every tab icon is tinted to, so mismatched source SVGs all
# render monochrome and on-theme.
TAB_ICON_RGB = (0xCD, 0xD6, 0xD0)


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


def _monochrome(pixbuf, rgb=TAB_ICON_RGB):
    """Recolour every visible pixel to ``rgb``, keeping alpha.

    Tints any source icon (line or filled, any colour) to a single on-theme
    colour so the tab bar stays monochrome regardless of what SVGs are dropped
    in. Anti-aliased edges blend naturally because alpha is preserved.
    """
    if not pixbuf.get_has_alpha():
        pixbuf = pixbuf.add_alpha(False, 0, 0, 0)
    width = pixbuf.get_width()
    height = pixbuf.get_height()
    stride = pixbuf.get_rowstride()
    data = bytearray(pixbuf.get_pixels())
    r, g, b = rgb
    for y in range(height):
        base = y * stride
        for x in range(width):
            i = base + x * 4
            if data[i + 3]:  # only where the pixel is visible
                data[i] = r
                data[i + 1] = g
                data[i + 2] = b
    return GdkPixbuf.Pixbuf.new_from_bytes(
        GLib.Bytes.new(bytes(data)),
        GdkPixbuf.Colorspace.RGB,
        True,
        8,
        width,
        height,
        stride,
    )


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


def notify_copied(char, name):
    """Show a brief desktop notification confirming the copy (best-effort)."""
    notify_send = shutil.which("notify-send")
    if notify_send is None:
        return
    try:
        subprocess.run(
            [notify_send, "--app-name=mojify", "--icon=mojify",
             "--expire-time=1500", f"Copied {char}", name],
            check=False,
        )
    except OSError:
        pass


class PickerWindow(Gtk.Window):
    """The floating emoji picker window."""

    def __init__(self, to_stdout=False, notify=True):
        super().__init__(title="mojify")

        # Behaviour: copy to clipboard (default) or print to stdout; whether to
        # show a desktop notification after a copy.
        self.to_stdout = to_stdout
        self.notify = notify

        # Ordered tab labels: a synthetic "Recent" tab first, then categories.
        self._tab_keys = [RECENT_KEY] + list(CATEGORIES)

        # Borderless, centered, always-on-top floating window.
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_keep_above(True)
        # Show in the taskbar/dock (with the app icon) while open. GNOME maps
        # the window to mojify.desktop via its app id — run --install-desktop.
        self.set_skip_taskbar_hint(False)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_default_size(600, 480)
        self.set_border_width(0)

        self._set_window_icon()
        self._apply_styles()

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        outer.get_style_context().add_class("mojify-root")
        self.add(outer)

        # Layout (top → bottom): category tabs, search box, emoji grid, and a
        # footer that names whatever emoji is hovered or focused.

        # Category tab bar. Browsing a tab shows that whole category; typing
        # in the search box temporarily overrides the tabs and searches all.
        # Start on Recent if there's any history, otherwise the first category.
        self.current_category = RECENT_KEY if recents.top(1) else next(iter(CATEGORIES))
        self._tab_buttons = {}
        outer.pack_start(self._build_tabs(), False, False, 0)

        # Search entry below the tabs.
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search emoji — e.g. fire, smile, heart")
        self.search_entry.get_style_context().add_class("mojify-search")
        self.search_entry.connect("search-changed", self._on_search_changed)
        self.search_entry.connect("activate", self._on_search_activate)
        outer.pack_start(self.search_entry, False, False, 0)

        # Scrollable area holding the results grid. Pin its size so the window
        # dimensions never depend on how many emojis are shown — otherwise a
        # sparse tab (e.g. an empty Recent) would shrink the whole window.
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        # Disable overlay (fading) scrollbars so the purple bar stays visible.
        scrolled.set_overlay_scrolling(False)
        # Fixed viewport: never grow/shrink to fit content.
        scrolled.set_propagate_natural_width(False)
        scrolled.set_propagate_natural_height(False)
        scrolled.set_min_content_width(GRID_WIDTH)
        scrolled.set_max_content_width(GRID_WIDTH)
        scrolled.set_min_content_height(GRID_HEIGHT)
        scrolled.set_max_content_height(GRID_HEIGHT)
        outer.pack_start(scrolled, True, True, 0)

        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_min_children_per_line(COLUMNS)
        self.flowbox.set_max_children_per_line(COLUMNS)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.flowbox.set_homogeneous(True)
        self.flowbox.get_style_context().add_class("mojify-grid")
        self.flowbox.connect("child-activated", self._on_child_activated)
        self.flowbox.connect("selected-children-changed", self._on_selection_changed)
        scrolled.add(self.flowbox)

        # Footer: names the hovered / focused emoji (so the grid itself can show
        # just the large glyphs, no per-cell label).
        self.footer = Gtk.Label(label="")
        self.footer.set_halign(Gtk.Align.START)
        self.footer.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        self.footer.get_style_context().add_class("mojify-footer")
        outer.pack_start(self.footer, False, False, 0)

        # Global key handling (Escape to close, arrows to navigate).
        self.connect("key-press-event", self._on_key_press)
        self.connect("destroy", Gtk.main_quit)

        self._populate("")

    def _build_tabs(self):
        """A horizontally-scrolling row of one toggle button per category.

        Each tab shows a monochrome outline icon (mojify/icons/), with the
        category name as a tooltip. Falls back to the emoji glyph if the icon
        can't be loaded.
        """
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        scroller.get_style_context().add_class("mojify-tabs")

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        scroller.add(row)

        for name in self._tab_keys:
            emoji, _, label = name.partition("  ")
            btn = Gtk.ToggleButton()
            image = self._tab_image(label)
            if image is not None:
                btn.set_image(image)
                btn.set_always_show_image(True)
            else:
                btn.set_label(emoji)
            btn.set_tooltip_text(label or emoji)
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.get_style_context().add_class("mojify-tab")
            btn.set_active(name == self.current_category)
            btn.connect("clicked", self._on_tab_clicked, name)
            self._tab_buttons[name] = btn
            row.pack_start(btn, False, False, 0)

        return scroller

    def _tab_image(self, label):
        """Load a category's tab icon, tinted monochrome, or None if missing."""
        import os

        fname = TAB_ICONS.get(label)
        if not fname:
            return None
        path = os.path.join(os.path.dirname(__file__), "icons", f"{fname}.svg")
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                path, TAB_ICON_SIZE, TAB_ICON_SIZE
            )
            return Gtk.Image.new_from_pixbuf(_monochrome(pixbuf))
        except Exception:
            return None

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

        # Themed name (resolves once --install-desktop has placed the icon in
        # the hicolor theme) plus a direct file fallback from the package.
        self.set_icon_name("mojify")
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

    def _make_cell(self, char, child):
        """Build a single emoji cell: just the large glyph.

        The name isn't shown per-cell. Hovering selects this ``child`` so the
        highlight follows the cursor (and stays on the last one hovered); the
        footer updates via the selection-changed handler. An EventBox wraps the
        label so we can catch hover (enter) events.
        """
        ebox = Gtk.EventBox()
        ebox.get_style_context().add_class("mojify-cell")
        # Input-only: receive hover events without painting over the cell's
        # selection highlight (which lives on the flowboxchild).
        ebox.set_visible_window(False)
        ebox.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK)
        ebox.connect("enter-notify-event", self._on_cell_hover, child)

        emoji_label = Gtk.Label(label=char)
        emoji_label.get_style_context().add_class("mojify-emoji")
        ebox.add(emoji_label)
        return ebox

    def _set_footer(self, char, name):
        self.footer.set_text(f"{char}   {display_name(name)}" if char else "")

    def _on_cell_hover(self, _widget, _event, child):
        # Move the selection (the mint highlight) to the hovered cell. It stays
        # there until another cell is hovered or the arrows move it.
        self.flowbox.select_child(child)
        return False

    def _on_selection_changed(self, flowbox):
        """Selection moves via hover or arrow keys; mirror it in the footer."""
        selected = flowbox.get_selected_children()
        if selected:
            child = selected[0]
            self._set_footer(getattr(child, "emoji_char", ""), getattr(child, "emoji_name", ""))

    def _populate(self, query):
        """Refresh the grid.

        With a query, show search results across all categories. With an empty
        query, browse the currently-selected category tab.
        """
        for child in self.flowbox.get_children():
            self.flowbox.remove(child)

        if query.strip():
            results = search(query, limit=MAX_RESULTS)
        elif self.current_category == RECENT_KEY:
            results = recents.top()
        else:
            results = CATEGORIES[self.current_category]

        for char, name, _keywords in results:
            child = Gtk.FlowBoxChild()
            child.emoji_char = char  # stash for later retrieval
            child.emoji_name = name
            child.add(self._make_cell(char, child))
            self.flowbox.add(child)

        self.flowbox.show_all()

        if not results and self.current_category == RECENT_KEY and not query.strip():
            self._set_footer("", "")
            self._show_placeholder("No recents yet — pick an emoji and it lands here.")
            return

        # Pre-select the first result so Enter works immediately (also updates
        # the footer via the selection-changed handler).
        first = self.flowbox.get_child_at_index(0)
        if first is not None:
            self.flowbox.select_child(first)

    def _show_placeholder(self, text):
        """Drop a single, non-selectable hint row into the empty grid."""
        child = Gtk.FlowBoxChild()
        child.set_can_focus(False)
        label = Gtk.Label(label=text)
        label.get_style_context().add_class("mojify-name")
        child.add(label)
        self.flowbox.add(child)
        self.flowbox.show_all()

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
            recents.record(char)
            if self.to_stdout:
                # Print the bare emoji so it composes in shell pipelines.
                sys.stdout.write(char)
                sys.stdout.flush()
            elif copy_to_clipboard(char) and self.notify:
                entry = BY_CHAR.get(char)
                notify_copied(char, entry[1] if entry else "")
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


def run_picker(to_stdout=False, notify=True):
    """Launch the picker window and run the GTK main loop."""
    # Advertise a stable app id. On Wayland this becomes the window's app_id /
    # WM_CLASS, which GNOME matches against `mojify.desktop` (StartupWMClass)
    # to show the logo in the dock/overview. See `mojify --install-desktop`.
    GLib.set_prgname("mojify")
    GLib.set_application_name("mojify")

    win = PickerWindow(to_stdout=to_stdout, notify=notify)
    win.connect("focus-out-event", lambda *_: win.close())
    win.show_all()
    win.search_entry.grab_focus()
    # Ensure the window paints promptly on Wayland.
    GLib.idle_add(win.present)
    Gtk.main()
