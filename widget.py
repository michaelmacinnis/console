import curses

import actions
import bindings
import buffer
import debug
import point


class Panel:
    def __init__(self):
        self.clear()

        self.height = 0

    def clear(self):
        # The buffer and selection points uses buffer co-ordinates.
        self.buffer = point.Point(0, 0)  # TODO: Rename to cursor.

        self.p0 = point.Point()
        self.p1 = point.Point()
        self.s = point.Point()

        # The button and screen points use display co-ordinates.
        self.button = point.Point(0, 0)
        self.screen = point.Point(0, 0)

        self.text = buffer.Buffer([""])

    def clear_selection(self):
        # The beginning, ending, and selection points use buffer co-ordinates.
        self.p0.clear()
        self.p1.clear()
        self.s.clear()

    def mouse(self, b, x, y):
        event = 0
        for mask in (curses.BUTTON1_PRESSED, curses.BUTTON1_RELEASED):
            if b & mask:
                event = mask
                break

        return {
            0: actions.mouse_move,
            curses.BUTTON1_PRESSED: actions.mouse_left_pressed,
            curses.BUTTON1_RELEASED: actions.mouse_left_released,
        }.get(event, lambda p, x, y: None)(self, x, y)

    def render(self, stdscr, offset, height, width):
        # debug.log("rendering", width, "x", height)
        # debug.log("text cursor at", str(self.buffer.x) + "," + str(self.buffer.y))
        # debug.log("screen cursor at", str(self.screen.x) + "," + str(self.screen.y))

        # Save offset and height.
        self.offset = offset
        self.height = height

        n = point.correction(self.buffer.y, 0, len(self.text) - 1)
        self.buffer.y += n
        self.screen.y += n

        n = point.correction(self.buffer.x, 0, len(self.text[self.buffer.y]))
        self.buffer.x += n
        self.screen.x += n

        self.screen.clip(width - 1, min(height - 1, self.buffer.y))

        col = max(0, self.buffer.x - self.screen.x)
        row = max(0, self.buffer.y - self.screen.y)

        for n in range(height):
            for d in self.text.render(width, row + n, col, self.p0, self.p1):
                addstr(stdscr, offset + n, d.col, d.str, d.attr)

        stdscr.move(self.screen.y + offset, self.screen.x)

        # debug.log()


class CommandPanel(Panel):
    def __init__(self):
        super().__init__()

        self.complete = ""
        self.multiline = False

    def command(self):
        cmd = self.complete
        if not cmd:
            return cmd, False

        echo = self.multiline and cmd not in (b"\x04", b"\n")

        self.complete = ""
        self.multiline = False

        return cmd, echo

    def handle(self, key):
        bindings.cli(key)(self, key)

    def prepend(self, data):
        self.multiline = True
        if not data:
            return

        text = list(line.decode("utf8") for line in data.splitlines())

        dy = len(text)
        self.buffer.move(0, dy)
        self.screen.move(0, dy)

        text.extend(self.text)

        self.text = text


class EditorPanel(Panel):
    def __init__(self, filename=None):
        super().__init__()

        self.filename = filename
        if filename:
            with open(filename, "r") as file:
                self.text = buffer.Buffer([line.rstrip("\n\r") for line in file])

    def append(self, data):
        update = self.buffer.y == len(self.text) - 1 and self.buffer.x == len(
            self.text[self.buffer.y]
        )

        self.text.append(data)

        if update:
            delta = len(self.text) - 1 - self.buffer.y
            debug.log(
                "delta", delta, "row", self.buffer.y, "len(self.txt)", len(self.text)
            )
            self.screen.y += delta
            self.buffer.y += delta
            self.buffer.x = len(self.text[self.buffer.y])

    def handle(self, key):
        bindings.editor(key)(self, key)


def addstr(stdscr, *args):
    try:
        stdscr.addstr(*args)
    except curses.error:
        pass
