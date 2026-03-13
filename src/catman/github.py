import os
from dataclasses import dataclass

import httpx

from .constants import GameVariant, ReleaseChannel


@dataclass
class ReleaseAsset:
    name: str
    url: str
    size: int


@dataclass
class GameRelease:
    tag: str
    name: str
    channel: ReleaseChannel
    published_at: str
    assets: list[ReleaseAsset]


class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(self):
        headers = {"Accept": "application/vnd.github+json"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(headers=headers, timeout=30)

    def get_releases(self, repo: str, page: int = 1, per_page: int = 100) -> list[dict]:
        """Fetch a page of releases for a given owner/repo string."""
        url = f"{self.BASE_URL}/repos/{repo}/releases"
        resp = self._client.get(url, params={"page": page, "per_page": per_page})
        resp.raise_for_status()
        return resp.json()

    def get_all_game_releases(
        self, variant: GameVariant, max_pages: int = 5
    ) -> list[GameRelease]:
        """Fetch releases for a game variant. Skips releases with no assets."""
        releases: list[GameRelease] = []
        for page in range(1, max_pages + 1):
            data = self.get_releases(variant.github_repo, page=page, per_page=100)
            if not data:
                break
            for r in data:
                assets_raw = r.get("assets", [])
                if not assets_raw:
                    continue
                channel = self._determine_channel(variant, r)
                assets = [
                    ReleaseAsset(
                        name=a["name"],
                        url=a["browser_download_url"],
                        size=a["size"],
                    )
                    for a in assets_raw
                ]
                releases.append(
                    GameRelease(
                        tag=r["tag_name"],
                        name=r.get("name") or r["tag_name"],
                        channel=channel,
                        published_at=r.get("published_at", ""),
                        assets=assets,
                    )
                )
        return releases

    def get_stable_releases(self, variant: GameVariant) -> list[GameRelease]:
        """Fetch stable releases. For CDDA, uses the git refs API to find stable tags."""
        if variant == GameVariant.CDDA:
            return self._get_cdda_stable_releases()
        elif variant == GameVariant.TLG:
            return self.get_all_game_releases(variant, max_pages=5)
        return []

    def _get_cdda_stable_releases(self) -> list[GameRelease]:
        """Fetch CDDA stable releases via matching refs for tags starting with '0.'."""
        repo = GameVariant.CDDA.github_repo
        resp = self._client.get(
            f"{self.BASE_URL}/repos/{repo}/git/matching-refs/tags/0."
        )
        if resp.status_code != 200:
            return []

        refs = resp.json()
        # Filter to letter-named releases (0.A and up), skip numeric-only and RC tags
        tags = []
        for ref in refs:
            tag = ref["ref"].replace("refs/tags/", "")
            # Skip old numeric-only versions, RCs, and experimental leak tags
            if "experimental" in tag or "RC" in tag:
                continue
            parts = tag.split(".")
            if len(parts) == 2 and parts[0] == "0":
                letter_part = parts[1].split("-")[0]
                if len(letter_part) == 1 and letter_part.isalpha():
                    tags.append(tag)

        releases: list[GameRelease] = []
        for tag in reversed(tags):  # Newest first
            try:
                resp = self._client.get(
                    f"{self.BASE_URL}/repos/{repo}/releases/tags/{tag}"
                )
                if resp.status_code != 200:
                    continue
                r = resp.json()
                assets_raw = r.get("assets", [])
                if not assets_raw:
                    continue
                assets = [
                    ReleaseAsset(
                        name=a["name"],
                        url=a["browser_download_url"],
                        size=a["size"],
                    )
                    for a in assets_raw
                ]
                releases.append(
                    GameRelease(
                        tag=r["tag_name"],
                        name=r.get("name") or r["tag_name"],
                        channel=ReleaseChannel.STABLE,
                        published_at=r.get("published_at", ""),
                        assets=assets,
                    )
                )
            except Exception:
                continue

        return releases

    @staticmethod
    def _determine_channel(variant: GameVariant, release: dict) -> ReleaseChannel:
        if variant == GameVariant.CDDA:
            return (
                ReleaseChannel.EXPERIMENTAL
                if release.get("prerelease")
                else ReleaseChannel.STABLE
            )
        elif variant == GameVariant.BN:
            return ReleaseChannel.EXPERIMENTAL
        else:  # TLG
            return ReleaseChannel.STABLE

    def close(self):
        self._client.close()
