"""Shared fixtures for unit tests."""

import pytest
from pathlib import Path

from catman.config import AppPaths
from catman.constants import GameVariant, ReleaseChannel
from catman.github import ReleaseAsset


class TmpAppPaths(AppPaths):
    """AppPaths with base overridden to a tmp directory."""

    def __init__(self, base: Path):
        self.base = base


@pytest.fixture
def app_paths(tmp_path):
    return TmpAppPaths(tmp_path)


@pytest.fixture
def stable_release_dict():
    return {
        "tag_name": "0.G",
        "name": "Cataclysm: DDA 0.G",
        "prerelease": False,
        "published_at": "2022-09-01T00:00:00Z",
        "assets": [
            {
                "name": "cdda-osx-tiles-x64.dmg",
                "browser_download_url": "https://example.com/cdda-osx-tiles-x64.dmg",
                "size": 100000,
            }
        ],
    }


@pytest.fixture
def experimental_release_dict():
    return {
        "tag_name": "cdda-experimental-2024-01-01-0000",
        "name": "Cataclysm: DDA experimental",
        "prerelease": True,
        "published_at": "2024-01-01T00:00:00Z",
        "assets": [
            {
                "name": "cdda-osx-tiles-x64.dmg",
                "browser_download_url": "https://example.com/cdda-osx-tiles-x64.dmg",
                "size": 100000,
            }
        ],
    }


def make_asset(name: str) -> ReleaseAsset:
    return ReleaseAsset(name=name, url=f"https://example.com/{name}", size=1000)
