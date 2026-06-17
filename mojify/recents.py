"""Persistent 'recently / frequently used' emoji tracking.

Usage is stored as a small JSON file under the XDG state dir
(``~/.local/state/mojify/recent.json`` by default). Each selected emoji keeps a
hit count and a monotonically increasing sequence number, so the "Recent" tab
can rank by frequency with a most-recent tie-break.
"""

import json
import os
from pathlib import Path

from .emojis import BY_CHAR

# How many emojis the Recent tab shows.
RECENT_LIMIT = 48


def _state_dir():
    base = os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state")
    return Path(base) / "mojify"


def _state_file():
    return _state_dir() / "recent.json"


def _load_raw():
    """Return the stored mapping ``{char: {"count": int, "seq": int}}``."""
    try:
        with open(_state_file(), encoding="utf-8") as handle:
            data = json.load(handle)
    except (FileNotFoundError, ValueError, OSError):
        return {}
    # Be defensive about a hand-edited or corrupted file.
    if not isinstance(data, dict):
        return {}
    return data


def record(char):
    """Record one use of ``char`` and persist. Best-effort (never raises)."""
    data = _load_raw()
    next_seq = 1 + max((v.get("seq", 0) for v in data.values()), default=0)
    entry = data.get(char) if isinstance(data.get(char), dict) else {}
    data[char] = {"count": int(entry.get("count", 0)) + 1, "seq": next_seq}

    try:
        _state_dir().mkdir(parents=True, exist_ok=True)
        # Write atomically so a crash mid-write can't corrupt the file.
        tmp = _state_file().with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False)
        os.replace(tmp, _state_file())
    except OSError:
        pass  # persistence is a nicety, not worth crashing the picker over


def top(limit=RECENT_LIMIT):
    """Return up to ``limit`` recent emoji entries, most-used first.

    Only characters present in the bundled dataset are returned (so a stale
    file referencing removed emojis degrades gracefully).
    """
    data = _load_raw()

    def sort_key(item):
        _char, stats = item
        stats = stats if isinstance(stats, dict) else {}
        return (stats.get("count", 0), stats.get("seq", 0))

    ordered = sorted(data.items(), key=sort_key, reverse=True)
    entries = []
    for char, _stats in ordered:
        entry = BY_CHAR.get(char)
        if entry is not None:
            entries.append(entry)
        if len(entries) >= limit:
            break
    return entries
