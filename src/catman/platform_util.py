import platform
import subprocess


def get_os() -> str:
    """Returns 'macos', 'linux', or 'windows'."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    return system


def get_arch() -> str:
    """Returns 'x64' or 'arm64'."""
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        return "x64"
    if machine in ("arm64", "aarch64"):
        return "arm64"
    return machine


def match_asset(name: str, os_name: str, arch: str, tiles: bool = True) -> bool:
    """Check if a release asset name matches the given platform.

    Handles naming from all three variants:
      CDDA: "with-graphics"/"terminal-only", "osx", "universal"
      BN:   "tiles"/"curses", "osx", "arm"/"x64"
      TLG:  "tiles"/"curses", "osx", "universal"
    """
    n = name.lower()

    # Must be a downloadable archive (skip .apk, .aab, etc.)
    if not any(
        n.endswith(ext) for ext in (".tar.gz", ".tar.xz", ".tar.bz2", ".zip", ".dmg")
    ):
        return False

    # Skip android
    if "android" in n:
        return False

    # OS matching
    if os_name == "macos":
        if not any(x in n for x in ("macos", "osx", "darwin")):
            return False
    elif os_name == "linux":
        if "linux" not in n:
            return False
    elif os_name == "windows":
        if not any(x in n for x in ("windows", "win64", "win32")):
            return False
    else:
        return False

    # Build type matching
    # CDDA uses "terminal-only" / "with-graphics"; BN/TLG use "curses" / "tiles"
    if tiles:
        if "curses" in n or "terminal-only" in n:
            return False
    else:
        if "tiles" in n or "with-graphics" in n:
            return False

    # Architecture matching
    if "universal" in n:
        return True

    if arch == "arm64":
        return any(x in n for x in ("arm64", "aarch64", "-arm-", "-arm."))
    else:  # x64
        if any(x in n for x in ("arm64", "aarch64", "-arm-", "-arm.")):
            return False
        return True


def find_matching_asset(assets, os_name: str, arch: str, tiles: bool = True):
    """Find the best matching asset for the given platform.

    Assets are expected to have a .name attribute.
    """
    matches = [a for a in assets if match_asset(a.name, os_name, arch, tiles)]

    # macOS arm64 fallback: try x64 (Rosetta 2) or universal
    if not matches and os_name == "macos" and arch == "arm64":
        matches = [a for a in assets if match_asset(a.name, os_name, "x64", tiles)]

    if not matches:
        return None

    # Prefer builds that include sounds
    for m in matches:
        if "sound" in m.name.lower():
            return m

    # Prefer .tar.gz over .dmg for easier extraction
    for m in matches:
        if m.name.endswith((".tar.gz", ".tar.xz", ".tar.bz2")):
            return m
    for m in matches:
        if m.name.endswith(".zip"):
            return m
    return matches[0]


def open_file_browser(path: str) -> None:
    """Open the system file browser at the given path."""
    os_name = get_os()
    if os_name == "macos":
        subprocess.Popen(["open", path])
    elif os_name == "linux":
        subprocess.Popen(["xdg-open", path])
    elif os_name == "windows":
        subprocess.Popen(["explorer", path])
