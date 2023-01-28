import curses
import os
import sys

import buffer

def getstr(op):
    return curses.tigetstr(op)

def keyname(n):
    if n < 0:
        return ''
    return curses.keyname(n).decode('utf-8')

class Terminal:
    def __init__(self, filename=None):
        os.environ.setdefault('ESCDELAY', '50')

        self.buffer = buffer.Buffer(filename=filename)
        self.command = buffer.Buffer()
        self.editing = filename is not None
        self.status = ''

    def Run(self, cycle):
        def main(stdscr, self):
            self.stdscr = stdscr

            curses.curs_set(2)
            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
            curses.raw()

            #print(dir(curses), file=sys.stderr)
            #print(dir(self.stdscr), file=sys.stderr)

            #import ctypes
            #dll = ctypes.CDLL('/lib/x86_64-linux-gnu/libncursesw.so.6')

            # Make sure focus in/out are defined.
            #dll.define_key(b'\x1b[I', 1001)
            #dll.define_key(b'\x1b[O', 1002)

            #print(curses.has_key(1001), file=sys.stderr)
            #print(curses.has_key(1002), file=sys.stderr)
            #print('focus in defined', dll.key_defined(b'\x1b[I'), file=sys.stderr)
            #print('focus out defined', dll.key_defined(b'\x1b[O'), file=sys.stderr)

            while cycle():
                pass

            curses.noraw()
            curses.flushinp()

        curses.wrapper(main, self)

    def handle(self, key):
        print(repr(key), file=sys.stderr)

        if key == 'KEY_MOUSE':
            id, x, y, z, bstate = curses.getmouse()
            self.status += ' id = {} x = {} y = {} z = {} bstate = {}'.format(
                id, x, y, z, bstate
            )

            rows, _ = self.stdscr.getmaxyx()
            self.editing = y < rows - 2

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
            self.status = 'key = {}'.format(k)
            return k
        except:
            return -1

    def key(self):
        k = self._key()
        if k == 27:
            self.stdscr.nodelay(True)
            n = self._key()
            if n >= 0:
                k = 'ALT+' + keyname(n)
            self.stdscr.nodelay(False)
            return k
        return keyname(k)

    def render(self):
        rows, cols = self.stdscr.getmaxyx()
        self.stdscr.clear()

        if rows > 1:
            n = min(rows-1, 0 if self.editing else len(self.command.buffer))
            rows -= n

            self.stdscr.addstr(rows-1, 0, self.status[:cols], curses.A_REVERSE)
            self.stdscr.chgat(-1, curses.A_REVERSE)

            self.buffer.render(self.stdscr, 0, rows-1, cols)

            if not self.editing:
                self.command.render(self.stdscr, rows, n, cols)

        self.stdscr.refresh()

