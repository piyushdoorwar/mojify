# Claude project guide — mojify

Context for Claude (and humans) working in this repo.

## What this is

`mojify` is a **Wayland-native emoji picker** for Ubuntu/GNOME, published on
PyPI (`pip install mojify`). The user presses a keyboard shortcut, searches for
an emoji, and it's copied to the clipboard — they paste it with `Ctrl + V`.
The launch shortcut documented in the README is `Super + .`.

## Core design constraints — do not break these

- **Wayland-first.** No `xdotool`, `ydotool`, `rofi`, or any keystroke
  injection. Wayland blocks synthetic input into other apps, so mojify is
  **clipboard-based by design**: copy the emoji, the user pastes it. This is
  the project's whole reason for existing — keep it that way.
- **Minimal dependencies.** The UI uses **GTK3 via PyGObject**, which already
  ships with Ubuntu's GNOME desktop, so it is intentionally **NOT** a declared
  PyPI dependency. The only external runtime requirement is **`wl-clipboard`**
  (the `wl-copy` binary), installed via apt. Do not add heavy deps.
- **Fully offline.** The emoji dataset is bundled in the package. No external
  API or network calls.

## Layout

```
mojify/
├── mojify/
│   ├── __init__.py     # __version__ lives here
│   ├── __main__.py     # CLI: launch / --version / --list
│   ├── picker.py       # GTK3 floating picker window + clipboard
│   └── emojis.py       # CATEGORIES dict + flat EMOJIS + search()
├── .github/
│   ├── workflows/publish.yml   # PyPI publish on GitHub Release
│   └── claude.md               # this file
├── pyproject.toml      # all packaging metadata
├── setup.py            # thin shim → setuptools
├── README.md
└── LICENSE             # MIT
```

## Emoji data (`emojis.py`)

- `CATEGORIES` is an **ordered dict**: `"😀  Smileys"` → list of
  `(character, name, keywords)` tuples. The dict keys are `"<emoji>  <Name>"`;
  the picker uses the leading emoji as the tab icon and the name as a tooltip.
- `EMOJIS` is derived from `CATEGORIES` (flat view) and is what `search()` and
  `mojify --list` operate on.
- **Adding emojis:** append `(char, name, keywords)` to the right category
  list. Give generous, lowercase `keywords` — they make search forgiving.
  Keep every `character` unique across the whole dataset.
- `search()` ranks: exact name → name prefix → name substring → keyword
  (word-anchored). Don't make keyword matching a loose substring (it caused
  "art" to match "heart").

## UI (`picker.py`)

- Borderless, centered, always-on-top, closes on Escape / focus-loss /
  selection. Search box on top, a row of category tabs, then the emoji grid.
- Typing searches across **all** categories and clears the tab highlight;
  clearing the search restores the current category view.
- Clipboard goes through `wl-copy` in `copy_to_clipboard()`.

## CLI (`__main__.py`)

- `mojify` launches the picker; `--version` and `--list` work **without** GTK
  (the picker is imported lazily) so scripting works on headless machines.

## Conventions

- Python **3.8+** compatible.
- The GUI can't be exercised in a headless CI/sandbox (needs a Wayland/X
  display). Validate logic via imports, `--list`, and `search()`; note when a
  change is UI-only and unverified live.
- Bump `__version__` in `mojify/__init__.py` **and** `version` in
  `pyproject.toml` together before cutting a release.

## Releasing

Versioning is automatic via **setuptools-scm** — the version comes from the
git tag, so never hardcode it. Publishing is automated by
[`.github/workflows/publish.yml`](workflows/publish.yml):

- **build** runs on every push/PR (and tags); **publish** runs only for pushed
  `v*` tags.
- To release: `git tag vX.Y.Z && git push origin vX.Y.Z`. The tag sets the
  version and triggers the PyPI upload.

Authentication uses **PyPI Trusted Publishing (OIDC)** — no API token or
secret. The publish job has `id-token: write` and uses
`pypa/gh-action-pypi-publish`. This requires a one-time trusted-publisher
config on PyPI (repo `piyushdoorwar/mojify`, workflow `publish.yml`,
environment `pypi`).
