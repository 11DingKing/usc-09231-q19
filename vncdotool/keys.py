"""X11 keysyms used to translate key names."""

from __future__ import annotations

from enum import IntEnum


class Key(IntEnum):
    BackSpace = 0xFF08
    Tab = 0xFF09
    Return = 0xFF0D
    Escape = 0xFF1B
    Delete = 0xFFFF
    Home = 0xFF50
    Left = 0xFF51
    Up = 0xFF52
    Right = 0xFF53
    Down = 0xFF54
    PageUp = 0xFF55
    PageDown = 0xFF56
    Insert = 0xFF63
    ShiftLeft = 0xFFE1
    ShiftRight = 0xFFE2
    ControlLeft = 0xFFE3
    ControlRight = 0xFFE4
    AltLeft = 0xFFE9
    AltRight = 0xFFEA
    MetaLeft = 0xFFE7
    MetaRight = 0xFFE8
    CapsLock = 0xFFE5
    F1 = 0xFFBE
    F2 = 0xFFBF
    F3 = 0xFFC0
    F4 = 0xFFC1
    F5 = 0xFFC2
    F6 = 0xFFC3
    F7 = 0xFFC4
    F8 = 0xFFC5
    F9 = 0xFFC6
    F10 = 0xFFC7
    F11 = 0xFFC8
    F12 = 0xFFC9


KEYMAP: dict[str, int] = {
    "bsp": Key.BackSpace,
    "backspace": Key.BackSpace,
    "tab": Key.Tab,
    "return": Key.Return,
    "enter": Key.Return,
    "esc": Key.Escape,
    "escape": Key.Escape,
    "del": Key.Delete,
    "delete": Key.Delete,
    "home": Key.Home,
    "left": Key.Left,
    "up": Key.Up,
    "right": Key.Right,
    "down": Key.Down,
    "pgup": Key.PageUp,
    "pageup": Key.PageUp,
    "pgdn": Key.PageDown,
    "pagedown": Key.PageDown,
    "ins": Key.Insert,
    "insert": Key.Insert,
    "shift": Key.ShiftLeft,
    "ctrl": Key.ControlLeft,
    "control": Key.ControlLeft,
    "alt": Key.AltLeft,
    "meta": Key.MetaLeft,
    "super": Key.MetaLeft,
    "capslock": Key.CapsLock,
    **{f"f{n}": getattr(Key, f"F{n}") for n in range(1, 13)},
}
