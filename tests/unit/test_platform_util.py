"""Tests for platform_util module."""

import pytest
from unittest.mock import patch

from catman.platform_util import get_arch, get_os, match_asset, find_matching_asset
from tests.unit.conftest import make_asset

# ---------------------------------------------------------------------------
# get_os / get_arch
# ---------------------------------------------------------------------------


class TestGetOs:
    def test_darwin_returns_macos(self):
        with patch("platform.system", return_value="Darwin"):
            assert get_os() == "macos"

    def test_linux_returns_linux(self):
        with patch("platform.system", return_value="Linux"):
            assert get_os() == "linux"

    def test_windows_returns_windows(self):
        with patch("platform.system", return_value="Windows"):
            assert get_os() == "windows"


class TestGetArch:
    def test_x86_64_returns_x64(self):
        with patch("platform.machine", return_value="x86_64"):
            assert get_arch() == "x64"

    def test_amd64_returns_x64(self):
        with patch("platform.machine", return_value="AMD64"):
            assert get_arch() == "x64"

    def test_arm64_returns_arm64(self):
        with patch("platform.machine", return_value="arm64"):
            assert get_arch() == "arm64"

    def test_aarch64_returns_arm64(self):
        with patch("platform.machine", return_value="aarch64"):
            assert get_arch() == "arm64"


# ---------------------------------------------------------------------------
# match_asset — OS matching
# ---------------------------------------------------------------------------


class TestMatchAssetOS:
    def test_macos_asset_matches_macos(self):
        assert match_asset("cdda-osx-tiles-universal.dmg", "macos", "x64") is True

    def test_macos_darwin_keyword(self):
        assert match_asset("game-darwin-tiles-x64.tar.gz", "macos", "x64") is True

    def test_macos_macos_keyword(self):
        assert match_asset("game-macos-tiles-x64.tar.gz", "macos", "x64") is True

    def test_linux_asset_matches_linux(self):
        assert match_asset("cdda-linux-tiles-x64.tar.gz", "linux", "x64") is True

    def test_windows_asset_matches_windows(self):
        assert match_asset("cdda-windows-tiles-x64.zip", "windows", "x64") is True

    def test_win64_keyword_matches_windows(self):
        assert match_asset("cdda-win64-tiles.zip", "windows", "x64") is True

    def test_linux_asset_rejected_for_macos(self):
        assert match_asset("cdda-linux-tiles-x64.tar.gz", "macos", "x64") is False

    def test_macos_asset_rejected_for_linux(self):
        assert match_asset("cdda-osx-tiles-universal.dmg", "linux", "x64") is False

    def test_unknown_os_returns_false(self):
        assert match_asset("cdda-osx-tiles-x64.dmg", "bsd", "x64") is False


# ---------------------------------------------------------------------------
# match_asset — Archive extension filtering
# ---------------------------------------------------------------------------


class TestMatchAssetExtension:
    def test_tar_gz_accepted(self):
        assert match_asset("cdda-linux-tiles-x64.tar.gz", "linux", "x64") is True

    def test_tar_xz_accepted(self):
        assert match_asset("cdda-linux-tiles-x64.tar.xz", "linux", "x64") is True

    def test_tar_bz2_accepted(self):
        assert match_asset("cdda-linux-tiles-x64.tar.bz2", "linux", "x64") is True

    def test_zip_accepted(self):
        assert match_asset("cdda-windows-tiles-x64.zip", "windows", "x64") is True

    def test_dmg_accepted(self):
        assert match_asset("cdda-osx-tiles-universal.dmg", "macos", "x64") is True

    def test_apk_rejected(self):
        assert match_asset("cdda-android-tiles.apk", "linux", "x64") is False

    def test_aab_rejected(self):
        assert match_asset("cdda-android-tiles.aab", "linux", "x64") is False

    def test_exe_rejected(self):
        assert match_asset("cdda-windows-tiles-x64.exe", "windows", "x64") is False


# ---------------------------------------------------------------------------
# match_asset — Android rejection
# ---------------------------------------------------------------------------


class TestMatchAssetAndroid:
    def test_android_in_name_rejected(self):
        assert match_asset("cdda-android-tiles.zip", "linux", "x64") is False

    def test_android_zip_rejected(self):
        assert match_asset("game-android-x64.zip", "linux", "x64") is False


# ---------------------------------------------------------------------------
# match_asset — Tiles vs curses/terminal-only
# ---------------------------------------------------------------------------


