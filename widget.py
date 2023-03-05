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
        self.buffer = point.Point(0, 0) # TODO: Rename to cursor.

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

        last = self.screen.y + offset
        # debug.log("adjusted", str(col) + "," + str(row))

        idx = row
        n = 0
        for line in self.text[row:][:height]:
            span = width
            n += 1

            # debug.log("line", offset, row, line)

            # The line is not within the selected region.
            if idx < self.p0.y or idx > self.p1.y:
                stdscr.attron(curses.A_NORMAL)
                stdscr.addstr(offset, 0, line[col:][:span])
                stdscr.hline(b" ", width)
                stdscr.attroff(curses.A_NORMAL)

                offset += 1
                idx += 1

                continue

            # The line is completely with the selected region.
            if idx > self.p0.y and idx < self.p1.y:
                stdscr.attron(curses.A_REVERSE)
                display = line[col:][:span]
                stdscr.addstr(offset, 0, display)
                try:
                    stdscr.addstr(offset, len(display), b" ")
                except:
                    pass
                stdscr.attroff(curses.A_REVERSE)
                stdscr.hline(b" ", width)

                offset += 1
                idx += 1

                continue

            shift = 0

            # The line is at the start of the selected region.
            if idx == self.p0.y:
                # Display the unselected part of the line (if any).
                if self.p0.x > col + shift:
                    unselected = line[col + shift : self.p0.x][:span]
                    stdscr.addstr(offset, shift, unselected, curses.A_NORMAL)

                    span -= len(unselected)
                    shift += len(unselected)

                if span > 0 and idx != self.p1.y:
                    selected = line[col + shift :][:span]
                    stdscr.addstr(offset, shift, selected, curses.A_REVERSE)

                    span -= len(selected)
                    shift += len(selected)

                    stdscr.addstr(offset, shift, b" ", curses.A_REVERSE)

            # The line is at the end of the selected region.
            if idx == self.p1.y:
                if span > 0 and self.p1.x > col + shift:
                    selected = line[col + shift : self.p1.x][:span]
                    stdscr.addstr(offset, shift, selected, curses.A_REVERSE)

                    span -= len(selected)
                    shift += len(selected)

                if span > 0:
                    if self.p1.x > len(line):
                        stdscr.addstr(offset, shift, b" ", curses.A_REVERSE)
                    else:
                        unselected = line[self.p1.x :][:span]
                        stdscr.addstr(offset, shift, unselected, curses.A_NORMAL)

            stdscr.hline(b" ", width - 1)
            idx += 1
            offset += 1

        while n < height:
            stdscr.move(offset, 0)
            stdscr.hline(b" ", width - 1)
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

