import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Backup:
    name: str
    path: Path
    created_at: datetime
    size: int


def list_backups(backups_dir: Path) -> list[Backup]:
    """List all backups, newest first."""
    if not backups_dir.exists():
        return []
    backups = []
    for f in backups_dir.iterdir():
        if f.suffix == ".zip":
            stat = f.stat()
            backups.append(
                Backup(
                    name=f.stem,
                    path=f,
                    created_at=datetime.fromtimestamp(stat.st_mtime),
                    size=stat.st_size,
                )
            )
    backups.sort(key=lambda b: b.created_at, reverse=True)
    return backups


def create_backup(
    save_dir: Path, backups_dir: Path, name: str | None = None
) -> Backup:
    """Create a zip backup of the save directory."""
    if not save_dir.exists() or not any(save_dir.iterdir()):
        raise FileNotFoundError(f"No saves found in {save_dir}")

    backups_dir.mkdir(parents=True, exist_ok=True)
    if name is None:
        name = datetime.now().strftime("backup_%Y%m%d_%H%M%S")

    backup_path = backups_dir / f"{name}.zip"
    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in save_dir.rglob("*"):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(save_dir))

    stat = backup_path.stat()
    return Backup(
        name=name,
        path=backup_path,
        created_at=datetime.fromtimestamp(stat.st_mtime),
        size=stat.st_size,
    )


def restore_backup(backup: Backup, save_dir: Path) -> None:
    """Restore a backup, replacing the current save directory contents."""
    if save_dir.exists():
        shutil.rmtree(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(backup.path, "r") as zf:
        zf.extractall(save_dir)


def rename_backup(backup: Backup, new_name: str) -> Backup:
    """Rename a backup file."""
    new_path = backup.path.parent / f"{new_name}.zip"
    backup.path.rename(new_path)
    return Backup(
        name=new_name,
        path=new_path,
        created_at=backup.created_at,
        size=backup.size,
    )


def delete_backup(backup: Backup) -> None:
    """Delete a backup file."""
    backup.path.unlink()
