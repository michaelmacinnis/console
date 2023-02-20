import actions
import debug


class Panel:
    def __init__(self):
        self.clear()

        self.height = 0

    def clear(self):
        self.text = [""]
        self.col = 0
        self.row = 1
        self.x = 0
        self.y = 0

    def render(self, stdscr, offset, maxy, maxx):
        debug.log("rendering", maxx, "x", maxy)
        debug.log("text cursor at", str(self.col) + "," + str(self.row))
        debug.log("screen cursor at", str(self.x) + "," + str(self.y))

        self.height = maxy

        n = adjust(len(self.text), 1, self.row)
        self.row += n
        self.y += n

        delta = self.y - self.row + 1
        if delta > 0:
            self.y -= delta

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


class CommandPanel(Panel):
    def __init__(self):
        super().__init__()

        self.complete = ""
        self.multiline = False

    def command(self):
        cmd = self.complete
        if not cmd:
            return cmd, False

        echo = self.multiline and cmd != b"\x04"

        self.complete = ""
        self.multiline = False

        return cmd, echo

    def handle(self, key):
        actions.cli.get(key, actions.command_insert_char)(self, key)

    def prepend(self, data):
        self.multiline = True
        if not data:
            return

        text = list(line.decode("utf8") for line in data.splitlines())
        self.row += len(text)
        self.y += len(text)

        text.append("")
        self.col += len(text[-1])
        self.x += len(text[-1])

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
        update = self.row == len(self.text) and self.col == len(self.text[self.row - 1])

        if not self.text[len(self.text) - 1]:
            self.text = self.text[:-1]

        self.text.extend(line.decode("utf8") for line in data.splitlines())
        self.text.append("")

        if update:
            delta = len(self.text) - self.row
            self.y += delta
            self.row += delta
            self.col = len(self.text[self.row - 1])

    def handle(self, key):
        actions.editor.get(key, actions.insert_char)(self, key)

# Helpers.

def adjust(maximum, minimum, n):
    return minimum - n if n < minimum else maximum - n if n > maximum else 0


def clip(maximum, minimum, n):
    return n + adjust(maximum, minimum, n)


