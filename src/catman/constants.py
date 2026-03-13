from dataclasses import dataclass, field
from enum import Enum


class GameVariant(Enum):
    CDDA = "cdda"
    BN = "bn"
    TLG = "tlg"

    @property
    def display_name(self) -> str:
        names = {
            GameVariant.CDDA: "Cataclysm: Dark Days Ahead",
            GameVariant.BN: "Cataclysm: Bright Nights",
            GameVariant.TLG: "Cataclysm: The Last Generation",
        }
        return names[self]

    @property
    def short_name(self) -> str:
        return self.value.upper()

    @property
    def github_repo(self) -> str:
        repos = {
            GameVariant.CDDA: "CleverRaven/Cataclysm-DDA",
            GameVariant.BN: "cataclysmbn/Cataclysm-BN",
            GameVariant.TLG: "Cataclysm-TLG/Cataclysm-TLG",
        }
        return repos[self]

    @property
    def has_stable(self) -> bool:
        return self in (GameVariant.CDDA, GameVariant.TLG)

    @property
    def has_experimental(self) -> bool:
        return self in (GameVariant.CDDA, GameVariant.BN)


class ReleaseChannel(Enum):
    STABLE = "stable"
    EXPERIMENTAL = "experimental"


class ContentType(Enum):
    MODS = "mods"
    FONTS = "font"
    SOUNDPACKS = "sound"
    TILESETS = "gfx"

    @property
    def display_name(self) -> str:
        names = {
            ContentType.MODS: "Mods",
            ContentType.FONTS: "Fonts",
            ContentType.SOUNDPACKS: "Soundpacks",
            ContentType.TILESETS: "Tilesets",
        }
        return names[self]

    @property
    def userdata_dir(self) -> str:
        return self.value


@dataclass
class ContentItem:
    name: str
    description: str
    url: str
    content_type: ContentType
    variants: list[GameVariant] = field(default_factory=list)
    is_github_repo: bool = True


CONTENT_CATALOG: list[ContentItem] = [
    # --- Soundpacks ---
    ContentItem(
        name="CC-Sounds",
        description="Comprehensive community soundpack with wide coverage",
        url="https://github.com/Fris0uman/CDDA-Soundpacks",
        content_type=ContentType.SOUNDPACKS,
        variants=[GameVariant.CDDA, GameVariant.TLG],
    ),
    # --- Tilesets ---
    ContentItem(
        name="UltimateCataclysm",
        description="Popular community tileset with extensive coverage",
        url="https://github.com/I-am-Erk/CDDA-Tilesets",
        content_type=ContentType.TILESETS,
        variants=[GameVariant.CDDA, GameVariant.TLG],
    ),
    # --- Mods ---
    ContentItem(
        name="CDDA-Kenan-Modpack",
        description="Large collection of community mods",
        url="https://github.com/Kenan2000/CDDA-Structured-Kenan-Modpack",
        content_type=ContentType.MODS,
        variants=[GameVariant.CDDA],
    ),
    ContentItem(
        name="BN-Kenan-Modpack",
        description="Large collection of community mods for Bright Nights",
        url="https://github.com/Kenan2000/Bright-Nights-Kenan-Modpack",
        content_type=ContentType.MODS,
        variants=[GameVariant.BN],
    ),
    # --- Fonts ---
    ContentItem(
        name="Terminus TTF",
        description="Clean bitmap-style font, great for roguelikes",
        url="https://files.ax86.net/terminus-ttf/files/latest.zip",
        content_type=ContentType.FONTS,
        variants=[GameVariant.CDDA, GameVariant.BN, GameVariant.TLG],
        is_github_repo=False,
    ),
]
