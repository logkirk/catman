import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path

import httpx
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TransferSpeedColumn,
)


def download_file(url: str, dest: Path) -> Path:
    """Download a file with a rich progress bar."""
    with httpx.stream("GET", url, follow_redirects=True, timeout=120) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        with Progress(
            "[progress.description]{task.description}",
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
        ) as progress:
            task = progress.add_task("Downloading", total=total or None)
            with open(dest, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=8192):
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))
    return dest


def extract_archive(archive: Path, dest: Path) -> Path:
    """Extract an archive to dest. Returns path to the extracted content root."""
    dest.mkdir(parents=True, exist_ok=True)
    name = archive.name.lower()

    if name.endswith((".tar.gz", ".tgz")):
        _extract_tar(archive, dest, "r:gz")
    elif name.endswith(".tar.xz"):
        _extract_tar(archive, dest, "r:xz")
    elif name.endswith(".tar.bz2"):
        _extract_tar(archive, dest, "r:bz2")
    elif name.endswith(".zip"):
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(dest)
    elif name.endswith(".dmg"):
        return _extract_dmg(archive, dest)
    else:
        raise ValueError(f"Unsupported archive format: {archive.name}")

    # If extraction created a single top-level directory, return that
    entries = [e for e in dest.iterdir() if not e.name.startswith(".")]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return dest


def _extract_tar(archive: Path, dest: Path, mode: str) -> None:
    with tarfile.open(archive, mode) as tar:
        try:
            tar.extractall(dest, filter="data")
        except TypeError:
            # Python < 3.11.4 doesn't support filter=
            tar.extractall(dest)


def _extract_dmg(dmg: Path, dest: Path) -> Path:
    """Extract a DMG file (macOS only)."""
    mount_point = Path(tempfile.mkdtemp(prefix="catman_dmg_"))
    try:
        result = subprocess.run(
            ["hdiutil", "attach", "-nobrowse", "-noverify", "-mountpoint", str(mount_point), str(dmg)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to mount DMG: {result.stderr}")

        for item in mount_point.iterdir():
            if item.name.startswith("."):
                continue
            target = dest / item.name
            if item.is_dir():
                subprocess.run(["cp", "-R", str(item), str(target)], check=True)
            else:
                subprocess.run(["cp", str(item), str(target)], check=True)
    finally:
        subprocess.run(
            ["hdiutil", "detach", str(mount_point), "-quiet"],
            capture_output=True,
        )
        mount_point.rmdir()

    entries = [e for e in dest.iterdir() if not e.name.startswith(".")]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return dest
