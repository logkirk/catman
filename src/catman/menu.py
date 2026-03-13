import subprocess

from simple_term_menu import TerminalMenu

# Register left/right arrow keys using terminfo so menus can handle them.
# Without this, pressing left/right in search_key=None menus stores the raw
# escape sequence as search text, then wcswidth() returns -1 on it, raising
# ValueError: __len__() should return >= 0.
_ACCEPT_KEYS = ["enter"]
_QUIT_KEYS = ["escape", "ctrl-g"]

for _name, _cap in (("right", "kcuf1"), ("left", "kcub1")):
    try:
        _seq = subprocess.check_output(
            ["tput", _cap], stderr=subprocess.DEVNULL
        ).decode()
        if _seq:
            TerminalMenu._name_to_control_character[_name] = _seq
            if _name == "right":
                _ACCEPT_KEYS.append("right")
            else:
                _QUIT_KEYS.append("left")
    except Exception:
        pass

_ACCEPT_KEYS = tuple(_ACCEPT_KEYS)
_QUIT_KEYS = tuple(_QUIT_KEYS)


def select_one(options: list[str], title: str | None = None) -> int | None:
    """Show a searchable single-select menu. Returns index or None if cancelled."""
    if not options:
        return None
    menu = TerminalMenu(
        options,
        title=title,
        search_key=None,
        accept_keys=_ACCEPT_KEYS,
        quit_keys=_QUIT_KEYS,
    )
    return menu.show()


def select_many(options: list[str], title: str | None = None) -> list[int]:
    """Show a searchable multi-select menu. Returns list of indices."""
    if not options:
        return []
    menu = TerminalMenu(
        options,
        title=title,
        multi_select=True,
        show_multi_select_hint=True,
        accept_keys=_ACCEPT_KEYS,
        quit_keys=_QUIT_KEYS,
    )
    result = menu.show()
    if result is None:
        return []
    if isinstance(result, int):
        return [result]
    return list(result)


def confirm(message: str) -> bool:
    """Show a yes/no confirmation. Returns True if yes."""
    menu = TerminalMenu(
        ["Yes", "No"],
        title=message,
        accept_keys=_ACCEPT_KEYS,
        quit_keys=_QUIT_KEYS,
    )
    return menu.show() == 0
