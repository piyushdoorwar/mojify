"""Tests for the theme helpers (no GTK or display needed)."""

import pytest

from mojify import theme


# --- decide_scheme --------------------------------------------------------

@pytest.mark.parametrize(
    "portal, expected",
    [(1, "dark"), (2, "light"), ((1,), "dark"), (((2,),), "light")],
)
def test_portal_value_maps_to_scheme(portal, expected):
    # Plain ints and the nested tuples GLib.Variant.unpack() can return.
    assert theme.decide_scheme(portal) == expected


def test_portal_prefer_light_overrides_dark_gtk_settings():
    assert theme.decide_scheme(2, gtk_prefer_dark=True, gtk_theme_name="Adwaita-dark") == "light"


def test_portal_prefer_dark_overrides_light_gtk_settings():
    assert theme.decide_scheme(1, gtk_prefer_dark=False, gtk_theme_name="Adwaita") == "dark"


@pytest.mark.parametrize("portal", [0, None, "garbage", 7])
def test_no_portal_preference_falls_back_to_gtk(portal):
    assert theme.decide_scheme(portal) == "light"
    assert theme.decide_scheme(portal, gtk_prefer_dark=True) == "dark"
    assert theme.decide_scheme(portal, gtk_theme_name="Yaru-dark") == "dark"
    assert theme.decide_scheme(portal, gtk_theme_name="Adwaita-Dark ") == "dark"
    assert theme.decide_scheme(portal, gtk_theme_name="Yaru") == "light"
    assert theme.decide_scheme(portal, gtk_theme_name="darkish") == "light"


def test_override_beats_everything():
    assert theme.decide_scheme(1, override="light") == "light"
    assert theme.decide_scheme(2, override="DARK") == "dark"
    # An unknown override is ignored.
    assert theme.decide_scheme(1, override="sepia") == "dark"


def test_current_scheme_honours_env_override(monkeypatch):
    monkeypatch.setenv(theme.ENV_OVERRIDE, "dark")
    assert theme.current_scheme() == "dark"
    monkeypatch.setenv(theme.ENV_OVERRIDE, "light")
    assert theme.current_scheme() == "light"


# --- fonts ----------------------------------------------------------------

def test_bundled_fonts_present():
    files = theme.bundled_font_files()
    assert any(f.endswith("DMSans-VariableFont.ttf") for f in files)


def test_register_fonts_without_fontconfig_is_silent():
    assert theme.register_fonts(loader=lambda: None) == 0


def test_register_fonts_survives_loader_error():
    def boom():
        raise OSError("no libfontconfig")

    assert theme.register_fonts(loader=boom) == 0


def test_register_fonts_survives_missing_symbol():
    class NoSymbol:
        def __getattr__(self, name):
            raise AttributeError(name)

    assert theme.register_fonts(loader=lambda: NoSymbol()) == 0


def test_register_fonts_with_no_font_dir(tmp_path):
    assert theme.register_fonts(font_dir=str(tmp_path / "missing")) == 0


def test_register_fonts_calls_fontconfig_per_file():
    calls = []

    class FakeFn:
        def __call__(self, config, path):
            calls.append((config, path))
            return 1

    class FakeLib:
        FcConfigAppFontAddFile = FakeFn()

    added = theme.register_fonts(loader=lambda: FakeLib())
    assert added == len(theme.bundled_font_files()) == len(calls)
    assert all(config is None and path.endswith(b".ttf") for config, path in calls)


# --- stylesheet -----------------------------------------------------------

def test_palettes_define_the_same_names():
    import re

    names = {}
    for scheme in (theme.LIGHT, theme.DARK):
        css = theme._read_resource(theme.PALETTE_FILES[scheme]).decode()
        names[scheme] = set(re.findall(r"@define-color\s+([\w-]+)", css))
    assert names[theme.LIGHT] == names[theme.DARK]

    style = theme._read_resource(theme.STYLE_FILE).decode()
    style = re.sub(r"/\*.*?\*/", "", style, flags=re.S)  # drop comments
    used = set(re.findall(r"@([a-z_]+)\b", style))
    assert used <= names[theme.LIGHT], used - names[theme.LIGHT]


def test_build_css_prepends_the_scheme_palette():
    light = theme.build_css(theme.LIGHT).decode()
    dark = theme.build_css(theme.DARK).decode()
    assert "#0d7a5a" in light and "#7fe0b0" in dark
    assert light.index("@define-color") < light.index(".mojify-root")


def test_emoji_font_comes_first_in_the_grid():
    style = theme._read_resource(theme.STYLE_FILE).decode()
    block = style.split(".mojify-emoji {", 1)[1].split("}", 1)[0]
    family = block.split("font-family:", 1)[1].split(";", 1)[0]
    assert family.strip().startswith('"Noto Color Emoji"')
    assert "DM Sans" not in family


def test_palette_rgb_reads_tab_icon_colour():
    assert theme.palette_rgb(theme.LIGHT, "tab_icon") == (0x0F, 0x1A, 0x14)
    assert theme.palette_rgb(theme.DARK, "tab_icon") == (0xF3, 0xF4, 0xF5)
    with pytest.raises(KeyError):
        theme.palette_rgb(theme.DARK, "nope")
