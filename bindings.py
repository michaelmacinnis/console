from actions import *


def cli(key):
    return cli_bindings.get(key, command_insert_char)


def editor(key):
    return editor_bindings.get(key, insert_char)


default_bindings = {
    "^X": cut_selection,
    "^C": copy_selection,
    "^V": paste_selection,
    "kEND5": cursor_end_of_buffer,
    "kHOM5": cursor_start_of_buffer,
    "KEY_BACKSPACE": delete_char,
    "KEY_DOWN": cursor_down,
    "KEY_END": cursor_end_of_line,
    "KEY_HOME": cursor_start_of_line,
    "KEY_LEFT": cursor_left,
    "KEY_NPAGE": cursor_next_page,
    "KEY_PPAGE": cursor_prev_page,
    "KEY_RIGHT": cursor_right,
    "KEY_UP": cursor_up,
}

cli_bindings = default_bindings.copy()

editor_bindings = default_bindings.copy()
editor_bindings.update({"^S": save_file})
