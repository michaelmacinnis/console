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

        self.status = repr(curses.tigetstr("kxIN"))

        print(getstr("kxIN"), file=sys.stderr)
        print(getstr("kxOUT"), file=sys.stderr)

        self.status = repr(self.dll.define_key(getstr("kxIN"), 1001))
        self.dll.define_key(getstr("kxOUT"), 1002)

        print(curses.has_key(1001), file=sys.stderr)
        print(curses.has_key(1002), file=sys.stderr)

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

        buf = self.buffer.render()
        cmd = self.command.render()

        if rows > 2:
            self.stdscr.addstr(rows-2, 0, self.status, curses.A_REVERSE)
            self.stdscr.chgat(-1, curses.A_REVERSE)

            if self.editing:
                self.stdscr.addstr(rows-1, 0, cmd)
                self.stdscr.addstr(0, 0, buf)
            else:
                self.stdscr.addstr(0, 0, buf)
                self.stdscr.addstr(rows-1, 0, cmd)


        self.stdscr.refresh()

        if self.editing:
            curses.setsyx(0, len(buf))
        else:
            curses.setsyx(rows-1, len(cmd))

