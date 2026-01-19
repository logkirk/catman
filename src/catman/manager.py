import subprocess
import shutil
import datetime
from pathlib import Path
from catman.config import DIRS, GAMES, get_platform_exe


def find_executable(install_dir: Path):
    """Recursively search for the game executable."""
    # Special handling for macOS .app bundles
    if (install_dir / "Cataclysm.app").exists():
        return install_dir / "Cataclysm.app" / "Contents" / "MacOS" / "Cataclysm"

    for exe_name in [
        "cataclysm-tiles",
        "cataclysm",
        "cataclysm-tiles.exe",
        "cataclysm.exe",
    ]:
        found = list(install_dir.rglob(exe_name))
        if found:
            return found[0]
    return None


def launch_game(game_key: str, version_tag: str):
    """Launches the game with the isolated --userdir."""
    install_dir = DIRS["games"] / game_key.lower() / version_tag
    user_dir = DIRS["userdata"] / game_key.lower()

    if not install_dir.exists():
        print(f"Version {version_tag} not installed.")
        return

    exe_path = find_executable(install_dir)
    if not exe_path:
        print("Executable not found!")
        return

    cmd = [str(exe_path), "--userdir", str(user_dir)]

    print(f"Launching {game_key}...")
    print(f"Game Root: {install_dir}")
    print(f"User Data: {user_dir}")

    subprocess.run(cmd)


def backup_save(game_key: str):
    """Zips the save folder from userdata."""
    user_dir = DIRS["userdata"] / game_key.lower()
    save_dir = user_dir / "save"
    if not save_dir.exists():
        return "No saves found."

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = user_dir / f"backup_{timestamp}.zip"

    shutil.make_archive(str(backup_file).replace(".zip", ""), "zip", save_dir)
    return f"Backup created: {backup_file.name}"


def install_asset(file_path: Path, asset_type: str, game_key: str):
    """Installs mods/soundpacks/fonts."""
    # Note: CDDA mods usually go to userdir/mods
    # Soundpacks often need to be in the game dir or userdir/gfx or userdir/sound (version dependent)
    # For safety, we install Mods to userdir. Soundpacks we try to put in userdir/data/sound if it exists,
    # otherwise we might need to link them.

    user_dir = DIRS["userdata"] / game_key.lower()

    target_dir = user_dir
    if asset_type == "mods":
        target_dir = user_dir / "mods"
    elif asset_type == "soundpacks":
        target_dir = user_dir / "sound"  # specific to newer builds usually
    elif asset_type == "fonts":
        target_dir = user_dir / "font"

    target_dir.mkdir(parents=True, exist_ok=True)

    if file_path.suffix == ".zip":
        with zipfile.ZipFile(file_path, "r") as z:
            z.extractall(target_dir)
    elif file_path.suffix == ".ttf":
        shutil.copy(file_path, target_dir / file_path.name)
