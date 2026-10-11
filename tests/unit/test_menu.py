"""Menu input regressions using the real selection and search loop."""

import io
from unittest.mock import Mock

import pytest

from catman import menu


@pytest.fixture
def terminal(monkeypatch):
    monkeypatch.setenv("TERM", "xterm")
    cls = menu._BufferedTerminalMenu
    codes = {
        "\x1bOB": "down", "\x1bOA": "up",
        "\x1bOC": "right", "\x1bOD": "left",
        "\r": "enter", "\x1b": "escape", "\x7f": "backspace",
        "\x07": "ctrl-g", "\t": "tab",
    }
    monkeypatch.setattr(cls, "_terminal_code_to_codename", codes)
    monkeypatch.setattr(cls, "_codename_to_terminal_code", {"cursor_down": ""})
    monkeypatch.setattr(cls, "_init_terminal_codes", lambda self: None)
    monkeypatch.setattr(cls, "_init_backspace_control_character", lambda self: None)
    monkeypatch.setattr(cls, "_name_to_control_character", {name: code for code, name in codes.items()})
    monkeypatch.setattr(menu.TerminalMenu, "_num_lines", lambda: 24)

    def init_term(self):
        self._tty_in = Mock()
        self._tty_in.fileno.return_value = 42
        self._tty_out = io.StringIO()

    monkeypatch.setattr(cls, "_init_term", init_term)
    monkeypatch.setattr(cls, "_reset_term", lambda self: None)
    monkeypatch.setattr(cls, "_clear_menu", lambda self: None)
    # Exercise the same length operation that used to crash during rendering.
    monkeypatch.setattr(cls, "_paint_menu", lambda self: len(self._search))
    monkeypatch.setattr(menu, "_HAS_LEFT", True)
    monkeypatch.setattr(menu, "_S1_ACCEPT", ("enter", "right", "left"))
    monkeypatch.setattr(menu, "_COMMON_ACCEPT", ("enter", "right"))
    monkeypatch.setattr(menu, "_QUIT_KEYS", ("escape", "ctrl-g", "left"))

    def feed(chunks, ready=True):
        reader = Mock(side_effect=chunks)
        monkeypatch.setattr(menu.os, "read", reader)
        monkeypatch.setattr(menu.select, "select", lambda *args: ([42] if ready else [], [], []))
        return reader

    return feed


@pytest.mark.parametrize("arrow, expected", [(b"\x1bOB", 2), (b"\x1bOA", 1)])
def test_held_arrow_moves_once_per_key(terminal, arrow, expected):
    terminal([arrow * 20 + b"\r"])
    assert menu.select_one(["One", "Two", "Three"]) == expected


@pytest.mark.parametrize("split", [1, 2, 3, 4, 5])
def test_arrow_sequences_split_across_reads(terminal, split):
    keys = b"\x1bOB\x1bOB\r"
    terminal([keys[:split], keys[split:]])
    assert menu.select_one(["One", "Two", "Three"]) == 2


def test_batched_search_and_navigation(terminal):
    terminal([b"Two\x1bOB\r"])
    assert menu.select_one(["One", "Two A", "Two B"]) == 2


def test_split_unicode_search(terminal):
    terminal([b"caf\xc3", b"\xa9\r"])
    assert menu.select_one(["Tea", "Café"]) == 1


def test_unbound_control_character_does_not_start_search(terminal):
    terminal([b"\x00\x1bOB\r"])
    assert menu.select_one(["One", "Two"]) == 1


@pytest.mark.parametrize("key", [b"\x1b", b"\x07"])
def test_cancel(terminal, key):
    terminal([key], ready=False)
    assert menu.select_one(["One", "Two"]) is None


def test_left_goes_back(terminal):
    terminal([b"\x1bOD"])
    assert menu.select_one(["One", "Two"]) is menu.BACK


def test_right_accepts_after_repeated_arrows(terminal):
    terminal([b"\x1bOB" * 3 + b"\x1bOC"])
    assert menu.select_one(["One", "Two"]) == 1


def test_multiselect_handles_batched_navigation_and_selection(terminal):
    terminal([b"\x1bOB \x1bOB\r"])
    assert menu.select_many(["One", "Two", "Three"]) == [1, 2]


def test_confirmation_handles_repeated_arrows(terminal):
    terminal([b"\x1bOB" * 21 + b"\r"])
    assert menu.confirm("Continue?") is False
