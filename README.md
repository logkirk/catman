# catman

CLI game management tool for [Cataclysm: Dark Days Ahead](https://github.com/CleverRaven/Cataclysm-DDA), [Cataclysm: Bright Nights](https://github.com/cataclysmbn/Cataclysm-BN), and [Cataclysm: The Last Generation](https://github.com/Cataclysm-TLG/Cataclysm-TLG).

Download, launch, and manage builds, mods, fonts, soundpacks, tilesets, and save backups — all from one interactive shell.

## Installation

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
uv tool install catman
```

Then run:

```bash
catman
```

## Developer setup

```bash
git clone https://github.com/user/catman.git
cd catman
uv venv
uv pip install -e .
uv run catman
```

## Usage

catman launches an interactive shell. Use `help` to see available commands:

- `variant` — switch between CDDA, BN, and TLG
- `download` — download stable or experimental builds
- `builds` — list and select downloaded builds
- `launch` — launch the game
- `mods` / `fonts` / `soundpacks` / `tilesets` — manage game content
- `backups` — save and restore backups

Set `GITHUB_TOKEN` in your environment to avoid GitHub API rate limits.
