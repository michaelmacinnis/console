import curses.ascii
import subprocess

import debug

# Actions.
def cursor_down(buffer, key):
    buffer.row += 1
    buffer.y += 1


def cursor_left(buffer, key):
    buffer.col -= 1
    buffer.x -= 1


def cursor_next_page(buffer, key):
    buffer.row = min(len(buffer.text), buffer.row + buffer.height)
    if buffer.row == len(buffer.text):
        buffer.y = buffer.height - 1


def cursor_prev_page(buffer, key):
    buffer.row = max(1, buffer.row - buffer.height)
    if buffer.row == 1:
        buffer.y = 0


def cursor_right(buffer, key):
    buffer.col += 1
    buffer.x += 1


def cursor_up(buffer, key):
    buffer.row -= 1
    buffer.y -= 1


def delete_char(buffer, key):
    if not buffer.col:
        # At the beginning of a line.
        prev = buffer.row - 1
        if prev > 0:
            # There are previous lines.
            buffer.col = len(buffer.text[prev - 1])
            buffer.text[prev - 1] += buffer.text[buffer.row - 1]
            buffer.text = buffer.text[:prev] + buffer.text[buffer.row :]
            buffer.row = prev
            buffer.x = buffer.col
            buffer.y -= 1
        return

    line = buffer.text[buffer.row - 1]
    buffer.text[buffer.row - 1] = line[: buffer.col - 1] + line[buffer.col :]
    buffer.col -= 1
    buffer.x -= 1


def insert_char(buffer, key):
    if key == "^J":
        if buffer.command:
            text = "\n".join(buffer.text + [""]).encode("utf8")
            debug.log(text)
            if buffer.multiline:
                r = subprocess.run(["sh", "-n"], input=text, capture_output=True)
                debug.log(r)
                if r.stderr:
                    text = None
            if text:
                buffer.multiline = False
                buffer._cmd = text
                buffer.clear()
                return

        buffer.text = (
            buffer.text[: buffer.row - 1]
            + [buffer.text[buffer.row - 1][: buffer.col]]
            + [buffer.text[buffer.row - 1][buffer.col :]]
            + buffer.text[buffer.row :]
        )
        buffer.col = 0
        buffer.row += 1
        buffer.x = 0
        buffer.y += 1
        return

    if key == "^Q":
        if buffer.command:
            if len(buffer.text) == 1 and not len(buffer.text[0]):
                buffer._cmd = b"\x04"
                buffer.clear()
                return

    if len(key) == 1 and curses.ascii.isprint(ord(key)):
        line = buffer.text[buffer.row - 1]
        buffer.text[buffer.row - 1] = line[: buffer.col] + key + line[buffer.col :]
        buffer.col += 1
        buffer.x += 1


def save_file(buffer, key):
    if buffer.filename:
        with open(buffer.filename, "w") as file:
            file.write("\n".join(buffer.text))
            file.write("\n")


bindings = {
    "KEY_BACKSPACE": delete_char,
    "KEY_DOWN": cursor_down,
    "KEY_LEFT": cursor_left,
    "KEY_NPAGE": cursor_next_page,
    "KEY_PPAGE": cursor_prev_page,
    "KEY_RIGHT": cursor_right,
    "KEY_UP": cursor_up,
    "^S": save_file,
}
