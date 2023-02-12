import debug

from actions import bindings, insert_char


def adjust(maximum, minimum, n):
    return minimum - n if n < minimum else maximum - n if n > maximum else 0


def clip(maximum, minimum, n):
    return n + adjust(maximum, minimum, n)


# TODO: Make this something more efficient.
# Memory mapped file or ropes or something.
class Panel:
    def __init__(self, command=False, filename=None):
        self.clear()

        self._cmd = ""
        self.command = command
        self.filename = filename
        self.height = 0
        self.multiline = False

        if filename:
            with open(filename, "r") as file:
                self.text = [line.rstrip("\n\r") for line in file]

    def append(self, data):
        update = self.row == len(self.text) and self.col == len(
            self.text[self.row - 1]
        )

        if not self.text[len(self.text) - 1]:
            self.text = self.text[:-1]

        self.text.extend(line.decode("utf8") for line in data.splitlines())
        self.text.append("")

        if update:
            delta = len(self.text) - self.row
            self.y += delta
            self.row += delta
            self.col = len(self.text[self.row - 1])

    def clear(self):
        self.text = [""]
        self.col = 0
        self.row = 1
        self.x = 0
        self.y = 0

    def close(self):
        pass

    def cmd(self):
        c = self._cmd
        self._cmd = ""

        return c

    def handle(self, key):
        action = bindings.get(key, insert_char)

        action(self, key)

        # self.print()

    def print(self):
        debug.log(self.text)

    def render(self, stdscr, offset, maxy, maxx):
        debug.log("rendering", maxx, "x", maxy)
        debug.log("text cursor at", str(self.col) + "," + str(self.row))
        debug.log("screen cursor at", str(self.x) + "," + str(self.y))

        self.height = maxy

        n = adjust(len(self.text), 1, self.row)
        self.row += n
        self.y += n

        # debug.log("text cursor at", str(self.col) + "," + str(self.row))

        n = adjust(len(self.text[self.row - 1]), 0, self.col)
        self.col += n
        self.x += n

        # debug.log(
        #    "adjusted text cursor",
        #    str(self.col) + "," + str(self.row),
        # )
        # debug.log("adjusted screen cursor", str(self.x) + "," + str(self.y))

        self.x = clip(maxx - 1, 0, self.x)
        self.y = clip(maxy - 1, 0, self.y)

        # debug.log("clipped screen cursor", str(self.x) + "," + str(self.y))

        col = max(1, self.col - self.x + 1)
        row = max(1, self.row - self.y)

        last = self.y + offset
        # debug.log("adjusted", str(col) + "," + str(row))

        for line in self.text[row - 1 :][:maxy]:
            # debug.log("line", offset, row - 1, line)

            stdscr.addstr(offset, 0, line[col - 1 :][: maxx - 1])
            offset += 1

        stdscr.move(last, self.x)

        # debug.log()
