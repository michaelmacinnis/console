import curses
import os
import sys

import bindings
import debug
import widget


def size(curses_resize=True):
    cols, rows = os.get_terminal_size()

    # Tell curses about new size.
    if curses_resize:
        curses.resizeterm(rows, cols)

    return cols, rows


class Terminal:
    def __init__(self, filename=None):
        os.environ.setdefault("ESCDELAY", "50")

        self.buf = widget.EditorPanel(filename)
        self.cli = widget.CommandPanel()
        self.status = widget.StatusPanel()

        self.editing = filename is not None
        self.selection = None

    def input(self):
        eof = key_press(self)
        if eof:
            return "", eof

        cmd, echo = self.cli.command()
        if echo:
            self.buf.append(cmd)

        return cmd, eof

    def output(self, data):
        self.buf.append(data)

    def render(self):
        # After running some programs (like top) the cursor disappears.
        # Hiding the cursor ...
        curses.curs_set(0)

        rows, cols = self.stdscr.getmaxyx()

        self.stdscr.keypad(1)

        if rows > 1:
            n = min(rows - 1, 0 if self.editing else len(self.cli.text))
            rows -= n

            self.buf.render(self.stdscr, 0, rows - 1, cols)

            x, y = self.cli.cursor.get()
            if self.editing:
                x, y = self.buf.cursor.get()

            self.status.set(x, y)
            self.status.render(self.stdscr, rows - 1, 1, cols)

            sx, sy = self.buf.screen.get()
            if not self.editing:
                self.cli.render(self.stdscr, rows, n, cols)
                sx, sy = self.cli.screen.get()
                sy += rows

            debug.log("sx =", sx, "sy =", sy)
            self.stdscr.move(sy, sx)

        # ... and then showing it again, seems to fix the problem.
        curses.curs_set(2)

        self.stdscr.refresh()

    def run(self, main):
        def wrapper(stdscr, self):
            self.stdscr = stdscr

            curses.mouseinterval(0)
            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
            curses.raw()

            print("\x1b[?1003h", flush=True)

            main(self)

            print("\x1b[?1003l", flush=True)

            curses.noraw()
            curses.flushinp()

        curses.wrapper(wrapper, self)

    def type_ahead(self, type_ahead):
        self.cli.prepend(type_ahead)


# Helpers.


def key(stdscr):
    try:
        k = stdscr.getch()
        debug.log("key(number) =", k)

        return k
    except:
        return -1


def key_by_name(stdscr):
    n = key(stdscr)
    if n < 0:
        return ""

    if n == 27:
        stdscr.nodelay(True)
        n = key(stdscr)
        stdscr.nodelay(False)

        if n >= 0:
            return "ALT+" + curses.keyname(n).decode("utf8")
        else:
            return "ESC"

    return curses.keyname(n).decode("utf8")


def key_press(self):
    key = key_by_name(self.stdscr)

    debug.log("key(name) =", repr(key))
    #self.status = "key = {}".format(key)

    if key == "KEY_MOUSE":
        try:
            id, x, y, z, b = curses.getmouse()
            #self.status += " id = {} x = {} y = {} z = {} bstate = {}".format(
            #    id, x, y, z, b
            #)

            if b & 65536:  # In case curses.BUTTON4_PRESSED is not defined.
                key = "KEY_PPAGE"
            elif b & 2097152:  # curses.BUTTON5_PRESSED is not always defined.
                key = "KEY_NPAGE"
            else:
                if y < self.buf.height:
                    if self.buf.mouse(b, x, y):
                        self.cli.clear_selection()
                        self.selection = self.buf
                elif y > self.buf.height:
                    if self.cli.mouse(b, x, y - self.buf.height - 1):
                        self.buf.clear_selection()
                        self.selection = self.cli

        except curses.error:
            pass

        return

    f = bindings.selection(key)
    if f:
        if self.selection:
            f(self.selection, key)
        return False

    if key == "^E":
        self.editing = False
        return False
    elif key == "^W":
        self.editing = True
        return False
    elif key == "^Q":
        if self.editing:
            self.status.prompt = "Exit (y/n)?"
            self.status.result = lambda ans: ans.lower()[:1] == "y"

    if self.status.prompt != "":
        self.status.handle(key)
        debug.log("self.status.complete[:1]", self.status.complete[:1])
        return self.status.result(self.status.complete)
    elif self.editing:
        self.buf.handle(key)
    else:
        self.cli.handle(key)

    return False
