import os
import platform
from pathlib import Path

APP_NAME = "catman"
BASE_DIR = Path.home() / f".{APP_NAME}"

# Directory Structure
DIRS = {
    "games": BASE_DIR / "games",  # Where game binaries live
    "userdata": BASE_DIR / "userdata",  # Saves, Configs, Mods (The persistent layer)
    "cache": BASE_DIR / "cache",  # Download cache
}

# GitHub Repositories
GAMES = {
    "CDDA": {
        "name": "Cataclysm: Dark Days Ahead",
        "repo": "CleverRaven/Cataclysm-DDA",
        "userdir_arg": "--userdir",
        "exe_names": ["cataclysm-tiles", "cataclysm", "cataclysm-tiles.exe"],
    },
    "CBN": {
        "name": "Cataclysm: Bright Nights",
        "repo": "cataclysmbnteam/Cataclysm-BN",
        "userdir_arg": "--userdir",
        "exe_names": ["cataclysm-tiles", "cataclysm", "cataclysm-tiles.exe"],
    },
    "TLG": {
        "name": "Cataclysm: The Last Generation",
        "repo": "Cataclysm-TLG/Cataclysm-TLG",
        "userdir_arg": "--userdir",
        "exe_names": ["cataclysm-tiles", "cataclysm", "cataclysm-tiles.exe"],
    },
}

# Popular Assets (Simplified List)
POPULAR_DOWNLOADS = {
    "soundpacks": [
        {
            "name": "Otopack",
            "url": "https://github.com/Kenan2000/Otopack/archive/refs/heads/master.zip",
        },
        {
            "name": "@'s Soundpack",
            "url": "https://github.com/dammarHF/The-Soundpack/archive/refs/heads/master.zip",
        },
    ],
    "mods": [
        {
            "name": "Kenan's Modpack (CDDA)",
            "url": "https://github.com/Kenan2000/Otopack-Mods-Updates/archive/refs/heads/master.zip",
        }
    ],
    "fonts": [
        {
            "name": "Unifont",
            "url": "https://unifoundry.com/pub/unifont/unifont-15.0.01/font-builds/unifont-15.0.01.ttf",
        }
    ],
}


def get_platform_exe():
    system = platform.system()
    if system == "Windows":
        return ".exe"
    return ""


def init_dirs():
    for d in DIRS.values():
        d.mkdir(parents=True, exist_ok=True)
    for game in GAMES:
        (DIRS["userdata"] / game.lower()).mkdir(exist_ok=True)
