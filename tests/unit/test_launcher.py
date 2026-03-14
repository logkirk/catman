"""Tests for launcher module."""

import time
import pytest
from pathlib import Path

from catman.launcher import find_most_recent_world, find_worlds


def _make_world(save_dir: Path, name: str) -> Path:
    world = save_dir / name
    world.mkdir(parents=True)
    return world


class TestFindWorlds:
    def test_empty_save_dir_returns_empty(self, tmp_path):
        userdata = tmp_path / "userdata"
        (userdata / "save").mkdir(parents=True)
        assert find_worlds(userdata) == []

    def test_missing_save_dir_returns_empty(self, tmp_path):
        userdata = tmp_path / "userdata"
        userdata.mkdir()
        assert find_worlds(userdata) == []

    def test_returns_world_names(self, tmp_path):
        userdata = tmp_path / "userdata"
        save_dir = userdata / "save"
        _make_world(save_dir, "World1")
        _make_world(save_dir, "World2")
        worlds = find_worlds(userdata)
        assert set(worlds) == {"World1", "World2"}

    def test_returns_sorted_names(self, tmp_path):
        userdata = tmp_path / "userdata"
        save_dir = userdata / "save"
        _make_world(save_dir, "Beta")
        _make_world(save_dir, "Alpha")
        _make_world(save_dir, "Gamma")
        assert find_worlds(userdata) == ["Alpha", "Beta", "Gamma"]

    def test_ignores_files_not_dirs(self, tmp_path):
        userdata = tmp_path / "userdata"
        save_dir = userdata / "save"
        save_dir.mkdir(parents=True)
        (save_dir / "not_a_world.txt").write_text("file")
        _make_world(save_dir, "RealWorld")
        assert find_worlds(userdata) == ["RealWorld"]


class TestFindMostRecentWorld:
    def test_empty_save_dir_returns_none(self, tmp_path):
        userdata = tmp_path / "userdata"
        (userdata / "save").mkdir(parents=True)
        assert find_most_recent_world(userdata) is None

    def test_missing_save_dir_returns_none(self, tmp_path):
        userdata = tmp_path / "userdata"
        userdata.mkdir()
        assert find_most_recent_world(userdata) is None

    def test_returns_most_recent(self, tmp_path):
        userdata = tmp_path / "userdata"
        save_dir = userdata / "save"
        _make_world(save_dir, "OldWorld")
        time.sleep(0.02)
        _make_world(save_dir, "NewWorld")
        assert find_most_recent_world(userdata) == "NewWorld"

    def test_single_world_returned(self, tmp_path):
        userdata = tmp_path / "userdata"
        save_dir = userdata / "save"
        _make_world(save_dir, "OnlyWorld")
        assert find_most_recent_world(userdata) == "OnlyWorld"
