import shutil
import tempfile
from pathlib import Path

from .constants import ContentItem, ContentType, GameVariant, CONTENT_CATALOG
from .downloader import download_file, extract_archive
from .github import GitHubClient


def get_catalog(content_type: ContentType, variant: GameVariant) -> list[ContentItem]:
    """Get catalog items for a content type and variant."""
    return [
        item
        for item in CONTENT_CATALOG
        if item.content_type == content_type and variant in item.variants
    ]


def get_content_dir(userdata_path: Path, content_type: ContentType) -> Path:
    """Get the directory for a content type within userdata."""
    return userdata_path / content_type.userdata_dir


def list_installed(userdata_path: Path, content_type: ContentType) -> list[str]:
    """List installed content of a given type."""
    content_dir = get_content_dir(userdata_path, content_type)
    if not content_dir.exists():
        return []

    if content_type == ContentType.FONTS:
        return sorted(
            f.name
            for f in content_dir.iterdir()
            if f.suffix.lower() in (".ttf", ".otf", ".woff", ".woff2")
        )

    return sorted(d.name for d in content_dir.iterdir() if d.is_dir())


def install_from_catalog(item: ContentItem, userdata_path: Path) -> str:
    """Install a content item from the catalog. Returns description of what was installed."""
    content_dir = get_content_dir(userdata_path, item.content_type)
    content_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)

        if item.is_github_repo:
            archive = _download_from_github(item.url, tmpdir)
        else:
            filename = item.url.split("/")[-1]
            archive = tmpdir / filename
            download_file(item.url, archive)

        # Single font file — just copy
        if archive.suffix.lower() in (".ttf", ".otf"):
            dest = content_dir / archive.name
            shutil.copy2(archive, dest)
            return archive.name

        # Extract archive
        extracted_dir = tmpdir / "extracted"
        extract_archive(archive, extracted_dir)

        return _install_extracted(
            extracted_dir, content_dir, item.content_type, item.name
        )


def _download_from_github(repo_url: str, tmpdir: Path) -> Path:
    """Download latest release asset or repo zip from a GitHub repo URL."""
    owner_repo = repo_url.replace("https://github.com/", "")
    client = GitHubClient()

    try:
        releases = client.get_releases(owner_repo, page=1, per_page=1)
    except Exception:
        releases = []

    if releases and releases[0].get("assets"):
        asset = releases[0]["assets"][0]
        archive = tmpdir / asset["name"]
        download_file(asset["browser_download_url"], archive)
    elif releases:
        tag = releases[0]["tag_name"]
        archive = tmpdir / "source.zip"
        download_file(f"{repo_url}/archive/refs/tags/{tag}.zip", archive)
    else:
        archive = tmpdir / "source.zip"
        download_file(f"{repo_url}/archive/refs/heads/main.zip", archive)

    client.close()
    return archive


def _install_extracted(
    extracted: Path, content_dir: Path, content_type: ContentType, fallback_name: str
) -> str:
    """Move extracted content into the appropriate content directory."""
    if content_type == ContentType.FONTS:
        count = 0
        for font_file in extracted.rglob("*"):
            if font_file.suffix.lower() in (".ttf", ".otf"):
                shutil.copy2(font_file, content_dir / font_file.name)
                count += 1
        return f"{count} font file(s)"

    # For mods, soundpacks, tilesets — look for marker files
    marker_files = {
        ContentType.MODS: "modinfo.json",
        ContentType.SOUNDPACKS: "soundpack.txt",
        ContentType.TILESETS: "tileset.txt",
    }
    marker = marker_files.get(content_type)

    if marker:
        found_dirs = set()
        for p in extracted.rglob(marker):
            found_dirs.add(p.parent)

        if found_dirs:
            names = []
            for d in found_dirs:
                dest = content_dir / d.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(d, dest)
                names.append(d.name)
            return ", ".join(sorted(names))

    # Fallback: copy the whole thing under the item name
    dest = content_dir / fallback_name
    if dest.exists():
        shutil.rmtree(dest)

    entries = [e for e in extracted.iterdir() if not e.name.startswith(".")]
    if len(entries) == 1 and entries[0].is_dir():
        shutil.copytree(entries[0], dest)
    else:
        shutil.copytree(extracted, dest)
    return fallback_name
