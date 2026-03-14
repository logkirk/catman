"""Tests for backup module."""

import zipfile
import pytest
from pathlib import Path

from catman.backup import (
    Backup,
    create_backup,
    delete_backup,
    list_backups,
    rename_backup,
    restore_backup,
)


def _make_save_dir(base: Path) -> Path:
    """Create a save dir with some dummy files."""
    save_dir = base / "save"
    save_dir.mkdir()
    (save_dir / "world1").mkdir()
    (save_dir / "world1" / "map.sav").write_text("data")
    return save_dir


class TestListBackups:
    def test_empty_dir_returns_empty(self, tmp_path):
        backups_dir = tmp_path / "backups"
        backups_dir.mkdir()
        assert list_backups(backups_dir) == []

    def test_missing_dir_returns_empty(self, tmp_path):
        assert list_backups(tmp_path / "nonexistent") == []

    def test_lists_zip_files(self, tmp_path):
        backups_dir = tmp_path / "backups"
        backups_dir.mkdir()
        (backups_dir / "backup1.zip").write_bytes(b"PK")
        (backups_dir / "backup2.zip").write_bytes(b"PK")
        results = list_backups(backups_dir)
        assert len(results) == 2
        names = {b.name for b in results}
        assert names == {"backup1", "backup2"}

    def test_ignores_non_zip_files(self, tmp_path):
        backups_dir = tmp_path / "backups"
        backups_dir.mkdir()
        (backups_dir / "backup1.zip").write_bytes(b"PK")
        (backups_dir / "notes.txt").write_text("not a backup")
        results = list_backups(backups_dir)
        assert len(results) == 1

    def test_sorted_newest_first(self, tmp_path):
        backups_dir = tmp_path / "backups"
        backups_dir.mkdir()
        import time

        (backups_dir / "old.zip").write_bytes(b"PK")
        time.sleep(0.01)
        (backups_dir / "new.zip").write_bytes(b"PK")
        results = list_backups(backups_dir)
        assert results[0].name == "new"
        assert results[1].name == "old"


class TestCreateBackup:
    def test_creates_valid_zip(self, tmp_path):
        save_dir = _make_save_dir(tmp_path)
        backups_dir = tmp_path / "backups"
        backup = create_backup(save_dir, backups_dir, name="test_backup")
        assert backup.path.exists()
        assert backup.name == "test_backup"
        assert zipfile.is_zipfile(backup.path)

    def test_auto_generates_name_when_none(self, tmp_path):
        save_dir = _make_save_dir(tmp_path)
        backups_dir = tmp_path / "backups"
        backup = create_backup(save_dir, backups_dir)
        assert backup.name.startswith("backup_")

    def test_zip_contains_save_files(self, tmp_path):
        save_dir = _make_save_dir(tmp_path)
        backups_dir = tmp_path / "backups"
        backup = create_backup(save_dir, backups_dir, name="test")
        with zipfile.ZipFile(backup.path) as zf:
            names = zf.namelist()
        assert any("map.sav" in n for n in names)

    def test_raises_on_empty_save_dir(self, tmp_path):
        save_dir = tmp_path / "save"
        save_dir.mkdir()
        backups_dir = tmp_path / "backups"
        with pytest.raises(FileNotFoundError):
            create_backup(save_dir, backups_dir)

    def test_raises_when_save_dir_missing(self, tmp_path):
        backups_dir = tmp_path / "backups"
        with pytest.raises(FileNotFoundError):
            create_backup(tmp_path / "nonexistent", backups_dir)

    def test_creates_backups_dir_if_missing(self, tmp_path):
        save_dir = _make_save_dir(tmp_path)
        backups_dir = tmp_path / "backups"
        assert not backups_dir.exists()
        create_backup(save_dir, backups_dir, name="test")
        assert backups_dir.is_dir()


class TestRestoreBackup:
    def test_restores_files(self, tmp_path):
        save_dir = _make_save_dir(tmp_path)
        backups_dir = tmp_path / "backups"
        backup = create_backup(save_dir, backups_dir, name="test")

        restore_dir = tmp_path / "restore"
        restore_backup(backup, restore_dir)
        assert (restore_dir / "world1" / "map.sav").exists()

    def test_replaces_existing_save_dir(self, tmp_path):
        save_dir = _make_save_dir(tmp_path)
        backups_dir = tmp_path / "backups"
        backup = create_backup(save_dir, backups_dir, name="test")

        restore_dir = tmp_path / "restore"
        restore_dir.mkdir()
        (restore_dir / "old_file.txt").write_text("stale")

        restore_backup(backup, restore_dir)
        assert not (restore_dir / "old_file.txt").exists()
        assert (restore_dir / "world1" / "map.sav").exists()


class TestRenameBackup:
    def test_renames_file_on_disk(self, tmp_path):
        save_dir = _make_save_dir(tmp_path)
        backups_dir = tmp_path / "backups"
        backup = create_backup(save_dir, backups_dir, name="original")

        renamed = rename_backup(backup, "renamed")
        assert renamed.name == "renamed"
        assert renamed.path.exists()
        assert renamed.path.name == "renamed.zip"
        assert not backup.path.exists()

    def test_returns_updated_backup(self, tmp_path):
        save_dir = _make_save_dir(tmp_path)
        backups_dir = tmp_path / "backups"
        backup = create_backup(save_dir, backups_dir, name="original")
        renamed = rename_backup(backup, "new_name")
        assert renamed.name == "new_name"
        assert renamed.path == backups_dir / "new_name.zip"


class TestDeleteBackup:
    def test_deletes_file(self, tmp_path):
        save_dir = _make_save_dir(tmp_path)
        backups_dir = tmp_path / "backups"
        backup = create_backup(save_dir, backups_dir, name="to_delete")
        assert backup.path.exists()

        delete_backup(backup)
        assert not backup.path.exists()
