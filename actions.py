import curses
import curses.ascii
import subprocess

import debug

clipboard = None

# Actions.
def command_insert_char(widget, key):
    if key == "^J":
        text = "\n".join(widget.text + [""]).encode("utf8")
        debug.log(text)

        if widget.multiline:
            r = subprocess.run(["sh", "-n"], input=text, capture_output=True)
            debug.log(r)
            if r.stderr:
                text = None
        if text:
            widget.complete = text
            widget.clear()
            return

    if key == "^Q":
        if len(widget.text) == 1 and not len(widget.text[0]):
            widget.complete = b"\x04"
            widget.clear()
            return

    insert_char(widget, key)


def copy_selection(widget, key):
    global clipboard

    if not all((widget.p0.valid, widget.p1.valid)):
        return

    clipboard = widget.text.select(widget.p0, widget.p1)


def cut_selection(widget, key):
    if not all((widget.p0.valid, widget.p1.valid)):
        return

    copy_selection(widget, key)

    widget.text.remove(widget.p0, widget.p1)

    widget.clear_selection()

    return


def cursor_down(widget, key):
    widget.buffer.y += 1
    widget.screen.y += 1


def cursor_end_of_buffer(widget, key):
    widget.buffer.y = len(widget.text) - 1
    widget.buffer.x = len(widget.text[widget.buffer.y])
    widget.screen.x = widget.buffer.x
    widget.screen.y = widget.buffer.y


def cursor_end_of_line(widget, key):
    widget.buffer.x = len(widget.text[widget.buffer.y])
    widget.screen.x = widget.buffer.x


def cursor_left(widget, key):
    widget.buffer.x -= 1
    widget.screen.x -= 1


def cursor_next_page(widget, key):
    widget.buffer.y = min(len(widget.text) - 1, widget.buffer.y + widget.height)
    if widget.buffer.y == len(widget.text) - 1:
        widget.screen.y = widget.height - 1


def cursor_prev_page(widget, key):
    widget.buffer.y = max(0, widget.buffer.y - widget.height)
    if not widget.buffer.y:
        widget.screen.y = 0


def cursor_right(widget, key):
    widget.buffer.x += 1
    widget.screen.x += 1


def cursor_start_of_buffer(widget, key):
    widget.buffer.x = 0
    widget.buffer.y = 0
    widget.screen.x = 0
    widget.screen.y = 0


def cursor_start_of_line(widget, key):
    widget.buffer.x = 0
    widget.screen.x = 0


def cursor_up(widget, key):
    widget.buffer.y -= 1
    widget.screen.y -= 1


def delete_char(widget, key):
    if not widget.buffer.x:
        # At the beginning of a line.
        prev = widget.buffer.y - 1
        if prev > 0:
            # There are previous lines.
            widget.buffer.x = len(widget.text[prev])
            widget.text[prev] += widget.text[widget.buffer.y]
            widget.text = widget.text[:widget.buffer.y] + widget.text[widget.buffer.y + 1:]
            widget.buffer.y = prev
            widget.screen.x = widget.buffer.x
            widget.screen.y -= 1
        return

    line = widget.text[widget.buffer.y]
    widget.text[widget.buffer.y] = line[: widget.buffer.x - 1] + line[widget.buffer.x :]
    widget.buffer.x -= 1
    widget.screen.x -= 1


def insert_char(widget, key):
    if key == "^J":
        widget.text = (
            widget.text[: widget.buffer.y]
            + [widget.text[widget.buffer.y][: widget.buffer.x]]
            + [widget.text[widget.buffer.y][widget.buffer.x :]]
            + widget.text[widget.buffer.y + 1:]
        )
        widget.buffer.x = 0
        widget.buffer.y += 1
        widget.screen.x = 0
        widget.screen.y += 1
        return

    if len(key) == 1 and curses.ascii.isprint(ord(key)):
        line = widget.text[widget.buffer.y]
        widget.text[widget.buffer.y] = line[: widget.buffer.x] + key + line[widget.buffer.x :]
        widget.buffer.x += 1
        widget.screen.x += 1


def mouse_left_pressed(widget, x, y):
    debug.log("mouse_left_pressed")

    widget.s.y = min(y + widget.buffer.y - widget.screen.y, len(widget.text) - 1)
    widget.s.x = min(x + widget.buffer.x - widget.screen.x, len(widget.text[widget.s.y]) + 1)

    widget.button.x = x
    widget.button.y = y

    widget.p0.x = -1
    widget.p0.y = -1
    widget.p1.x = -1
    widget.p1.y = -1


def mouse_left_released(widget, x, y):
    debug.log("mouse_left_released")

    if widget.button.equal(x, y):
        widget.buffer.x += x - widget.screen.x
        widget.buffer.y += y - widget.screen.y
        widget.screen.x = x
        widget.screen.y = y

    widget.button.x = -1
    widget.button.y = -1

    if widget.s.x == -1 or widget.s.y == -1:
        return

    mouse_move(widget, x, y)

    widget.s.x = -1
    widget.s.y = -1

    return widget


def mouse_move(widget, x, y):
    debug.log("mouse_move")

    if widget.s.x == -1 or widget.s.y == -1:
        return

    s = min(y + widget.buffer.y - widget.screen.y, len(widget.text) - 1)
    r = min(x + widget.buffer.x - widget.screen.x, len(widget.text[s]) + 1)

    if s < widget.s.y or s == widget.s.y and r < widget.s.x:
        widget.p0.x = r
        widget.p0.y = s
        widget.p1.x = widget.s.x
        widget.p1.y = widget.s.y
    else:
        widget.p0.x = widget.s.x
        widget.p0.y = widget.s.y
        widget.p1.x = r
        widget.p1.y = s

    debug.log(f"selected from {widget.p0.x},{widget.p0.y} to {widget.p1.x},{widget.p1.y}")


def paste_selection(widget, key):
    if not clipboard:
        return

    debug.log(f"PASTING: {repr(clipboard)}")

    widget.text.insert(widget.buffer, clipboard)


def save_file(widget, key):
    if widget.filename:
        with open(widget.filename, "w") as file:
            file.write("\n".join(widget.text))
            file.write("\n")
