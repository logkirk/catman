from simple_term_menu import TerminalMenu


def select_one(options: list[str], title: str | None = None) -> int | None:
    """Show a searchable single-select menu. Returns index or None if cancelled."""
    if not options:
        return None
    menu = TerminalMenu(options, title=title, search_key=None)
    return menu.show()


def select_many(options: list[str], title: str | None = None) -> list[int]:
    """Show a searchable multi-select menu. Returns list of indices."""
    if not options:
        return []
    menu = TerminalMenu(
        options, title=title, multi_select=True, show_multi_select_hint=True
    )
    result = menu.show()
    if result is None:
        return []
    if isinstance(result, int):
        return [result]
    return list(result)


def confirm(message: str) -> bool:
    """Show a yes/no confirmation. Returns True if yes."""
    menu = TerminalMenu(["Yes", "No"], title=message)
    return menu.show() == 0
