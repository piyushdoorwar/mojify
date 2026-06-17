"""Tests for the emoji dataset and search ranking."""

from mojify.emojis import BY_CHAR, CATEGORIES, EMOJIS, _keyword_match, search


def test_flat_list_matches_categories():
    total = sum(len(items) for items in CATEGORIES.values())
    assert len(EMOJIS) == total
    assert len(EMOJIS) > 800  # comprehensive-ish


def test_no_duplicate_characters():
    chars = [entry[0] for entry in EMOJIS]
    assert len(chars) == len(set(chars))


def test_recent_first_tab_not_a_real_category():
    # The picker injects a synthetic "Recent" tab; it must not collide.
    assert not any(name.endswith("Recent") for name in CATEGORIES)


def test_by_char_lookup_is_complete():
    assert len(BY_CHAR) == len(EMOJIS)
    for char, name, _kw in EMOJIS:
        assert BY_CHAR[char] == (char, name, _kw)


def test_every_entry_has_three_fields():
    for entry in EMOJIS:
        assert len(entry) == 3
        char, name, keywords = entry
        assert char and isinstance(name, str) and isinstance(keywords, str)


def test_empty_query_returns_everything():
    assert len(search("")) == len(EMOJIS)
    assert len(search("   ")) == len(EMOJIS)


def test_limit_is_respected():
    assert len(search("", limit=10)) == 10
    assert len(search("face", limit=3)) == 3


def test_exact_name_ranks_first():
    assert search("fire")[0][0] == "🔥"
    assert search("rocket")[0][0] == "🚀"


def test_prefix_beats_keyword():
    # "heart" the name should come before keyword-only matches.
    results = search("heart")
    assert results[0][1].startswith("heart") or "heart" in results[0][1]


def test_keyword_match_is_word_anchored():
    # Keywords match at word starts, not as loose substrings: "lit" should
    # match the keyword "lit" but "it" should not match it mid-word.
    assert _keyword_match("lit", "hot flame lit trending")
    assert _keyword_match("trend", "hot flame lit trending")
    assert not _keyword_match("rend", "hot flame lit trending")
    assert not _keyword_match("it", "hot flame lit trending")


def test_search_is_case_insensitive():
    assert search("FIRE")[0][0] == "🔥"
