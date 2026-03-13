import json
from dataclasses import dataclass, field
from pathlib import Path

from platformdirs import user_data_dir

from .constants import GameVariant, ReleaseChannel


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

    def userdata_dir(self, variant: GameVariant, channel: ReleaseChannel) -> Path:
        return self.variant_dir(variant) / f"userdata-{channel.value}"

    def legacy_userdata_dir(self, variant: GameVariant) -> Path:
        return self.variant_dir(variant) / "userdata"

    def backups_dir(self, variant: GameVariant) -> Path:
        return self.variant_dir(variant) / "backups"

    def migrate_legacy_userdata(
        self, variant: GameVariant, channel: ReleaseChannel
    ) -> bool:
        """Migrate old userdata/ to channel-specific directory. Returns True if migrated."""
        legacy = self.legacy_userdata_dir(variant)
        target = self.userdata_dir(variant, channel)
        if legacy.is_dir() and not legacy.is_symlink() and not target.exists():
            legacy.rename(target)
            return True
        return False

    def ensure_dirs(self, variant: GameVariant, channel: ReleaseChannel) -> None:
        ud = self.userdata_dir(variant, channel)
        for d in [
            self.builds_dir(variant),
            ud,
            self.backups_dir(variant),
            ud / "mods",
            ud / "font",
            ud / "gfx",
            ud / "sound",
            ud / "save",
            ud / "config",
            self.downloads_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)


@dataclass
class Config:
    active_variant: GameVariant = GameVariant.CDDA
    active_builds: dict[str, str] = field(default_factory=dict)
    active_channels: dict[str, str] = field(default_factory=dict)
    build_channels: dict[str, dict[str, str]] = field(default_factory=dict)

    def get_channel(self, variant: GameVariant) -> ReleaseChannel:
        """Get active channel for variant, defaulting sensibly."""
        ch = self.active_channels.get(variant.value)
        if ch:
            return ReleaseChannel(ch)
        if variant.has_stable:
            return ReleaseChannel.STABLE
        return ReleaseChannel.EXPERIMENTAL

    def set_channel(self, variant: GameVariant, channel: ReleaseChannel) -> None:
        self.active_channels[variant.value] = channel.value

    def register_build(
        self, variant: GameVariant, build_tag: str, channel: ReleaseChannel
    ) -> None:
        """Record which channel a build belongs to."""
        if variant.value not in self.build_channels:
            self.build_channels[variant.value] = {}
        self.build_channels[variant.value][build_tag] = channel.value

    def get_build_channel(
        self, variant: GameVariant, build_tag: str
    ) -> ReleaseChannel | None:
        """Get the channel a build belongs to, if known."""
        ch = self.build_channels.get(variant.value, {}).get(build_tag)
        if ch:
            return ReleaseChannel(ch)
        return None

    def save(self, paths: AppPaths) -> None:
        paths.base.mkdir(parents=True, exist_ok=True)
        data = {
            "active_variant": self.active_variant.value,
            "active_builds": self.active_builds,
            "active_channels": self.active_channels,
            "build_channels": self.build_channels,
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
                active_channels=data.get("active_channels", {}),
                build_channels=data.get("build_channels", {}),
            )
        except (json.JSONDecodeError, ValueError, KeyError):
            return cls()
