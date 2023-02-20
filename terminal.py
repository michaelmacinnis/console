import curses
import os
import sys

import debug
import widget


def get_key(stdscr):
    try:
        k = stdscr.getch()
        debug.log("KEY =", k)

        return k
    except:
        return -1


def get_key_by_name(stdscr):
    n = get_key(stdscr)
    if n < 0:
        return ""

    if n == curses.KEY_RESIZE:
        return "KEY_RESIZE"

    if n == 27:
        stdscr.nodelay(True)
        n = get_key(stdscr)
        stdscr.nodelay(False)

        if n >= 0:
            return "ALT+" + curses.keyname(n).decode("utf8")
        else:
            return "ESC"

    return curses.keyname(n).decode("utf8")


def get_size():
    cols, rows = os.get_terminal_size()

    # Tell curses about new size.
    curses.resizeterm(rows, cols)

    return cols, rows


class Terminal:
    def __init__(self, filename=None):
        os.environ.setdefault("ESCDELAY", "50")

        self.buf = widget.EditorPanel(filename)
        self.cli = widget.CommandPanel()

        self.editing = filename is not None
        self.status = ""

    def Run(self, main):
        def wrapper(stdscr, self):
            self.stdscr = stdscr

            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
            curses.raw()

            main(self)

            curses.noraw()
            curses.flushinp()

        curses.wrapper(wrapper, self)

    def handle(self, key):
        debug.log(repr(key))
        self.status = "key = {}".format(key)

        if key == "KEY_MOUSE":
            id, x, y, z, bstate = curses.getmouse()
            self.status += " id = {} x = {} y = {} z = {} bstate = {}".format(
                id, x, y, z, bstate
            )

            return False

        if key == "^E":
            self.editing = False
            return False
        elif key == "^W":
            self.editing = True
            return False
        elif key == "^Q":
            if self.editing:
                return True

        if self.editing:
            self.buf.handle(key)
        else:
            self.cli.handle(key)

        return False

    def input(self):
        cmd = ""
        eof = self.handle(get_key_by_name(self.stdscr))
        if not eof:
            cmd = self.cli.command()
            if cmd and cmd != b"\x04":
                if self.cli.multiline:
                    self.buf.append(cmd)
                    self.cli.multiline = False

        return cmd, eof

    def multiline(self, type_ahead):
        debug.log("MULTI LINE")
        self.cli.multiline = True

        if type_ahead:
            debug.log("type-ahead", type_ahead)
            self.cli.prepend(type_ahead)

    def output(self, data):
        self.buf.append(data)

    def render(self):
        # After running some programs (like top) the cursor disappears.
        # Hiding the cursor ...
        curses.curs_set(0)

        rows, cols = self.stdscr.getmaxyx()

        self.stdscr.keypad(1)
        self.stdscr.clear()

        if rows > 1:
            n = min(rows - 1, 0 if self.editing else len(self.cli.text))
            rows -= n

            self.stdscr.addstr(rows - 1, 0, self.status[:cols], curses.A_REVERSE)
            self.stdscr.chgat(-1, curses.A_REVERSE)

            self.buf.render(self.stdscr, 0, rows - 1, cols)

            if not self.editing:
                self.cli.render(self.stdscr, rows, n, cols)

        # ... and then showing it again, seems to fix the problem.
        curses.curs_set(2)

        self.stdscr.refresh()
