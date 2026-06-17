"""Tests for the recently-used emoji store."""

import importlib

import pytest


@pytest.fixture
def recents(tmp_path, monkeypatch):
    """A fresh recents module pointed at an isolated state dir."""
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    import mojify.recents as module

    return importlib.reload(module)


def test_empty_by_default(recents):
    assert recents.top() == []


def test_record_and_rank_by_frequency(recents):
    recents.record("🔥")
    recents.record("🔥")
    recents.record("🚀")
    ranked = [entry[0] for entry in recents.top()]
    assert ranked[:2] == ["🔥", "🚀"]


def test_recency_breaks_ties(recents):
    recents.record("🔥")
    recents.record("🚀")  # same count, but more recent
    ranked = [entry[0] for entry in recents.top()]
    assert ranked[:2] == ["🚀", "🔥"]


def test_top_respects_limit(recents):
    for char in ["🔥", "🚀", "❤️", "😀"]:
        recents.record(char)
    assert len(recents.top(limit=2)) == 2


def test_persists_across_reload(recents, tmp_path, monkeypatch):
    recents.record("🔥")
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    import mojify.recents as module

    reloaded = importlib.reload(module)
    assert [e[0] for e in reloaded.top()] == ["🔥"]


def test_unknown_characters_are_dropped(recents):
    recents.record("🔥")
    recents.record("xyz-not-an-emoji")  # not in the dataset
    assert [e[0] for e in recents.top()] == ["🔥"]


def test_corrupt_file_is_ignored(recents):
    recents._state_dir().mkdir(parents=True, exist_ok=True)
    recents._state_file().write_text("}{ not json")
    assert recents.top() == []
    # And recording still works (overwrites the garbage).
    recents.record("🔥")
    assert [e[0] for e in recents.top()] == ["🔥"]