class TestMatchAssetBuildType:
    def test_tiles_true_rejects_curses(self):
        assert (
            match_asset("cdda-linux-curses-x64.tar.gz", "linux", "x64", tiles=True)
            is False
        )

    def test_tiles_true_rejects_terminal_only(self):
        assert (
            match_asset(
                "cdda-osx-terminal-only-universal.dmg", "macos", "x64", tiles=True
            )
            is False
        )

    def test_tiles_false_rejects_tiles(self):
        assert (
            match_asset("cdda-linux-tiles-x64.tar.gz", "linux", "x64", tiles=False)
            is False
        )

    def test_tiles_false_rejects_with_graphics(self):
        assert (
            match_asset(
                "cdda-osx-with-graphics-universal.dmg", "macos", "x64", tiles=False
            )
            is False
        )

    def test_tiles_true_accepts_tiles(self):
        assert (
            match_asset("cdda-linux-tiles-x64.tar.gz", "linux", "x64", tiles=True)
            is True
        )

    def test_tiles_false_accepts_curses(self):
        assert (
            match_asset("cdda-linux-curses-x64.tar.gz", "linux", "x64", tiles=False)
            is True
        )


# ---------------------------------------------------------------------------
# match_asset — Architecture
# ---------------------------------------------------------------------------


class TestMatchAssetArch:
    def test_universal_always_matches(self):
        assert match_asset("cdda-osx-tiles-universal.dmg", "macos", "arm64") is True
        assert match_asset("cdda-osx-tiles-universal.dmg", "macos", "x64") is True

    def test_arm64_asset_matches_arm64(self):
        assert match_asset("game-linux-tiles-arm64.tar.gz", "linux", "arm64") is True

    def test_arm64_asset_rejected_for_x64(self):
        assert match_asset("game-linux-tiles-arm64.tar.gz", "linux", "x64") is False

    def test_aarch64_asset_matches_arm64(self):
        assert match_asset("game-linux-tiles-aarch64.tar.gz", "linux", "arm64") is True

    def test_arm_dash_asset_matches_arm64(self):
        assert match_asset("game-linux-tiles-arm-v7.tar.gz", "linux", "arm64") is True

    def test_x64_asset_matches_x64(self):
        assert match_asset("cdda-linux-tiles-x64.tar.gz", "linux", "x64") is True

    def test_x64_asset_rejected_for_arm64(self):
        # x64-only asset should not match arm64 (no arm64 keyword in name)
        # This asset doesn't contain arm64 keywords, so it "passes" arch check for arm64
        # (the code returns True for x64 if no arm keywords present)
        # Actually arm64 falls through to the arm check: looks for arm64/aarch64/-arm-/-arm.
        # An x64 asset has none of these, so arm64 returns False only if no arm keywords found
        # Wait, let me re-read the logic:
        # if arch == "arm64": return any(x in n for x in ("arm64", "aarch64", "-arm-", "-arm."))
        # So for arm64, an x64 asset returns False since none of those are in the name.
        assert match_asset("cdda-linux-tiles-x64.tar.gz", "linux", "arm64") is False


# ---------------------------------------------------------------------------
# find_matching_asset
# ---------------------------------------------------------------------------


class TestFindMatchingAsset:
    def test_returns_none_when_no_match(self):
        assets = [make_asset("cdda-linux-tiles-x64.tar.gz")]
        assert find_matching_asset(assets, "macos", "x64") is None

    def test_prefers_sound_build(self):
        assets = [
            make_asset("cdda-linux-tiles-x64.tar.gz"),
            make_asset("cdda-linux-tiles-sound-x64.tar.gz"),
        ]
        result = find_matching_asset(assets, "linux", "x64")
        assert result is not None
        assert "sound" in result.name

    def test_prefers_tar_gz_over_zip(self):
        assets = [
            make_asset("cdda-linux-tiles-x64.zip"),
            make_asset("cdda-linux-tiles-x64.tar.gz"),
        ]
        result = find_matching_asset(assets, "linux", "x64")
        assert result is not None
        assert result.name.endswith(".tar.gz")

    def test_prefers_tar_gz_over_dmg(self):
        assets = [
            make_asset("game-macos-tiles-x64.dmg"),
            make_asset("game-macos-tiles-x64.tar.gz"),
        ]
        result = find_matching_asset(assets, "macos", "x64")
        assert result is not None
        assert result.name.endswith(".tar.gz")

    def test_prefers_zip_over_dmg(self):
        assets = [
            make_asset("game-macos-tiles-x64.dmg"),
            make_asset("game-macos-tiles-x64.zip"),
        ]
        result = find_matching_asset(assets, "macos", "x64")
        assert result is not None
        assert result.name.endswith(".zip")

    def test_macos_arm64_fallback_to_x64(self):
        assets = [make_asset("cdda-osx-tiles-x64.dmg")]
        result = find_matching_asset(assets, "macos", "arm64")
        assert result is not None
        assert result.name == "cdda-osx-tiles-x64.dmg"

    def test_macos_arm64_prefers_native_over_fallback(self):
        assets = [
            make_asset("cdda-osx-tiles-x64.dmg"),
            make_asset("cdda-osx-tiles-arm64.dmg"),
        ]
        result = find_matching_asset(assets, "macos", "arm64")
        assert result is not None
        assert "arm64" in result.name

    def test_returns_first_match_when_no_preference(self):
        assets = [make_asset("cdda-linux-tiles-x64.zip")]
        result = find_matching_asset(assets, "linux", "x64")
        assert result is not None
        assert result.name == "cdda-linux-tiles-x64.zip"
