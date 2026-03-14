"""Tests for github module."""

import pytest

from catman.constants import GameVariant, ReleaseChannel
from catman.github import GitHubClient


class TestDetermineChannel:
    def test_tlg_always_stable(self, stable_release_dict, experimental_release_dict):
        assert (
            GitHubClient._determine_channel(GameVariant.TLG, stable_release_dict)
            == ReleaseChannel.STABLE
        )
        assert (
            GitHubClient._determine_channel(GameVariant.TLG, experimental_release_dict)
            == ReleaseChannel.STABLE
        )

    def test_cdda_prerelease_is_experimental(self, experimental_release_dict):
        assert (
            GitHubClient._determine_channel(GameVariant.CDDA, experimental_release_dict)
            == ReleaseChannel.EXPERIMENTAL
        )

    def test_cdda_non_prerelease_is_stable(self, stable_release_dict):
        assert (
            GitHubClient._determine_channel(GameVariant.CDDA, stable_release_dict)
            == ReleaseChannel.STABLE
        )

    def test_bn_prerelease_is_experimental(self, experimental_release_dict):
        assert (
            GitHubClient._determine_channel(GameVariant.BN, experimental_release_dict)
            == ReleaseChannel.EXPERIMENTAL
        )

    def test_bn_non_prerelease_is_stable(self, stable_release_dict):
        assert (
            GitHubClient._determine_channel(GameVariant.BN, stable_release_dict)
            == ReleaseChannel.STABLE
        )

    def test_missing_prerelease_key_treated_as_stable(self):
        release = {"tag_name": "v1.0", "name": "v1.0"}  # no "prerelease" key
        assert (
            GitHubClient._determine_channel(GameVariant.CDDA, release)
            == ReleaseChannel.STABLE
        )
