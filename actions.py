import curses
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


def copy_selection(panel, key):
    if any(n < 0 for n in (panel.r, panel.s, panel.u, panel.v)):
        return

    if panel.s == panel.v:
        panel.clipboard = [panel.text[panel.s - 1][panel.r : panel.u]]
        return

    panel.clipboard = [panel.text[panel.s - 1][panel.r :]]

    idx = panel.s + 1
    while idx < panel.v:
        panel.clipboard.append(panel.text[idx - 1])
        idx += 1

    panel.clipboard.append(panel.text[panel.v - 1][: panel.u])


#    if panel.row >= panel.s:
#        panel.row += idx
#        panel.y += idx


def cut_selection(panel, key):
    copy_selection(panel, key)

    panel.text[panel.s - 1] = (
        panel.text[panel.s - 1][: panel.r] + panel.text[panel.v - 1][panel.u :]
    )

    if panel.s != panel.v:
        panel.text = panel.text[: panel.s] + panel.text[panel.v :]

    delta = panel.v - panel.s
    if delta and panel.row >= panel.s:
        panel.row -= delta
        panel.y -= delta

    panel.markr = -1
    panel.marks = -1
    panel.r = -1
    panel.s = -1
    panel.u = -1
    panel.v = -1

    return


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


def mouse_left_pressed(panel, x, y):
    debug.log("mouse_left_pressed")

    panel.marks = min(y + panel.row - panel.y, len(panel.text))
    panel.markr = min(x + panel.col - panel.x, len(panel.text[panel.marks - 1]) + 1)

    panel.pressx = x
    panel.pressy = y

    panel.r = -1
    panel.s = -1
    panel.u = -1
    panel.v = -1


def mouse_left_released(panel, x, y):
    debug.log("mouse_left_released")

    if panel.pressx == x and panel.pressy == y:
        panel.col += x - panel.x
        panel.row += y - panel.y
        panel.x = x
        panel.y = y

    panel.pressx = -1
    panel.pressy = -1

    if panel.markr == -1 or panel.marks == -1:
        return

    mouse_move(panel, x, y)

    panel.markr = -1
    panel.marks = -1


def mouse_move(panel, x, y):
    debug.log("mouse_move")

    if panel.markr == -1 or panel.marks == -1:
        return

    s = min(y + panel.row - panel.y, len(panel.text))
    r = min(x + panel.col - panel.x, len(panel.text[s - 1]) + 1)

    if s < panel.marks or s == panel.marks and r < panel.markr:
        panel.r = r
        panel.s = s
        panel.u = panel.markr
        panel.v = panel.marks
    else:
        panel.r = panel.markr
        panel.s = panel.marks
        panel.u = r
        panel.v = s

    debug.log(f"selected from {panel.r},{panel.s} to {panel.u},{panel.v}")


def paste_selection(panel, key):
    debug.log("pasting:\n", "\n".join(panel.clipboard))
    if not panel.clipboard:
        return

    if len(panel.clipboard) == 1:
        panel.text[panel.row - 1] = (
            panel.text[panel.row - 1][: panel.col]
            + panel.clipboard[0]
            + panel.text[panel.row - 1][panel.col :]
        )

    panel.text = (
        panel.text[: panel.row - 1]
        + [panel.text[panel.row - 1][: panel.col] + panel.clipboard[0]]
        + panel.clipboard[1:-1]
        + [panel.clipboard[-1] + panel.text[panel.row - 1][panel.col :]]
        + panel.text[panel.row :]
    )


def save_file(panel, key):
    if panel.filename:
        with open(panel.filename, "w") as file:
            file.write("\n".join(panel.text))
            file.write("\n")
