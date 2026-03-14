"""Tests for config module."""

import json
import pytest

from catman.config import AppPaths, Config
from catman.constants import GameVariant, ReleaseChannel
from tests.unit.conftest import TmpAppPaths


class TestConfigChannelDefaults:
    def test_cdda_defaults_to_stable(self):
        config = Config()
        assert config.get_channel(GameVariant.CDDA) == ReleaseChannel.STABLE

    def test_tlg_defaults_to_stable(self):
        config = Config()
        assert config.get_channel(GameVariant.TLG) == ReleaseChannel.STABLE

    def test_bn_defaults_to_stable(self):
        # BN has_stable=True, so default is STABLE
        config = Config()
        assert config.get_channel(GameVariant.BN) == ReleaseChannel.STABLE


class TestConfigSetChannel:
    def test_set_and_get_channel_roundtrip(self):
        config = Config()
        config.set_channel(GameVariant.CDDA, ReleaseChannel.EXPERIMENTAL)
        assert config.get_channel(GameVariant.CDDA) == ReleaseChannel.EXPERIMENTAL

    def test_set_channel_does_not_affect_other_variants(self):
        config = Config()
        config.set_channel(GameVariant.CDDA, ReleaseChannel.EXPERIMENTAL)
        assert config.get_channel(GameVariant.TLG) == ReleaseChannel.STABLE


class TestConfigBuildChannel:
    def test_register_and_get_build_channel(self):
        config = Config()
        config.register_build(GameVariant.CDDA, "0.G", ReleaseChannel.STABLE)
        assert (
            config.get_build_channel(GameVariant.CDDA, "0.G") == ReleaseChannel.STABLE
        )

    def test_register_experimental_build(self):
        config = Config()
        config.register_build(
            GameVariant.BN, "exp-20240101", ReleaseChannel.EXPERIMENTAL
        )
        assert (
            config.get_build_channel(GameVariant.BN, "exp-20240101")
            == ReleaseChannel.EXPERIMENTAL
        )

    def test_get_build_channel_returns_none_for_unknown(self):
        config = Config()
        assert config.get_build_channel(GameVariant.CDDA, "unknown") is None

    def test_register_multiple_builds(self):
        config = Config()
        config.register_build(GameVariant.CDDA, "0.G", ReleaseChannel.STABLE)
        config.register_build(GameVariant.CDDA, "0.H", ReleaseChannel.STABLE)
        config.register_build(GameVariant.BN, "exp-1", ReleaseChannel.EXPERIMENTAL)
        assert (
            config.get_build_channel(GameVariant.CDDA, "0.G") == ReleaseChannel.STABLE
        )
        assert (
            config.get_build_channel(GameVariant.CDDA, "0.H") == ReleaseChannel.STABLE
        )
        assert (
            config.get_build_channel(GameVariant.BN, "exp-1")
            == ReleaseChannel.EXPERIMENTAL
        )


class TestConfigSaveLoad:
    def test_save_and_load_roundtrip(self, app_paths):
        config = Config()
        config.active_variant = GameVariant.BN
        config.set_channel(GameVariant.CDDA, ReleaseChannel.EXPERIMENTAL)
        config.register_build(GameVariant.CDDA, "0.G", ReleaseChannel.STABLE)
        config.save(app_paths)

        loaded = Config.load(app_paths)
        assert loaded.active_variant == GameVariant.BN
        assert loaded.get_channel(GameVariant.CDDA) == ReleaseChannel.EXPERIMENTAL
        assert (
            loaded.get_build_channel(GameVariant.CDDA, "0.G") == ReleaseChannel.STABLE
        )

    def test_load_missing_file_returns_default(self, app_paths):
        config = Config.load(app_paths)
        assert config.active_variant == GameVariant.CDDA

    def test_load_missing_file_creates_file(self, app_paths):
        Config.load(app_paths)
        assert app_paths.config_file.exists()

    def test_load_corrupted_json_returns_default(self, app_paths):
        app_paths.base.mkdir(parents=True, exist_ok=True)
        app_paths.config_file.write_text("not valid json {{{")
        config = Config.load(app_paths)
        assert config.active_variant == GameVariant.CDDA


class TestAppPaths:
    def test_config_file_path(self, app_paths):
        assert app_paths.config_file == app_paths.base / "config.json"

    def test_downloads_dir_path(self, app_paths):
        assert app_paths.downloads_dir == app_paths.base / "downloads"

    def test_variant_dir_path(self, app_paths):
        assert (
            app_paths.variant_dir(GameVariant.CDDA)
            == app_paths.base / "variants" / "cdda"
        )

    def test_builds_dir_path(self, app_paths):
        assert (
            app_paths.builds_dir(GameVariant.CDDA)
            == app_paths.base / "variants" / "cdda" / "builds"
        )

    def test_userdata_dir_path(self, app_paths):
        path = app_paths.userdata_dir(GameVariant.CDDA, ReleaseChannel.STABLE)
        assert path == app_paths.base / "variants" / "cdda" / "userdata-stable"

    def test_backups_dir_path(self, app_paths):
        assert (
            app_paths.backups_dir(GameVariant.CDDA)
            == app_paths.base / "variants" / "cdda" / "backups"
        )

    def test_ensure_dirs_creates_directories(self, app_paths):
        app_paths.ensure_dirs(GameVariant.CDDA, ReleaseChannel.STABLE)
        ud = app_paths.userdata_dir(GameVariant.CDDA, ReleaseChannel.STABLE)
        assert app_paths.builds_dir(GameVariant.CDDA).is_dir()
        assert ud.is_dir()
        assert app_paths.backups_dir(GameVariant.CDDA).is_dir()
        assert (ud / "mods").is_dir()
        assert (ud / "font").is_dir()
        assert (ud / "gfx").is_dir()
        assert (ud / "sound").is_dir()
        assert (ud / "save").is_dir()
        assert (ud / "config").is_dir()
        assert app_paths.downloads_dir.is_dir()

    def test_migrate_legacy_userdata(self, app_paths):
        legacy = app_paths.legacy_userdata_dir(GameVariant.CDDA)
        legacy.mkdir(parents=True)
        (legacy / "save").mkdir()

        result = app_paths.migrate_legacy_userdata(
            GameVariant.CDDA, ReleaseChannel.STABLE
        )
        assert result is True
        assert not legacy.exists()
        assert app_paths.userdata_dir(GameVariant.CDDA, ReleaseChannel.STABLE).is_dir()

    def test_migrate_legacy_userdata_skips_if_no_legacy(self, app_paths):
        result = app_paths.migrate_legacy_userdata(
            GameVariant.CDDA, ReleaseChannel.STABLE
        )
        assert result is False

    def test_migrate_legacy_userdata_skips_if_target_exists(self, app_paths):
        legacy = app_paths.legacy_userdata_dir(GameVariant.CDDA)
        legacy.mkdir(parents=True)
        target = app_paths.userdata_dir(GameVariant.CDDA, ReleaseChannel.STABLE)
        target.mkdir(parents=True)

        result = app_paths.migrate_legacy_userdata(
            GameVariant.CDDA, ReleaseChannel.STABLE
        )
        assert result is False
        assert legacy.exists()
