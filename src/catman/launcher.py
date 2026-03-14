import os
import shlex
import shutil
import stat
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


def _find_binary_in_app(app_path: Path, tiles: bool = True) -> Path | None:
    """Find the actual game binary inside a macOS .app bundle."""
    resources = app_path / "Contents" / "Resources"
    if not resources.is_dir():
        return None
    names = TILES_EXE_NAMES if tiles else CURSES_EXE_NAMES
    for name in names:
        binary = resources / name
        if binary.is_file() and os.access(binary, os.X_OK):
            return binary
    # Fallback: any cataclysm executable in Resources
    for p in resources.iterdir():
        if (
            p.is_file()
            and os.access(p, os.X_OK)
            and "cataclysm" in p.name.lower()
            and not p.name.startswith(".")
            and p.suffix not in (".txt", ".json", ".md", ".py", ".sh")
        ):
            return p
    return None


def find_executable(build_path: Path, tiles: bool = True) -> Path | None:
    """Find the game executable in a build directory."""
    # On macOS, look inside .app bundles for the actual binary
    if get_os() == "macos":
        for app in build_path.rglob("*.app"):
            if "cataclysm" in app.name.lower():
                binary = _find_binary_in_app(app, tiles)
                if binary:
                    return binary

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
            and p.suffix not in (".txt", ".json", ".md", ".py", ".sh")
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


def _launch_curses_new_window(
    cmd: list[str], cwd: str, env: dict, os_name: str
) -> None:
    """Launch a curses binary in a new terminal window."""
    if os_name == "macos":
        # Write a temp shell script so we avoid AppleScript string-escaping issues.
        # Temp paths are free of spaces/special chars, safe to embed in AppleScript.
        lines = ["#!/bin/sh"]
        for key in ("DYLD_LIBRARY_PATH", "DYLD_FRAMEWORK_PATH"):
            if key in env:
                lines.append(f"export {key}={shlex.quote(env[key])}")
        lines.append(f"cd {shlex.quote(cwd)}")
        lines.append(" ".join(shlex.quote(c) for c in cmd))
        tmp = f"/tmp/catman_launch_{os.getpid()}.sh"
        with open(tmp, "w") as f:
            f.write("\n".join(lines) + "\n")
        os.chmod(tmp, stat.S_IRWXU)
        script = f'tell application "Terminal" to do script "{tmp}"'
        subprocess.Popen(["osascript", "-e", script], stdout=subprocess.DEVNULL)
    elif os_name == "linux":
        terminals = [
            ["x-terminal-emulator", "-e"],
            ["gnome-terminal", "--"],
            ["xterm", "-e"],
            ["konsole", "-e"],
            ["xfce4-terminal", "-e"],
            ["lxterminal", "-e"],
            ["alacritty", "-e"],
            ["kitty"],
        ]
        for term_args in terminals:
            if shutil.which(term_args[0]):
                subprocess.Popen(term_args + cmd, cwd=cwd, env=env)
                return
        # Fallback: run in current terminal
        subprocess.Popen(cmd, cwd=cwd, env=env)
    elif os_name == "windows":
        subprocess.Popen(["cmd", "/c", "start", "cmd", "/k"] + cmd, cwd=cwd, env=env)
    else:
        subprocess.Popen(cmd, cwd=cwd, env=env)


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

    game_args = ["--userdir", str(userdata_path)]
    if world:
        game_args.extend(["--world", world])

    env = os.environ.copy()
    os_name = get_os()

    if os_name == "macos":
        # Set framework/library paths for SDL dependencies
        exe_dir = str(exe.parent)
        env["DYLD_LIBRARY_PATH"] = exe_dir
        env["DYLD_FRAMEWORK_PATH"] = exe_dir

    cmd = [str(exe)] + game_args

    # Detect actual build type from the binary name. The `tiles` param is only
    # a hint for find_executable — its fallback can return a curses binary even
    # when tiles=True, so re-check here before deciding how to launch.
    is_curses = "tiles" not in exe.name.lower()

    if is_curses:
        _launch_curses_new_window(cmd, str(exe.parent), env, os_name)
    else:
        subprocess.Popen(cmd, cwd=str(exe.parent), env=env)
