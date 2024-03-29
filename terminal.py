import curses
import fcntl
import os
import struct
import sys
import tty

import bindings
import debug
import responses
import widget

previous_rows = 0
previous_cols = 0


def resize(fd):
    global previous_cols
    global previous_rows

    zero = struct.pack("HHHH", 0, 0, 0, 0)

    t = fcntl.ioctl(0, tty.TIOCGWINSZ, zero)

    rows, cols, x, y = struct.unpack("HHHH", t)

    w = struct.pack("HHHH", rows, cols, x, y)
    fcntl.ioctl(fd, tty.TIOCSWINSZ, w)

    if cols == previous_cols and rows == previous_rows:
        return

    previous_cols = cols
    previous_rows = rows

    debug.log("terminal size changed to", cols, rows, x, y)

    curses.resizeterm(rows, cols)

    sys.stdout.write(f"\x1b[8;{rows};{cols}t")
    sys.stdout.flush()


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
            self.status.running = cmd.splitlines()[0].decode("utf8")

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
        self.status.running = "(bash)"


# Helpers.


def key(stdscr):
    try:
        k = stdscr.getch()

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
    if key == "KEY_MOUSE":
        try:
            id, x, y, z, b = curses.getmouse()
            # self.status += " id = {} x = {} y = {} z = {} bstate = {}".format(
            #    id, x, y, z, b
            # )

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

        return False

    f = bindings.selection(key)
    if f:
        if self.selection:
            f(self.selection, key)
        return False

    if key == "^E":
        self.editing = False
        return False
    elif key == "^F":
        if self.status.prompt != "":
            return False

        self.status.prompt = "Forward search for?"
        self.status.response = responses.forward_search
        return False
    elif key == "^L":
        if self.status.prompt != "":
            return False

        self.status.prompt = "Line number?"
        self.status.response = responses.line_number
        return False
    elif key == "^Q":
        if self.editing:
            self.status.prompt = "Exit (y/n)?"
            self.status.response = responses.exit
        elif len(self.cli.text) == 1 and not len(self.cli.text[0]):
            self.status.prompt = "Send EOF (y/n)?"
            self.status.response = responses.send_eof
        return False
    elif key == "^R":
        if self.status.prompt != "":
            return False

        self.status.prompt = "Reverse search for?"
        self.status.response = responses.reverse_search
        return False
    elif key == "^W":
        self.editing = True
        return False

    if self.status.prompt != "":
        self.status.handle(key)
        return self.status.response(self)
    elif self.editing:
        self.buf.handle(key)
    else:
        self.cli.handle(key)

    return False
