import curses
import enum

import actions
import bindings
import buffer
import debug
import point

class StatusPanel(point.Point):
    def __init__(self):
        super().__init__()

        self.clear()
        self.complete = ""
        self.running = ""

    def clear(self):
        # The cursor and selection points uses buffer co-ordinates.
        self.cursor = point.Point(0, 0)
        self.screen = point.Point(0, 0)

        self.prompt = ""

        self.text = buffer.Buffer([""])

    def command(self):
        cmd = self.complete
        self.complete = ""
        return cmd

    def handle(self, key):
        bindings.prompt(key)(self, key)

    def render(self, stdscr, offset, height, width):
        if self.prompt == "":
            loc = f"{self.y + 1},{self.x} "
            run = f" {self.running}"

            if len(loc) + len(run) > width:
                # Not enough room. Display nothing.
                loc = ""
                run = ""

            spacer = " " * (width - len(loc) - len(run))
            addstr(stdscr, offset, 0, run + spacer + loc, curses.A_REVERSE)

        else:
            prompt = f"{self.prompt} {self.text[0]}"[:width]
            if len(prompt) > width:
                prompt = "?"

            spacer = " " * (width - len(prompt))
            addstr(stdscr, offset, 0, prompt + spacer, curses.A_REVERSE)

class Panel:
    def __init__(self):
        self.clear()

        self.height = 0

    def clear(self):
        # The cursor and selection points uses buffer co-ordinates.
        self.cursor = point.Point(0, 0)

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

    def goto_line(self, y, x=0):
        if len(self.text) <= y:
            return

        deltax = x - self.cursor.x
        deltay = y - self.cursor.y

        self.cursor.x += deltax
        self.cursor.y += deltay

        self.screen.x += deltax
        self.screen.y += deltay

    def goto_text(self, text, by=1):
        y = self.cursor.y

        line = self.text[y]
        start = 0
        end = len(line)

        if by > 0:
            start = self.cursor.x
        else:
            end = self.cursor.x

        idx = -1
        line = line[start:end]
        while True:
            if by > 0:
                idx = line.find(text)
            else:
                idx = line.rfind(text)

            if idx != -1:
                break

            y += by
            if y < 0 or y > len(self.text):
                break

            start = 0
            line = self.text[y]

        if idx != -1:
            self.goto_line(y, start + idx)


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
        # Save height.
        self.height = height

        n = point.correction(self.cursor.y, 0, len(self.text) - 1)
        self.cursor.y += n
        self.screen.y += n

        n = point.correction(self.cursor.x, 0, len(self.text[self.cursor.y]))
        self.cursor.x += n
        self.screen.x += n

        # Largest y may be less than height - 1 if the buffer is smaller.
        self.screen.clip(width - 1, min(height - 1, self.cursor.y))

        col = max(0, self.cursor.x - self.screen.x)
        row = max(0, self.cursor.y - self.screen.y)

        for n in range(height):
            for c in self.text.chunks(width, row + n, col, self.p0, self.p1):
                attr = curses.A_REVERSE if c.sel else curses.A_NORMAL
                addstr(stdscr, offset + n, c.col, c.str, attr)

        stdscr.move(self.screen.y + offset, self.screen.x)


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
        self.cursor.move(0, dy)
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
        update = self.cursor.y == len(self.text) - 1 and self.cursor.x == len(
            self.text[self.cursor.y]
        )

        self.text.append(data)

        if update:
            delta = len(self.text) - 1 - self.cursor.y
            debug.log(
                "delta", delta, "row", self.cursor.y, "len(self.txt)", len(self.text)
            )
            self.screen.y += delta
            self.cursor.y += delta
            self.cursor.x = len(self.text[self.cursor.y])

    def handle(self, key):
        bindings.editor(key)(self, key)


def addstr(stdscr, *args):
    try:
        stdscr.addstr(*args)
    except curses.error:
        # Curses throws an exception when printing to the last row and column.
        pass
