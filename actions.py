import curses.ascii
import subprocess

import debug

# Actions.
def command_insert_char(panel, key):
    if key == "^J":
        text = "\n".join(panel.text + [""]).encode("utf8")
        debug.log(text)

        if panel.multiline:
            r = subprocess.run(["sh", "-n"], input=text, capture_output=True)
            debug.log(r)
            if r.stderr:
                text = None
        if text:
            panel.complete = text
            panel.clear()
            return

    if key == "^Q":
        if len(panel.text) == 1 and not len(panel.text[0]):
            panel.complete = b"\x04"
            panel.clear()
            return

    insert_char(panel, key)


def cursor_down(panel, key):
    panel.row += 1
    panel.y += 1


def cursor_end_of_buffer(panel, key):
    panel.row = len(panel.text)
    panel.col = len(panel.text[panel.row - 1])
    panel.x = panel.col
    panel.y = panel.row - 1


def cursor_end_of_line(panel, key):
    panel.col = len(panel.text[panel.row - 1])
    panel.x = panel.col


def cursor_left(panel, key):
    panel.col -= 1
    panel.x -= 1


def cursor_next_page(panel, key):
    panel.row = min(len(panel.text), panel.row + panel.height)
    if panel.row == len(panel.text):
        panel.y = panel.height - 1


def cursor_prev_page(panel, key):
    panel.row = max(1, panel.row - panel.height)
    if panel.row == 1:
        panel.y = 0


def cursor_right(panel, key):
    panel.col += 1
    panel.x += 1


def cursor_start_of_buffer(panel, key):
    panel.col = 0
    panel.row = 1
    panel.x = 0
    panel.y = 0


def cursor_start_of_line(panel, key):
    panel.col = 0
    panel.x = 0


def cursor_up(panel, key):
    panel.row -= 1
    panel.y -= 1


def delete_char(panel, key):
    if not panel.col:
        # At the beginning of a line.
        prev = panel.row - 1
        if prev > 0:
            # There are previous lines.
            panel.col = len(panel.text[prev - 1])
            panel.text[prev - 1] += panel.text[panel.row - 1]
            panel.text = panel.text[:prev] + panel.text[panel.row :]
            panel.row = prev
            panel.x = panel.col
            panel.y -= 1
        return

    line = panel.text[panel.row - 1]
    panel.text[panel.row - 1] = line[: panel.col - 1] + line[panel.col :]
    panel.col -= 1
    panel.x -= 1


def insert_char(panel, key):
    if key == "^J":
        panel.text = (
            panel.text[: panel.row - 1]
            + [panel.text[panel.row - 1][: panel.col]]
            + [panel.text[panel.row - 1][panel.col :]]
            + panel.text[panel.row :]
        )
        panel.col = 0
        panel.row += 1
        panel.x = 0
        panel.y += 1
        return

    if len(key) == 1 and curses.ascii.isprint(ord(key)):
        line = panel.text[panel.row - 1]
        panel.text[panel.row - 1] = line[: panel.col] + key + line[panel.col :]
        panel.col += 1
        panel.x += 1


def save_file(panel, key):
    if panel.filename:
        with open(panel.filename, "w") as file:
            file.write("\n".join(panel.text))
            file.write("\n")


default = {
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

cli = default.copy()

editor = default.copy()
editor.update({"^S": save_file})
