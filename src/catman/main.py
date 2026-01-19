import typer
import asyncio
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from catman.config import init_dirs, GAMES, DIRS, POPULAR_DOWNLOADS
from catman.install import get_releases, match_asset, download_file, extract_game
from catman.manager import launch_game, backup_save, install_asset

app = typer.Typer()
console = Console()


def select_game_menu():
    table = Table(title="Select Game")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="magenta")

    keys = list(GAMES.keys())
    for idx, key in enumerate(keys):
        table.add_row(str(idx + 1), GAMES[key]["name"])

    console.print(table)
    choice = Prompt.ask(
        "Enter selection", choices=[str(i + 1) for i in range(len(keys))]
    )
    return keys[int(choice) - 1]


def game_action_menu(game_key):
    while True:
        console.rule(f"[bold red]{GAMES[game_key]['name']}")
        console.print("[1] Launch Game")
        console.print("[2] Install/Update Version")
        console.print("[3] Backup Saves")
        console.print("[4] Download Extras (Mods/Soundpacks)")
        console.print("[5] Back to Main Menu")

        choice = Prompt.ask("Choose action", choices=["1", "2", "3", "4", "5"])

        if choice == "1":
            # List installed versions
            game_dir = DIRS["games"] / game_key.lower()
            if not game_dir.exists() or not any(game_dir.iterdir()):
                console.print("[red]No versions installed![/red]")
                continue

            versions = [d.name for d in game_dir.iterdir() if d.is_dir()]
            for idx, v in enumerate(versions):
                console.print(f"[{idx+1}] {v}")

            v_choice = Prompt.ask(
                "Select version", choices=[str(i + 1) for i in range(len(versions))]
            )
            launch_game(game_key, versions[int(v_choice) - 1])

        elif choice == "2":
            asyncio.run(handle_install(game_key))

        elif choice == "3":
            msg = backup_save(game_key)
            console.print(f"[green]{msg}[/green]")

        elif choice == "4":
            handle_extras(game_key)

        elif choice == "5":
            break


async def handle_install(game_key):
    releases = await get_releases(game_key)

    table = Table(title="Available Releases")
    table.add_column("Index")
    table.add_column("Tag")
    table.add_column("Published")

    for idx, r in enumerate(releases):
        table.add_row(str(idx + 1), r["tag_name"], r["published_at"])

    console.print(table)
    sel = Prompt.ask(
        "Select release to install", choices=[str(i + 1) for i in range(len(releases))]
    )
    release = releases[int(sel) - 1]

    asset_url = match_asset(release["assets"])
    if not asset_url:
        console.print("[red]Could not find a compatible download for your OS.[/red]")
        return

    # Download
    filename = asset_url.split("/")[-1]
    dest = DIRS["cache"] / filename
    await download_file(asset_url, dest)

    # Extract
    console.print("[yellow]Extracting...[/yellow]")
    extract_game(dest, game_key, release["tag_name"])
    console.print(f"[green]Installed {release['tag_name']} successfully![/green]")


def handle_extras(game_key):
    console.print("[1] Soundpacks")
    console.print("[2] Mods")
    console.print("[3] Fonts")
    c = Prompt.ask("Select Type", choices=["1", "2", "3"])

    cat_map = {"1": "soundpacks", "2": "mods", "3": "fonts"}
    category = cat_map[c]

    items = POPULAR_DOWNLOADS[category]
    for idx, item in enumerate(items):
        console.print(f"[{idx+1}] {item['name']}")

    sel = Prompt.ask("Select item", choices=[str(i + 1) for i in range(len(items))])
    item = items[int(sel) - 1]

    dest = DIRS["cache"] / f"extra_{category}_{sel}.zip"
    asyncio.run(download_file(item["url"], dest))
    install_asset(dest, category, game_key)
    console.print("[green]Installed![/green]")


@app.command()
def start():
    init_dirs()
    while True:
        console.clear()
        console.print("[bold green]CatMan - Cataclysm Manager[/bold green]")
        game_key = select_game_menu()
        game_action_menu(game_key)


if __name__ == "__main__":
    app()
