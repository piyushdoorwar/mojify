# mojify 🔥

**A Wayland-native emoji picker for Ubuntu/GNOME.**

Press a shortcut, type to search, hit Enter — the emoji is copied to your
clipboard. Paste it anywhere with `Ctrl + V`.

```
pip install mojify
```

---

## Why it exists

GNOME's built-in emoji picker only works inside GTK apps, and most
third-party pickers (rofi-emoji, etc.) rely on `xdotool` / `ydotool` to *type*
the emoji — which **does not work on Wayland** because Wayland blocks programs
from synthesizing keystrokes into other apps for security reasons.

**mojify takes the Wayland-friendly route:** it copies the emoji to your
clipboard and lets you paste it yourself with `Ctrl + V`. That works in *every*
application — your terminal, browser, editor, chat app, anywhere — with no
input-injection hacks.

It's built on **GTK3 (PyGObject)**, which already ships with Ubuntu's GNOME
desktop, so the only thing you need to add is the clipboard helper.

---

## Install

```bash
pip install mojify
```

### Required dependency: `wl-clipboard`

mojify uses `wl-copy` to put the emoji on your clipboard:

```bash
sudo apt install wl-clipboard
```

> GTK3 / PyGObject already come with Ubuntu's GNOME desktop. If you're on a
> stripped-down system and the picker won't start, install them with:
> `sudo apt install python3-gi gir1.2-gtk-3.0`

---

## Usage

Launch the picker directly:

```bash
mojify
```

Other commands:

```bash
mojify --version    # print the version
mojify --list       # print every bundled emoji (char<TAB>name<TAB>keywords)
```

`--list` is handy for scripting, e.g. piping into your own fuzzy finder:

```bash
mojify --list | fzf | cut -f1 | wl-copy
```

---

## Set up the `Ctrl + .` keyboard shortcut (GNOME)

The whole point is to summon mojify with one keystroke. Bind it as a custom
shortcut:

1. Open **Settings → Keyboard → View and Customize Shortcuts**.
2. Scroll to the bottom and click **Custom Shortcuts**, then the **+** button.
3. Fill in:
   - **Name:** `mojify`
   - **Command:** `mojify`
     *(if that doesn't work, use the absolute path — run `which mojify` to find it, e.g. `/home/you/.local/bin/mojify`)*
   - **Shortcut:** press `Ctrl + .`
4. Click **Add**.

Now press `Ctrl + .` anywhere and the picker pops up.

> **Tip:** if you installed with `pip install --user`, make sure
> `~/.local/bin` is on your `PATH`, or just use the absolute path in the
> command field.

---

## How it works

1. Press your shortcut (e.g. `Ctrl + .`).
2. A small floating search window appears in the center of the screen,
   always on top, with no titlebar.
3. Start typing to **search emojis by name or keyword** (`fire`, `smile`,
   `heart`, `rocket`, …). Results update in real time.
4. Use **arrow keys** to move through the grid, or click with the mouse.
5. Press **Enter** (or click) to select. The emoji is copied to your
   clipboard and the window closes instantly.
6. Press **`Ctrl + V`** wherever you want the emoji.
7. Press **Escape** at any time to dismiss the picker without selecting.

---

## Known limitation

**You have to paste manually with `Ctrl + V`.** mojify cannot type the emoji
into the focused app for you, because Wayland deliberately prevents
applications from injecting keystrokes into other windows. Copy-to-clipboard
is the robust, secure way to do this on Wayland — and it works everywhere.

---

## Project layout

```
mojify/
├── mojify/
│   ├── __init__.py
│   ├── __main__.py     # CLI entry point (python -m mojify / `mojify`)
│   ├── picker.py       # GTK3 floating picker window
│   └── emojis.py       # bundled emoji dataset + search
├── setup.py
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## Contributing

Contributions are very welcome! 🎉

1. **Fork** the repo and create a feature branch.
2. Make your change. The codebase is small and dependency-light:
   - **Adding emojis?** Edit [`mojify/emojis.py`](mojify/emojis.py). Each entry
     is a `(character, name, keywords)` tuple. Add generous keywords —
     they're what make search forgiving.
   - **UI tweaks?** They live in [`mojify/picker.py`](mojify/picker.py).
3. Test locally with an editable install:
   ```bash
   pip install -e .
   mojify
   ```
4. Open a pull request describing the change.

Please keep the zero-heavy-dependency philosophy: GTK3 (already on Ubuntu) for
the UI and `wl-clipboard` for the clipboard — nothing more.

---

## License

[MIT](LICENSE) © 2026 Piyush Doorwar
