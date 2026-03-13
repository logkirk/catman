import os
import subprocess
from pathlib import Path

from .platform_util import get_os

TILES_EXE_NAMES = [
    "cataclysm-tiles",
    "cataclysm-bn-tiles",
]

CURSES_EXE_NAMES = [
    "cataclysm",
    "cataclysm-bn",
]


def find_executable(build_path: Path, tiles: bool = True) -> Path | None:
    """Find the game executable in a build directory."""
    # On macOS, look for .app bundles first
    if get_os() == "macos":
        for app in build_path.rglob("*.app"):
            if "cataclysm" in app.name.lower():
                return app

    names = TILES_EXE_NAMES if tiles else CURSES_EXE_NAMES

    # Search by known names (recursive)
    for name in names:
        for p in build_path.rglob(name):
            if p.is_file() and os.access(p, os.X_OK):
                return p

    # Fallback: any executable containing "cataclysm"
    for p in build_path.rglob("*"):
        if (
            p.is_file()
            and os.access(p, os.X_OK)
            and "cataclysm" in p.name.lower()
            and not p.name.startswith(".")
            and not p.suffix in (".txt", ".json", ".md", ".py", ".sh")
        ):
            return p

    return None


def find_worlds(userdata_path: Path) -> list[str]:
    """List all save worlds in the userdata directory."""
    save_dir = userdata_path / "save"
    if not save_dir.exists():
        return []
    return sorted(d.name for d in save_dir.iterdir() if d.is_dir())


def find_most_recent_world(userdata_path: Path) -> str | None:
    """Find the most recently modified save world."""
    save_dir = userdata_path / "save"
    if not save_dir.exists():
        return None
    worlds = [(d, d.stat().st_mtime) for d in save_dir.iterdir() if d.is_dir()]
    if not worlds:
        return None
    worlds.sort(key=lambda x: x[1], reverse=True)
    return worlds[0][0].name


def launch_game(
    build_path: Path,
    userdata_path: Path,
    world: str | None = None,
    tiles: bool = True,
) -> None:
    """Launch the game with --userdir."""
    exe = find_executable(build_path, tiles)
    if exe is None:
        raise FileNotFoundError(f"No game executable found in {build_path}")

    userdata_path.mkdir(parents=True, exist_ok=True)
    args: list[str] = []

    if get_os() == "macos" and exe.suffix == ".app":
        args = ["open", "-a", str(exe), "--args"]
    else:
        args = [str(exe)]

    args.extend(["--userdir", str(userdata_path)])
    if world:
        args.extend(["--world", world])

    subprocess.Popen(args, cwd=str(build_path))
