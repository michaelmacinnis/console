import curses
import os
import sys

import debug
import panel


def getstr(op):
    return curses.tigetstr(op)


def keyname(n):
    if n < 0:
        return ""
    return curses.keyname(n).decode("utf8")


def resize(rows, cols):
    curses.resizeterm(rows, cols)


class Terminal:
    def __init__(self, filename=None):
        os.environ.setdefault("ESCDELAY", "50")

        self.buffer = panel.Panel(filename=filename)
        self.command = panel.Panel(command=True)
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

    def append(self, data):
        self.buffer.append(data)

    def cmd(self):
        return self.command.cmd()

    def handle(self, key):
        debug.log(repr(key))

        if key == "KEY_MOUSE":
            id, x, y, z, bstate = curses.getmouse()
            self.status += " id = {} x = {} y = {} z = {} bstate = {}".format(
                id, x, y, z, bstate
            )

            # rows, _ = self.stdscr.getmaxyx()
            # self.editing = y < rows - 2

            return True

        if key == "^E":
            self.editing = False
            return True
        elif key == "^W":
            self.editing = True
            return True
        elif key == "^Q":
            if self.editing:
                return False

        if self.editing:
            self.buffer.handle(key)
        else:
            self.command.handle(key)

        return True

    def _key(self):
        try:
            k = self.stdscr.getch()
            debug.log("KEY =", k)

            return k
        except:
            return -1

    def key(self):
        k = self._key()
        if k == curses.KEY_RESIZE:
            k = "KEY_RESIZE"
        elif k == 27:
            self.stdscr.nodelay(True)

            n = self._key()
            if n >= 0:
                k = "ALT+" + keyname(n)
            else:
                k = "ESC"

            self.stdscr.nodelay(False)
        else:
            k = keyname(k)

        self.status = "key = {}".format(k)

        return k

    def render(self):
        # After running some programs (like top) the cursor disappears.
        # Hiding the cursor ...
        curses.curs_set(0)

        rows, cols = self.stdscr.getmaxyx()

        self.stdscr.keypad(1)
        self.stdscr.clear()

        if rows > 1:
            n = min(rows - 1, 0 if self.editing else len(self.command.text))
            rows -= n

            self.stdscr.addstr(rows - 1, 0, self.status[:cols], curses.A_REVERSE)
            self.stdscr.chgat(-1, curses.A_REVERSE)

            self.buffer.render(self.stdscr, 0, rows - 1, cols)

            if not self.editing:
                self.command.render(self.stdscr, rows, n, cols)

        # ... and then showing it again, seems to fix the problem.
        curses.curs_set(2)

        self.stdscr.refresh()
