import curses
import os
import sys

from ctypes import CDLL, create_string_buffer

import buffer

def getstr(op):
    return curses.tigetstr(op)

def keyname(n):
    if n < 0:
        return ''
    return curses.keyname(n).decode('utf-8')

class Terminal:
    def __init__(self):
        self.buffer = buffer.Buffer()
        self.command = buffer.Buffer()
        self.editing = False
        self.status = ''

        os.environ.setdefault('ESCDELAY', '50')

        self.stdscr = curses.initscr()

        self.dll = CDLL('/lib/x86_64-linux-gnu/libncursesw.so.6')

        curses.curs_set(2)
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        #curses.mousemask(16777215)

        import _curses

        print(dir(curses), file=sys.stderr)
        print(dir(_curses), file=sys.stderr)
        print(dir(self.stdscr), file=sys.stderr)

        curses.cbreak()
        curses.noecho()
        curses.raw()

        self.stdscr.keypad(True)

        # Make sure focus in/out are defined.
        self.dll.define_key(b'\x1b[I', 1001)
        self.dll.define_key(b'\x1b[O', 1002)

        print(curses.has_key(1001), file=sys.stderr)
        print(curses.has_key(1002), file=sys.stderr)
        print('focus in defined', self.dll.key_defined(b'\x1b[I'), file=sys.stderr)
        print('focus out defined', self.dll.key_defined(b'\x1b[O'), file=sys.stderr)

    def close(self):
        self.stdscr.keypad(False)

        curses.noraw()
        curses.nocbreak()
        curses.echo()

        curses.endwin()
        curses.flushinp()

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
            if key == "^J":
                cmd = self.command.buffer
                self.command.clear()
                print(cmd, file=sys.stderr)
            else:
                self.command.handle(key)

        return True

    def _key(self):
        try:
            #k = self.stdscr.getch()
            k = self.dll.getch()
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

        # The buffer renders from 0 to rows-3
        # The status renders at rows-2
        # The command renders at rows-1

        self.buffer.render(self.stdscr, 0, rows-2, cols)
        self.command.render(self.stdscr, rows-1, 1, cols)

        if rows > 2:
            self.stdscr.addstr(rows-2, 0, self.status[:cols], curses.A_REVERSE)
            self.stdscr.chgat(-1, curses.A_REVERSE)

            if self.editing:
                self.command.render(self.stdscr, rows-1, 1, cols)
                self.buffer.render(self.stdscr, 0, rows-2, cols)
                #self.stdscr.addstr(rows-1, 0, cmd)
                #self.stdscr.addstr(0, 0, buf)
            else:
                self.buffer.render(self.stdscr, 0, rows-2, cols)
                self.command.render(self.stdscr, rows-1, 1, cols)
                #self.stdscr.addstr(0, 0, buf)
                #self.stdscr.addstr(rows-1, 0, cmd)


        self.stdscr.refresh()

