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
        name="CC-Sounds (full)",
        description="Comprehensive community soundpack with wide coverage",
        url="https://github.com/Fris0uman/CDDA-Soundpacks/releases/latest/download/CC-Sounds.zip",
        content_type=ContentType.SOUNDPACKS,
        variants=[GameVariant.CDDA, GameVariant.TLG],
        is_github_repo=False,
    ),
    ContentItem(
        name="CC-Sounds (sfx only)",
        description="CC-Sounds SFX-only (no music)",
        url="https://github.com/Fris0uman/CDDA-Soundpacks/releases/latest/download/CC-Sounds-sfx-only.zip",
        content_type=ContentType.SOUNDPACKS,
        variants=[GameVariant.CDDA, GameVariant.TLG],
        is_github_repo=False,
    ),
    ContentItem(
        name="CC-Sounds (music only)",
        description="CO.AG Music ambient soundtrack",
        url="https://github.com/Fris0uman/CDDA-Soundpacks/releases/latest/download/CO.AG-music-only.zip",
        content_type=ContentType.SOUNDPACKS,
        variants=[GameVariant.CDDA, GameVariant.TLG],
        is_github_repo=False,
    ),
    ContentItem(
        name="BeepBoopBip",
        description="Retro beep/boop sound effects",
        url="https://github.com/Golfavel/CDDA-Soundpacks_BeepBoop/archive/refs/heads/master.zip",
        content_type=ContentType.SOUNDPACKS,
        variants=[GameVariant.CDDA, GameVariant.TLG],
        is_github_repo=False,
    ),
    ContentItem(
        name="@s",
        description="Damalsk's community soundpack",
        url="https://github.com/damalsk/damalsksoundpack/archive/refs/heads/master.zip",
        content_type=ContentType.SOUNDPACKS,
        variants=[GameVariant.CDDA, GameVariant.TLG],
        is_github_repo=False,
    ),
    ContentItem(
        name="budg3",
        description="budg3's CDDA soundpack",
        url="https://github.com/budg3/CDDA-Soundpack/archive/refs/heads/master.zip",
        content_type=ContentType.SOUNDPACKS,
        variants=[GameVariant.CDDA, GameVariant.TLG],
        is_github_repo=False,
    ),
    ContentItem(
        name="ChestHole",
        description="ChestHole soundpack",
        url="https://web.archive.org/web/2/https://chezzo.com/cataclysm/ChestHoleSoundPack.zip",
        content_type=ContentType.SOUNDPACKS,
        variants=[GameVariant.CDDA, GameVariant.TLG],
        is_github_repo=False,
    ),
    ContentItem(
        name="ChestHole (CC-licensed)",
        description="ChestHole CC-licensed soundpack",
        url="https://web.archive.org/web/2/https://chezzo.com/cataclysm/ChestHoleCCSoundPack.zip",
        content_type=ContentType.SOUNDPACKS,
        variants=[GameVariant.CDDA, GameVariant.TLG],
        is_github_repo=False,
    ),
    ContentItem(
        name="ChestHole (Old Timey)",
        description="ChestHole Old Timey soundpack",
        url="https://web.archive.org/web/2/https://chezzo.com/cataclysm/ChestOldTimeySoundPack.zip",
        content_type=ContentType.SOUNDPACKS,
        variants=[GameVariant.CDDA, GameVariant.TLG],
        is_github_repo=False,
    ),
    ContentItem(
        name="Otopack",
        description="Otopack community soundpack",
        url="https://github.com/Kenan2000/Otopack-Mods-Updates/archive/refs/heads/master.zip",
        content_type=ContentType.SOUNDPACKS,
        variants=[GameVariant.CDDA, GameVariant.TLG],
        is_github_repo=False,
    ),
    ContentItem(
        name="Otopack",
        description="Otopack for Bright Nights",
        url="https://github.com/NarandBD/Otopack-BN-Mk-2/archive/refs/heads/master.zip",
        content_type=ContentType.SOUNDPACKS,
        variants=[GameVariant.BN],
        is_github_repo=False,
    ),
    ContentItem(
        name="RRFSounds",
        description="RRF community soundpack",
        url="https://www.dropbox.com/s/9tfsd8g8apdgyxo/RRFSounds.zip?dl=1",
        content_type=ContentType.SOUNDPACKS,
        variants=[GameVariant.CDDA, GameVariant.TLG],
        is_github_repo=False,
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
