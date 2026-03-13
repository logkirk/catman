import subprocess

from simple_term_menu import TerminalMenu

# Sentinel returned by select_one when left arrow is pressed (go back one level).
# Distinct from None (which means Escape/cancel = exit the command entirely).
BACK = object()

# Register left/right arrow keys using terminfo so menus can handle them.
# Without this, pressing left/right in search_key=None menus stores the raw
# escape sequence as search text, then wcswidth() returns -1 on it, raising
# ValueError: __len__() should return >= 0.
_COMMON_ACCEPT = ["enter"]
_QUIT_KEYS = ["escape", "ctrl-g"]
_HAS_LEFT = False

for _name, _cap in (("right", "kcuf1"), ("left", "kcub1")):
    try:
        _seq = subprocess.check_output(
            ["tput", _cap], stderr=subprocess.DEVNULL
        ).decode()
        if _seq:
            TerminalMenu._name_to_control_character[_name] = _seq
            if _name == "right":
                _COMMON_ACCEPT.append("right")
            else:
                # left in accept for select_one (detected as BACK)
                # left in quit for select_many/confirm (cancel)
                _QUIT_KEYS.append("left")
                _HAS_LEFT = True
    except Exception:
        pass

_COMMON_ACCEPT = tuple(_COMMON_ACCEPT)
# select_one also accepts left so we can detect it and return BACK
_S1_ACCEPT = _COMMON_ACCEPT + (("left",) if _HAS_LEFT else ())
_QUIT_KEYS = tuple(_QUIT_KEYS)


def select_one(options: list[str], title: str | None = None) -> int | None | object:
    """Show a searchable single-select menu.

    Returns the selected index, None if cancelled (Escape), or BACK if the
    left arrow was pressed (go back one level).
    """
    if not options:
        return None
    menu = TerminalMenu(
        options,
        title=title,
        search_key=None,
        accept_keys=_S1_ACCEPT,
        quit_keys=_QUIT_KEYS,
    )
    result = menu.show()
    if _HAS_LEFT and menu.chosen_accept_key == "left":
        return BACK
    return result


def select_many(options: list[str], title: str | None = None) -> list[int]:
    """Show a searchable multi-select menu. Returns list of indices."""
    if not options:
        return []
    menu = TerminalMenu(
        options,
        title=title,
        multi_select=True,
        show_multi_select_hint=True,
        accept_keys=_COMMON_ACCEPT,
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
        accept_keys=_COMMON_ACCEPT,
        quit_keys=_QUIT_KEYS,
    )
    return menu.show() == 0
