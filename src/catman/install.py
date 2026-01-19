import httpx
import zipfile
import tarfile
import shutil
import platform
from rich.progress import Progress
from catman.config import DIRS, GAMES


async def get_releases(game_key: str):
    """Fetch releases from GitHub."""
    repo = GAMES[game_key]["repo"]
    url = f"https://api.github.com/repos/{repo}/releases"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return resp.json()[:10]  # Return top 10 releases


def match_asset(assets):
    """Find the correct asset for the current OS."""
    os_name = platform.system().lower()
    # Mappings for loose keywords in filenames
    keywords = []
    if os_name == "windows":
        keywords = ["win", "x64", "msvc"]
    elif os_name == "darwin":  # macOS
        keywords = ["osx", "macos", "dmg"]
    elif os_name == "linux":
        keywords = ["linux", "x64"]

    for asset in assets:
        name = asset["name"].lower()
        if any(k in name for k in keywords) and not "curses" in name:  # Prefer tiles
            return asset["browser_download_url"]
    return None


async def download_file(url: str, dest_path: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        async with client.stream("GET", url) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            with open(dest_path, "wb") as f, Progress() as progress:
                task = progress.add_task("[cyan]Downloading...", total=total)
                async for chunk in resp.aiter_bytes():
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))


def extract_game(archive_path, game_key, version_tag):
    """Extracts game to games/game_key/version_tag"""
    install_dir = DIRS["games"] / game_key.lower() / version_tag
    if install_dir.exists():
        shutil.rmtree(install_dir)
    install_dir.mkdir(parents=True)

    # Extraction
    if str(archive_path).endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as z:
            z.extractall(install_dir)
    elif str(archive_path).endswith("tar.gz"):
        with tarfile.open(archive_path, "r:gz") as t:
            t.extractall(install_dir)

    # Flatten logic: If extracted to a subfolder (common in GitHub releases), move it up
    items = list(install_dir.iterdir())
    if len(items) == 1 and items[0].is_dir():
        temp_sub = items[0]
        for subitem in temp_sub.iterdir():
            shutil.move(str(subitem), str(install_dir))
        temp_sub.rmdir()

    return install_dir
