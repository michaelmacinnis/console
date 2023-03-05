import curses
import curses.ascii
import subprocess

import debug

clipboard = []

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
    global clipboard

    if any(n < 0 for n in (panel.r, panel.s, panel.u, panel.v)):
        return

    if panel.s == panel.v:
        clipboard = [panel.text[panel.s][panel.r : panel.u]]
    else:
        clipboard = [panel.text[panel.s][panel.r :]]

        idx = panel.s + 1
        while idx < panel.v:
            clipboard.append(panel.text[idx])
            idx += 1

        clipboard.append(panel.text[panel.v][: panel.u])

    if panel.u > len(panel.text[panel.v]):
        clipboard.append("")


def cut_selection(panel, key):
    global clipboard

    copy_selection(panel, key)

    delta = 0
    remainder = panel.text[panel.v + 1:]

    if panel.u > len(panel.text[panel.v]):
        delta = 1
        remainder = panel.text[panel.v + 2:]

        panel.text[panel.s] = panel.text[panel.s][: panel.r] + panel.text[panel.v + 1]
    else:
        panel.text[panel.s] = panel.text[panel.s][: panel.r] + panel.text[panel.v][panel.u :]

    panel.text = panel.text[: panel.s + 1] + remainder

    # TODO: Fix up cursor adjustment.
    #delta += panel.v - panel.s
    #if delta and panel.buffer.y >= panel.s:
    #    panel.buffer.y -= delta
    #    panel.screen.y -= delta

    panel.clear_selection()

    return


def cursor_down(panel, key):
    panel.buffer.y += 1
    panel.screen.y += 1


def cursor_end_of_buffer(panel, key):
    panel.buffer.y = len(panel.text) - 1
    panel.buffer.x = len(panel.text[panel.buffer.y])
    panel.screen.x = panel.buffer.x
    panel.screen.y = panel.buffer.y


def cursor_end_of_line(panel, key):
    panel.buffer.x = len(panel.text[panel.buffer.y])
    panel.screen.x = panel.buffer.x


def cursor_left(panel, key):
    panel.buffer.x -= 1
    panel.screen.x -= 1


def cursor_next_page(panel, key):
    panel.buffer.y = min(len(panel.text) - 1, panel.buffer.y + panel.height)
    if panel.buffer.y == len(panel.text) - 1:
        panel.screen.y = panel.height - 1


def cursor_prev_page(panel, key):
    panel.buffer.y = max(0, panel.buffer.y - panel.height)
    if not panel.buffer.y:
        panel.screen.y = 0


def cursor_right(panel, key):
    panel.buffer.x += 1
    panel.screen.x += 1


def cursor_start_of_buffer(panel, key):
    panel.buffer.x = 0
    panel.buffer.y = 0
    panel.screen.x = 0
    panel.screen.y = 0


def cursor_start_of_line(panel, key):
    panel.buffer.x = 0
    panel.screen.x = 0


def cursor_up(panel, key):
    panel.buffer.y -= 1
    panel.screen.y -= 1


def delete_char(panel, key):
    if not panel.buffer.x:
        # At the beginning of a line.
        prev = panel.buffer.y - 1
        if prev > 0:
            # There are previous lines.
            panel.buffer.x = len(panel.text[prev])
            panel.text[prev] += panel.text[panel.buffer.y]
            panel.text = panel.text[:panel.buffer.y] + panel.text[panel.buffer.y + 1:]
            panel.buffer.y = prev
            panel.screen.x = panel.buffer.x
            panel.screen.y -= 1
        return

    line = panel.text[panel.buffer.y]
    panel.text[panel.buffer.y] = line[: panel.buffer.x - 1] + line[panel.buffer.x :]
    panel.buffer.x -= 1
    panel.screen.x -= 1


def insert_char(panel, key):
    if key == "^J":
        panel.text = (
            panel.text[: panel.buffer.y]
            + [panel.text[panel.buffer.y][: panel.buffer.x]]
            + [panel.text[panel.buffer.y][panel.buffer.x :]]
            + panel.text[panel.buffer.y + 1:]
        )
        panel.buffer.x = 0
        panel.buffer.y += 1
        panel.screen.x = 0
        panel.screen.y += 1
        return

    if len(key) == 1 and curses.ascii.isprint(ord(key)):
        line = panel.text[panel.buffer.y]
        panel.text[panel.buffer.y] = line[: panel.buffer.x] + key + line[panel.buffer.x :]
        panel.buffer.x += 1
        panel.screen.x += 1


def mouse_left_pressed(panel, x, y):
    debug.log("mouse_left_pressed")

    panel.marks = min(y + panel.buffer.y - panel.screen.y, len(panel.text) - 1)
    panel.markr = min(x + panel.buffer.x - panel.screen.x, len(panel.text[panel.marks]) + 1)

    panel.button.x = x
    panel.button.y = y

    panel.r = -1
    panel.s = -1
    panel.u = -1
    panel.v = -1


def mouse_left_released(panel, x, y):
    debug.log("mouse_left_released")

    if panel.button.x == x and panel.button.y == y:
        panel.buffer.x += x - panel.screen.x
        panel.buffer.y += y - panel.screen.y
        panel.screen.x = x
        panel.screen.y = y

    panel.button.x = -1
    panel.button.y = -1

    if panel.markr == -1 or panel.marks == -1:
        return

    mouse_move(panel, x, y)

    panel.markr = -1
    panel.marks = -1

    return panel


def mouse_move(panel, x, y):
    debug.log("mouse_move")

    if panel.markr == -1 or panel.marks == -1:
        return

    s = min(y + panel.buffer.y - panel.screen.y, len(panel.text) - 1)
    r = min(x + panel.buffer.x - panel.screen.x, len(panel.text[s]) + 1)

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
    if not clipboard:
        return

    if len(clipboard) == 1:
        debug.log(f"PASTING: {repr(clipboard[0])}")
        panel.text[panel.buffer.y] = (
            panel.text[panel.buffer.y][: panel.buffer.x]
            + clipboard[0]
            + panel.text[panel.buffer.y][panel.buffer.x :]
        )
        return

    panel.text = (
        panel.text[: panel.buffer.y]
        + [panel.text[panel.buffer.y][: panel.buffer.x] + clipboard[0]]
        + clipboard[1:-1]
        + [clipboard[-1] + panel.text[panel.buffer.y][panel.buffer.x :]]
        + panel.text[panel.buffer.y + 1:]
    )


def save_file(panel, key):
    if panel.filename:
        with open(panel.filename, "w") as file:
            file.write("\n".join(panel.text))
            file.write("\n")
