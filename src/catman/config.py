import json
from dataclasses import dataclass, field
from pathlib import Path

from platformdirs import user_data_dir

from .constants import GameVariant


class AppPaths:
    def __init__(self):
        self.base = Path(user_data_dir("catman"))

    @property
    def config_file(self) -> Path:
        return self.base / "config.json"

    @property
    def downloads_dir(self) -> Path:
        return self.base / "downloads"

    def variant_dir(self, variant: GameVariant) -> Path:
        return self.base / "variants" / variant.value

    def builds_dir(self, variant: GameVariant) -> Path:
        return self.variant_dir(variant) / "builds"

    def userdata_dir(self, variant: GameVariant) -> Path:
        return self.variant_dir(variant) / "userdata"

    def backups_dir(self, variant: GameVariant) -> Path:
        return self.variant_dir(variant) / "backups"

    def ensure_dirs(self, variant: GameVariant) -> None:
        for d in [
            self.builds_dir(variant),
            self.userdata_dir(variant),
            self.backups_dir(variant),
            self.userdata_dir(variant) / "mods",
            self.userdata_dir(variant) / "font",
            self.userdata_dir(variant) / "gfx",
            self.userdata_dir(variant) / "sound",
            self.userdata_dir(variant) / "save",
            self.downloads_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)


@dataclass
class Config:
    active_variant: GameVariant = GameVariant.CDDA
    active_builds: dict[str, str] = field(default_factory=dict)

    def save(self, paths: AppPaths) -> None:
        paths.base.mkdir(parents=True, exist_ok=True)
        data = {
            "active_variant": self.active_variant.value,
            "active_builds": self.active_builds,
        }
        paths.config_file.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, paths: AppPaths) -> "Config":
        if not paths.config_file.exists():
            config = cls()
            config.save(paths)
            return config
        try:
            data = json.loads(paths.config_file.read_text())
            return cls(
                active_variant=GameVariant(data.get("active_variant", "cdda")),
                active_builds=data.get("active_builds", {}),
            )
        except (json.JSONDecodeError, ValueError, KeyError):
            return cls()
