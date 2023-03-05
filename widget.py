import curses

import actions
import bindings
import debug
import point


class Panel:
    def __init__(self):
        self.clear()

        self.height = 0

    def clear(self):
        self.buffer = point.Point(0, 0)
        self.button = point.Point(0, 0)
        self.screen = point.Point(0, 0)

        self.clipboard = []
        self.text = [""]

        self.col = 0
        self.row = 0

        self.clear_selection()

    def clear_selection(self):
        self.r = -1
        self.s = -1
        self.u = -1
        self.v = -1

        self.markr = -1
        self.marks = -1

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
        # debug.log("text cursor at", str(self.col) + "," + str(self.row))
        # debug.log("screen cursor at", str(self.screen.x) + "," + str(self.screen.y))

        # Save offset and height.
        self.offset = offset
        self.height = height

        n = adjust(len(self.text) - 1, 0, self.row)
        self.row += n
        self.screen.y += n

        delta = self.screen.y - self.row
        if delta > 0:
            self.screen.y -= delta

        # debug.log("text cursor at", str(self.col) + "," + str(self.row))

        n = adjust(len(self.text[self.row]), 0, self.col)
        self.col += n
        self.screen.x += n

        # debug.log(
        #    "adjusted text cursor",
        #    str(self.col) + "," + str(self.row),
        # )
        # debug.log("adjusted screen cursor", str(self.screen.x) + "," + str(self.screen.y))

        self.screen.x = clip(width - 1, 0, self.screen.x)
        self.screen.y = clip(height - 1, 0, self.screen.y)

        # debug.log("clipped screen cursor", str(self.screen.x) + "," + str(self.screen.y))

        col = max(0, self.col - self.screen.x)
        row = max(0, self.row - self.screen.y)

        last = self.screen.y + offset
        # debug.log("adjusted", str(col) + "," + str(row))

        idx = row
        n = 0
        for line in self.text[row:][:height]:
            span = width - 1
            n += 1

            # debug.log("line", offset, row, line)

            # The line is not within the selected region.
            if idx < self.s or idx > self.v:
                stdscr.attron(curses.A_NORMAL)
                stdscr.addstr(offset, 0, line[col:][:span])
                stdscr.hline(b' ', width - 1)
                stdscr.attroff(curses.A_NORMAL)
                stdscr.hline(b' ', width - 1)
                offset += 1
                idx += 1
                continue

            # The line is completely with the selected region.
            if idx > self.s and idx < self.v:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(offset, 0, line[col:][:span])
                stdscr.hline(b' ', 1)
                stdscr.attroff(curses.A_REVERSE)
                stdscr.hline(b' ', width - 1)
                offset += 1
                idx += 1
                continue

            shift = 0

            # The line is at the start of the selected region.
            if idx == self.s:
                # Display the unselected part of the line (if any).
                if self.r > col + shift:
                    unselected = line[col + shift : self.r][:span]
                    stdscr.addstr(offset, shift, unselected, curses.A_NORMAL)

                    span -= len(unselected)
                    shift += len(unselected)

                if span > 0 and idx != self.v:
                    selected = line[col + shift :][:span]
                    stdscr.addstr(offset, shift, selected, curses.A_REVERSE)

                    span -= len(selected)
                    shift += len(selected)

                    stdscr.addstr(offset, shift, b' ', curses.A_REVERSE)

            # The line is at the end of the selected region.
            if idx == self.v:
                if span > 0 and self.u > col + shift:
                    selected = line[col + shift : self.u][:span]
                    stdscr.addstr(offset, shift, selected, curses.A_REVERSE)

                    span -= len(selected)
                    shift += len(selected)

                if span > 0:
                    if self.u > len(line):
                        stdscr.addstr(offset, shift, b' ', curses.A_REVERSE)
                    else:
                        unselected = line[self.u :][:span]
                        stdscr.addstr(offset, shift, unselected, curses.A_NORMAL)

            stdscr.hline(b' ', width - 1)
            idx += 1
            offset += 1

        while n < height:
            stdscr.move(offset, 0)
            stdscr.hline(b' ', width - 1)
            n += 1
            offset += 1

        stdscr.move(last, self.screen.x)

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
        self.row += len(text)
        self.screen.y += len(text)

        text.append("")
        self.col += len(text[-1])
        self.screen.x += len(text[-1])

        text[-1] += self.text[0]
        text.extend(self.text[1:])

        self.text = text


class EditorPanel(Panel):
    def __init__(self, filename=None):
        super().__init__()

        self.filename = filename
        if filename:
            with open(filename, "r") as file:
                self.text = [line.rstrip("\n\r") for line in file]

    def append(self, data):
        update = self.row == len(self.text) - 1 and self.col == len(self.text[self.row ])

        if not self.text[len(self.text) - 1]:
            self.text = self.text[:-1]

        self.text.extend(line.decode("utf8") for line in data.splitlines())
        self.text.append("")

        if update:
            delta = len(self.text) - 1 - self.row
            debug.log("delta", delta, "row", self.row, "len(self.txt)", len(self.text))
            self.screen.y += delta
            self.row += delta
            self.col = len(self.text[self.row])

    def handle(self, key):
        bindings.editor(key)(self, key)


# Helpers.


def adjust(maximum, minimum, n):
    return minimum - n if n < minimum else maximum - n if n > maximum else 0


def clip(maximum, minimum, n):
    return n + adjust(maximum, minimum, n)
