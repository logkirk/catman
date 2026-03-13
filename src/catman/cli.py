import shutil
from pathlib import Path

import cmd2
from rich.console import Console

from .backup import (
    create_backup,
    delete_backup,
    list_backups,
    rename_backup,
    restore_backup,
)
from .config import AppPaths, Config
from .constants import ContentType, GameVariant, ReleaseChannel
from .content import (
    delete_catalog_item,
    get_catalog,
    get_content_dir,
    install_from_catalog,
    is_catalog_item_installed,
)
from .downloader import download_file, extract_archive
from .github import GitHubClient
from .launcher import find_most_recent_world, find_worlds, launch_game
from .menu import BACK, confirm, select_one
from .platform_util import find_matching_asset, get_arch, get_os, open_file_browser

console = Console()


class CatmanShell(cmd2.Cmd):
    intro = (
        "Welcome to catman \u2014 Cataclysm Game Manager\nType 'help' for commands.\n"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.paths = AppPaths()
        self.config = Config.load(self.paths)
        variant = self.config.active_variant
        channel = self.config.get_channel(variant)
        # Migrate legacy userdata/ to channel-specific directory
        if self.paths.migrate_legacy_userdata(variant, channel):
            console.print(f"[dim]Migrated user data to {channel.value} channel.[/dim]")
        self.paths.ensure_dirs(variant, channel)
        self._update_prompt()
        self.hidden_commands.extend(
            [
                "alias",
                "macro",
                "run_script",
                "run_pyscript",
                "shortcuts",
                "edit",
                "shell",
            ]
        )

    def _update_prompt(self):
        v = self.config.active_variant
        ch = self.config.get_channel(v)
        build = self.config.active_builds.get(v.value)
        parts = [v.short_name, ch.value]
        if build:
            parts.append(build)
        self.prompt = f"catman [{'/'.join(parts)}]> "

    @property
    def _variant(self) -> GameVariant:
        return self.config.active_variant

    @property
    def _channel(self) -> ReleaseChannel:
        return self.config.get_channel(self._variant)

    @property
    def _userdata(self) -> Path:
        return self.paths.userdata_dir(self._variant, self._channel)

    @property
    def _builds_dir(self) -> Path:
        return self.paths.builds_dir(self._variant)

    @property
    def _backups_dir(self) -> Path:
        return self.paths.backups_dir(self._variant)

    # ── helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _has_user_content(path: Path) -> bool:
        """Check if a userdata directory has any actual files."""
        if not path.exists():
            return False
        return any(f.is_file() for f in path.rglob("*"))

    def _handle_channel_switch(self, new_channel: ReleaseChannel) -> None:
        """Handle switching to a new channel, prompting to copy data if needed."""
        variant = self._variant
        old_channel = self.config.get_channel(variant)
        new_userdata = self.paths.userdata_dir(variant, new_channel)

        if new_channel != old_channel:
            new_has_data = self._has_user_content(new_userdata)
            if not new_has_data:
                old_userdata = self.paths.userdata_dir(variant, old_channel)
                if self._has_user_content(old_userdata):
                    console.print(
                        f"\n[yellow]Switching to {new_channel.value} channel.[/yellow]"
                    )
                    console.print(
                        "Config files may not be compatible between game versions."
                    )
                    idx = select_one(
                        [
                            f"Copy data from {old_channel.value}",
                            "Start fresh",
                        ],
                        title="User data for new channel",
                    )
                    if idx == 0:
                        shutil.copytree(old_userdata, new_userdata, dirs_exist_ok=True)
                        console.print(
                            f"[green]Copied user data from {old_channel.value}.[/green]"
                        )

        # Always explicitly record the channel
        self.config.set_channel(variant, new_channel)
        self.paths.ensure_dirs(variant, new_channel)
        self._update_prompt()

    # ── variant ─────────────────────────────────────────────────────────

    def do_variant(self, _statement):
        """Switch active game variant."""
        choices = [f"{v.short_name} - {v.display_name}" for v in GameVariant]
        idx = select_one(choices, title="Select game variant")
        if idx is not None and idx is not BACK:
            self.config.active_variant = list(GameVariant)[idx]
            variant = self.config.active_variant
            channel = self.config.get_channel(variant)
            # Migrate legacy userdata if switching to a variant for the first time
            self.paths.migrate_legacy_userdata(variant, channel)
            self.paths.ensure_dirs(variant, channel)
            self.config.save(self.paths)
            self._update_prompt()
            console.print(f"Switched to {variant.display_name}")

    # ── status ──────────────────────────────────────────────────────────

    def do_status(self, _statement):
        """Show current variant, channel, build, and save info."""
        v = self._variant
        ch = self._channel
        console.print(f"[bold]Variant:[/bold]  {v.display_name}")
        console.print(f"[bold]Channel:[/bold]  {ch.value}")

        active_build = self.config.active_builds.get(v.value)
        console.print(
            f"[bold]Build:[/bold]    {active_build or '(none — use download)'}"
        )

        worlds = find_worlds(self._userdata)
        if worlds:
            console.print(f"[bold]Worlds:[/bold]   {', '.join(worlds)}")
            recent = find_most_recent_world(self._userdata)
            if recent:
                console.print(f"[bold]Recent:[/bold]   {recent}")
        else:
            console.print("[bold]Worlds:[/bold]   (none)")

    # ── download ────────────────────────────────────────────────────────

    def do_download(self, _statement):
        """Download a game build."""
        variant = self._variant

        # Channel selection
        if variant.has_stable and variant.has_experimental:
            idx = select_one(["Stable", "Experimental"], title="Select release channel")
            if idx is None or idx is BACK:
                return
            channel = ReleaseChannel.STABLE if idx == 0 else ReleaseChannel.EXPERIMENTAL
        elif variant.has_stable:
            channel = ReleaseChannel.STABLE
        else:
            channel = ReleaseChannel.EXPERIMENTAL

        console.print(
            f"Fetching {channel.value} releases for {variant.display_name}..."
        )

        try:
            client = GitHubClient()
            if channel == ReleaseChannel.STABLE:
                releases = client.get_stable_releases(variant)
            else:
                releases = [
                    r
                    for r in client.get_all_game_releases(variant)
                    if r.channel == channel
                ]
            client.close()
        except Exception as e:
            console.print(f"[red]Error fetching releases: {e}[/red]")
            return
        if not releases:
            console.print(f"[yellow]No {channel.value} releases found.[/yellow]")
            return

        # Version menu
        items = [f"{r.name}  ({r.tag})  {r.published_at[:10]}" for r in releases]
        idx = select_one(items, title=f"Select {channel.value} version")
        if idx is None or idx is BACK:
            return
        release = releases[idx]

        # Build type
        type_idx = select_one(
            ["Tiles (graphical)", "Curses (terminal)"], title="Select build type"
        )
        if type_idx is None or type_idx is BACK:
            return
        tiles = type_idx == 0

        # Find matching asset
        os_name = get_os()
        arch = get_arch()
        asset = find_matching_asset(release.assets, os_name, arch, tiles)
        if asset is None:
            console.print(f"[red]No matching build found for {os_name}/{arch}.[/red]")
            if release.assets:
                console.print("Available assets:")
                for a in release.assets:
                    console.print(f"  - {a.name}")
            return

        console.print(f"Downloading: {asset.name}")

        downloads_dir = self.paths.downloads_dir
        downloads_dir.mkdir(parents=True, exist_ok=True)
        archive_path = downloads_dir / asset.name

        try:
            download_file(asset.url, archive_path)
        except Exception as e:
            console.print(f"[red]Download failed: {e}[/red]")
            return

        build_name = release.tag
        build_dir = self._builds_dir / build_name
        if build_dir.exists():
            shutil.rmtree(build_dir)
        build_dir.mkdir(parents=True, exist_ok=True)

        console.print("Extracting...")
        try:
            extract_archive(archive_path, build_dir)
        except Exception as e:
            console.print(f"[red]Extraction failed: {e}[/red]")
            return
        finally:
            archive_path.unlink(missing_ok=True)

        self.config.register_build(self._variant, build_name, channel)
        self._handle_channel_switch(channel)
        self.config.active_builds[self._variant.value] = build_name
        self.config.save(self.paths)
        self._update_prompt()
        console.print(f"[green]Build {build_name} installed and set as active.[/green]")

    # ── builds ──────────────────────────────────────────────────────────

    def do_builds(self, _statement):
        """List and manage downloaded builds."""
        variant = self._variant
        while True:
            idx = select_one(
                ["Manage builds", "Open builds folder", "Back"],
                title="Build Management",
            )
            if idx is None or idx is BACK or idx == 2:
                return
            if idx == 1:
                self._builds_dir.mkdir(parents=True, exist_ok=True)
                console.print(f"Opening {self._builds_dir}")
                open_file_browser(str(self._builds_dir))
                return
            if self._builds_manage(variant) is not BACK:
                return

    def _builds_manage(self, variant: GameVariant) -> object:
        """Build selection. Returns BACK to re-show tier-1, None to exit."""
        if not self._builds_dir.exists():
            console.print("No builds yet. Use 'download' to get started.")
            return None
        builds = sorted(
            [d.name for d in self._builds_dir.iterdir() if d.is_dir()], reverse=True
        )
        if not builds:
            console.print("No builds found.")
            return None
        active = self.config.active_builds.get(variant.value)
        labels = []
        for b in builds:
            label = b
            ch = self.config.get_build_channel(variant, b)
            if ch:
                label += f"  [{ch.value}]"
            if b == active:
                label += "  [active]"
            labels.append(label)
        while True:
            bidx = select_one(labels, title="Select build")
            if bidx is None:
                return None
            if bidx is BACK:
                return BACK
            if self._builds_action(variant, builds[bidx]) is not BACK:
                return None

    def _builds_action(self, variant: GameVariant, build_name: str) -> object:
        """Build action menu. Returns BACK to re-show build list, None to exit."""
        action_idx = select_one(["Set active", "Delete", "Back"], title=build_name)
        if action_idx is None:
            return None
        if action_idx is BACK or action_idx == 2:
            return BACK
        if action_idx == 0:
            ch = self.config.get_build_channel(variant, build_name)
            if ch:
                self._handle_channel_switch(ch)
            self.config.active_builds[variant.value] = build_name
            self.config.save(self.paths)
            self._update_prompt()
            console.print(f"[green]Active build: {build_name}[/green]")
        elif action_idx == 1:
            if confirm(f"Delete build {build_name}?"):
                shutil.rmtree(self._builds_dir / build_name)
                if self.config.active_builds.get(variant.value) == build_name:
                    del self.config.active_builds[variant.value]
                    self.config.save(self.paths)
                self._update_prompt()
                console.print(f"[green]Deleted {build_name}[/green]")
        return None

    # ── launch ──────────────────────────────────────────────────────────

    def do_launch(self, _statement):
        """Launch the active game build."""
        active_build = self.config.active_builds.get(self._variant.value)
        if not active_build:
            console.print("No active build. Use 'download' first.")
            return

        build_path = self._builds_dir / active_build
        if not build_path.exists():
            console.print(f"[red]Build directory missing: {build_path}[/red]")
            return

        recent_world = find_most_recent_world(self._userdata)
        world = None
        if recent_world:
            idx = select_one(
                ["Launch game", f"Launch into world: {recent_world}"],
                title="Launch options",
            )
            if idx is None or idx is BACK:
                return
            if idx == 1:
                world = recent_world

        console.print(f"Launching {self._variant.display_name}...")
        try:
            launch_game(build_path, self._userdata, world=world)
        except (FileNotFoundError, RuntimeError) as e:
            console.print(f"[red]{e}[/red]")

    # ── backups ─────────────────────────────────────────────────────────

    def do_backups(self, _statement):
        """Manage save backups."""
        while True:
            idx = select_one(
                ["Manage backups", "Open backups folder", "Back"],
                title="Backup Management",
            )
            if idx is None or idx is BACK or idx == 2:
                return
            if idx == 1:
                self._backups_dir.mkdir(parents=True, exist_ok=True)
                console.print(f"Opening {self._backups_dir}")
                open_file_browser(str(self._backups_dir))
                return
            if self._backups_manage() is not BACK:
                return

    def _backups_manage(self) -> object:
        """Backup selection. Returns BACK to re-show tier-1, None to exit."""
        save_dir = self._userdata / "save"
        while True:
            backups = list_backups(self._backups_dir)
            items = ["+ Create new backup"] + [
                f"{b.name}  ({b.created_at:%Y-%m-%d %H:%M}, {b.size // 1024}KB)"
                for b in backups
            ]
            bidx = select_one(items, title="Backups")
            if bidx is None:
                return None
            if bidx is BACK:
                return BACK
            if bidx == 0:
                name = input("Backup name (enter for auto): ").strip() or None
                try:
                    backup = create_backup(save_dir, self._backups_dir, name)
                    console.print(f"[green]Created backup: {backup.name}[/green]")
                except FileNotFoundError:
                    console.print("[yellow]No saves to back up.[/yellow]")
                continue  # refresh list
            if self._backups_action(backups[bidx - 1], save_dir) is not BACK:
                return None

    def _backups_action(self, backup, save_dir: Path) -> object:
        """Backup action menu. Returns BACK to re-show backup list, None to exit."""
        action_idx = select_one(
            ["Restore", "Rename", "Delete", "Back"], title=backup.name
        )
        if action_idx is None:
            return None
        if action_idx is BACK or action_idx == 3:
            return BACK
        if action_idx == 0:
            if confirm("Restore? This overwrites current saves."):
                restore_backup(backup, save_dir)
                console.print(f"[green]Restored: {backup.name}[/green]")
        elif action_idx == 1:
            new_name = input("New name: ").strip()
            if new_name:
                rename_backup(backup, new_name)
                console.print(f"[green]Renamed to {new_name}[/green]")
        elif action_idx == 2:
            if confirm(f"Delete {backup.name}?"):
                delete_backup(backup)
                console.print("[green]Deleted.[/green]")
        return None

    # ── data management ───────────────────────────────────────────────

    def do_data(self, _statement):
        """Manage user data directory."""
        variant = self._variant
        channel = self._channel

        actions = [
            "Delete current user data",
        ]

        # Offer copy between channels for variants with both
        if variant.has_stable and variant.has_experimental:
            other = (
                ReleaseChannel.EXPERIMENTAL
                if channel == ReleaseChannel.STABLE
                else ReleaseChannel.STABLE
            )
            actions.append(f"Copy data from {other.value} channel")

        actions.append("Open data folder")
        actions.append("Back")

        idx = select_one(actions, title="User Data Management")
        if idx is None or idx is BACK or actions[idx] == "Back":
            return

        action = actions[idx]

        if action == "Delete current user data":
            if confirm(
                f"Delete ALL user data for {variant.short_name}/{channel.value}? "
                "This cannot be undone."
            ):
                userdata = self._userdata
                if userdata.exists():
                    shutil.rmtree(userdata)
                self.paths.ensure_dirs(variant, channel)
                console.print("[green]User data deleted.[/green]")

        elif action.startswith("Copy data from"):
            other = (
                ReleaseChannel.EXPERIMENTAL
                if channel == ReleaseChannel.STABLE
                else ReleaseChannel.STABLE
            )
            other_userdata = self.paths.userdata_dir(variant, other)
            if not self._has_user_content(other_userdata):
                console.print(
                    f"[yellow]No data found for {other.value} channel.[/yellow]"
                )
                return
            if confirm(
                f"Copy data from {other.value}? "
                f"This will overwrite current {channel.value} data."
            ):
                current = self._userdata
                if current.exists():
                    shutil.rmtree(current)
                shutil.copytree(other_userdata, current)
                console.print(f"[green]Copied data from {other.value} channel.[/green]")

        elif action == "Open data folder":
            userdata = self._userdata
            userdata.mkdir(parents=True, exist_ok=True)
            console.print(f"Opening {userdata}")
            open_file_browser(str(userdata))

    # ── content management ──────────────────────────────────────────────

    def _content_command(self, content_type: ContentType):
        """Generic handler for mods/fonts/soundpacks/tilesets."""
        label = content_type.display_name.lower()
        content_dir = get_content_dir(self._userdata, content_type)
        while True:
            idx = select_one(
                [f"Manage popular {label}", f"Open {label} folder", "Back"],
                title=f"{content_type.display_name} Management",
            )
            if idx is None or idx is BACK or idx == 2:
                return
            if idx == 1:
                content_dir.mkdir(parents=True, exist_ok=True)
                console.print(f"Opening {content_dir}")
                open_file_browser(str(content_dir))
                return
            catalog = get_catalog(content_type, self._variant)
            if not catalog:
                console.print(
                    f"[yellow]No {label} available for {self._variant.display_name}.[/yellow]"
                )
                return
            if self._content_manage(content_type, catalog) is not BACK:
                return

    def _content_manage(self, content_type: ContentType, catalog: list) -> object:
        """Content item selection. Returns BACK to re-show tier-1, None to exit."""
        label = content_type.display_name.lower()
        while True:
            items = [
                f"{item.name} \u2014 {item.description}"
                + (
                    "  [installed]"
                    if is_catalog_item_installed(item, self._userdata)
                    else ""
                )
                for item in catalog
            ]
            cidx = select_one(items, title=f"Select {label}")
            if cidx is None:
                return None
            if cidx is BACK:
                return BACK
            if self._content_action(catalog[cidx]) is not BACK:
                return None

    def _content_action(self, selected) -> object:
        """Content action menu. Returns BACK to re-show item list, None to exit."""
        installed = is_catalog_item_installed(selected, self._userdata)
        if installed:
            action_idx = select_one(["Update", "Delete", "Back"], title=selected.name)
            if action_idx is None:
                return None
            if action_idx is BACK or action_idx == 2:
                return BACK
            if action_idx == 0:
                console.print(f"Updating {selected.name}...")
                try:
                    result = install_from_catalog(selected, self._userdata)
                    console.print(f"[green]Updated: {result}[/green]")
                except Exception as e:
                    console.print(f"[red]Update failed: {e}[/red]")
            elif action_idx == 1:
                if confirm(f"Delete {selected.name}?"):
                    try:
                        delete_catalog_item(selected, self._userdata)
                        console.print(f"[green]Deleted {selected.name}.[/green]")
                    except Exception as e:
                        console.print(f"[red]Delete failed: {e}[/red]")
        else:
            action_idx = select_one(["Install", "Back"], title=selected.name)
            if action_idx is None:
                return None
            if action_idx is BACK or action_idx == 1:
                return BACK
            console.print(f"Installing {selected.name}...")
            try:
                result = install_from_catalog(selected, self._userdata)
                console.print(f"[green]Installed: {result}[/green]")
            except Exception as e:
                console.print(f"[red]Installation failed: {e}[/red]")
        return None

    def do_mods(self, _statement):
        """Manage mods."""
        self._content_command(ContentType.MODS)

    def do_fonts(self, _statement):
        """Manage fonts."""
        self._content_command(ContentType.FONTS)

    def do_soundpacks(self, _statement):
        """Manage soundpacks."""
        self._content_command(ContentType.SOUNDPACKS)

    def do_tilesets(self, _statement):
        """Manage tilesets."""
        self._content_command(ContentType.TILESETS)
