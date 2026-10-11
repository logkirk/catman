"""Tests for constants module."""

import pytest

from catman.constants import (
    ContentItem,
    ContentType,
    GameVariant,
    ReleaseChannel,
    CONTENT_CATALOG,
)


class TestGameVariant:
    def test_display_names(self):
        assert GameVariant.CDDA.display_name == "Cataclysm: Dark Days Ahead"
        assert GameVariant.BN.display_name == "Cataclysm: Bright Nights"
        assert GameVariant.TLG.display_name == "Cataclysm: The Last Generation"

    def test_short_names(self):
        assert GameVariant.CDDA.short_name == "CDDA"
        assert GameVariant.BN.short_name == "BN"
        assert GameVariant.TLG.short_name == "TLG"

    def test_github_repos(self):
        assert GameVariant.CDDA.github_repo == "CleverRaven/Cataclysm-DDA"
        assert GameVariant.BN.github_repo == "cataclysmbn/Cataclysm-BN"
        assert GameVariant.TLG.github_repo == "Cataclysm-TLG/Cataclysm-TLG"

    def test_has_stable(self):
        assert GameVariant.CDDA.has_stable is True
        assert GameVariant.BN.has_stable is True
        assert GameVariant.TLG.has_stable is True

    def test_has_experimental(self):
        assert GameVariant.CDDA.has_experimental is True
        assert GameVariant.BN.has_experimental is True
        assert GameVariant.TLG.has_experimental is False

    def test_values(self):
        assert GameVariant.CDDA.value == "cdda"
        assert GameVariant.BN.value == "bn"
        assert GameVariant.TLG.value == "tlg"


class TestContentType:
    def test_display_names(self):
        assert ContentType.MODS.display_name == "Mods"
        assert ContentType.FONTS.display_name == "Fonts"
        assert ContentType.SOUNDPACKS.display_name == "Soundpacks"
        assert ContentType.TILESETS.display_name == "Tilesets"

    def test_userdata_dirs(self):
        assert ContentType.MODS.userdata_dir == "mods"
        assert ContentType.FONTS.userdata_dir == "font"
        assert ContentType.SOUNDPACKS.userdata_dir == "sound"
        assert ContentType.TILESETS.userdata_dir == "gfx"


class TestContentCatalog:
    def test_catalog_not_empty(self):
        assert len(CONTENT_CATALOG) > 0

    def test_all_items_have_name(self):
        for item in CONTENT_CATALOG:
            assert item.name, f"Item has empty name: {item}"

    def test_all_items_have_description(self):
        for item in CONTENT_CATALOG:
            assert item.description, f"Item {item.name!r} has empty description"

    def test_all_items_have_url(self):
        for item in CONTENT_CATALOG:
            assert item.url, f"Item {item.name!r} has empty URL"

    def test_all_items_have_content_type(self):
        for item in CONTENT_CATALOG:
            assert isinstance(item.content_type, ContentType)

    def test_all_items_have_nonempty_variants(self):
        for item in CONTENT_CATALOG:
            assert item.variants, f"Item {item.name!r} has empty variants list"

    def test_all_variants_are_game_variants(self):
        for item in CONTENT_CATALOG:
            for v in item.variants:
                assert isinstance(v, GameVariant)

    def test_catalog_covers_all_content_types(self):
        types_present = {item.content_type for item in CONTENT_CATALOG}
        assert ContentType.MODS in types_present
        assert ContentType.FONTS in types_present
        assert ContentType.SOUNDPACKS in types_present
        assert ContentType.TILESETS in types_present
