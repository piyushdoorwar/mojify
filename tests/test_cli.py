"""Tests for the command-line interface (the non-GUI paths)."""

import pytest

from mojify import __main__ as cli
from mojify.emojis import EMOJIS


def test_list_prints_every_emoji(capsys):
    assert cli.main(["--list"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert len(out) == len(EMOJIS)
    # Each line is tab-separated: char, name, keywords.
    char, name, _kw = out[0].split("\t")
    assert (char, name) == (EMOJIS[0][0], EMOJIS[0][1])


def test_version_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    assert "mojify" in capsys.readouterr().out


def test_install_and_uninstall_desktop(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))

    assert cli.main(["--install-desktop"]) == 0
    desktop = tmp_path / "applications" / "mojify.desktop"
    icon = tmp_path / "icons" / "hicolor" / "scalable" / "apps" / "mojify.svg"
    assert desktop.is_file() and icon.is_file()

    content = desktop.read_text()
    assert "StartupWMClass=mojify" in content
    assert "Icon=mojify" in content
    assert content.startswith("[Desktop Entry]")

    assert cli.main(["--uninstall-desktop"]) == 0
    assert not desktop.exists() and not icon.exists()


def test_uninstall_when_absent_is_ok(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert cli.main(["--uninstall-desktop"]) == 0
    assert "Nothing to remove" in capsys.readouterr().out
