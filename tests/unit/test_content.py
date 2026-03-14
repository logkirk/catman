"""Tests for content module pure functions."""

import pytest
from pathlib import Path

from catman.constants import ContentType, GameVariant
from catman.content import get_catalog, get_content_dir


class TestGetCatalog:
    def test_filters_by_content_type(self):
        mods = get_catalog(ContentType.MODS, GameVariant.CDDA)
        assert all(item.content_type == ContentType.MODS for item in mods)

    def test_filters_by_variant(self):
        soundpacks = get_catalog(ContentType.SOUNDPACKS, GameVariant.BN)
        assert all(GameVariant.BN in item.variants for item in soundpacks)

    def test_returns_empty_for_no_match(self):
        # TLG has no mods in catalog
        results = get_catalog(ContentType.MODS, GameVariant.TLG)
        assert results == []

    def test_cdda_has_mods(self):
        assert len(get_catalog(ContentType.MODS, GameVariant.CDDA)) > 0

    def test_cdda_has_soundpacks(self):
        assert len(get_catalog(ContentType.SOUNDPACKS, GameVariant.CDDA)) > 0

    def test_cdda_has_tilesets(self):
        assert len(get_catalog(ContentType.TILESETS, GameVariant.CDDA)) > 0

    def test_cdda_has_fonts(self):
        assert len(get_catalog(ContentType.FONTS, GameVariant.CDDA)) > 0

    def test_bn_has_soundpacks(self):
        assert len(get_catalog(ContentType.SOUNDPACKS, GameVariant.BN)) > 0

    def test_tlg_has_soundpacks(self):
        assert len(get_catalog(ContentType.SOUNDPACKS, GameVariant.TLG)) > 0


class TestGetContentDir:
    def test_mods_dir(self, tmp_path):
        assert get_content_dir(tmp_path, ContentType.MODS) == tmp_path / "mods"

    def test_fonts_dir(self, tmp_path):
        assert get_content_dir(tmp_path, ContentType.FONTS) == tmp_path / "font"

    def test_soundpacks_dir(self, tmp_path):
        assert get_content_dir(tmp_path, ContentType.SOUNDPACKS) == tmp_path / "sound"

    def test_tilesets_dir(self, tmp_path):
        assert get_content_dir(tmp_path, ContentType.TILESETS) == tmp_path / "gfx"
