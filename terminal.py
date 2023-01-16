import curses
import os

import buffer

class Terminal:
    def __init__(self):
        self.buffer = buffer.Buffer()
        self.command = buffer.Buffer()
        self.editing = False
        self.status = ''

        os.environ.setdefault('ESCDELAY', '50')

        self.stdscr = curses.initscr()

        curses.curs_set(2)
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)

        curses.cbreak()
        curses.noecho()
        curses.raw()

        self.stdscr.keypad(True)

    def close(self):
        self.stdscr.keypad(False)

        curses.noraw()
        curses.nocbreak()
        curses.echo()

        curses.endwin()
        curses.flushinp()

    def handle(self, key):
        self.status = 'key = {}'.format(key)

        if key == b'KEY_MOUSE':
            id, x, y, z, bstate = curses.getmouse()
            self.status += ' id = {} x = {} y = {} z = {} bstate = {}'.format(
                id, x, y, z, bstate
            )

            rows, _ = self.stdscr.getmaxyx()
            self.editing = y < rows - 2

            return True

        if key == chr(5):
            self.editing = False
            return True
        elif key == chr(23):
            self.editing = True
            return True
        elif key == chr(17):
            if self.editing:
                return False

        if self.editing:
            self.buffer.handle(key)
        else:
            self.command.handle(key)

        return True

    def _key(self):
        try:
            k = self.stdscr.get_wch()
            if isinstance(k, int):
                k = curses.keyname(k)

            return k
        except:
            return ''

    def key(self):
        k = self._key()
        if k == chr(27):
            self.stdscr.nodelay(True)
            n = self._key()
            if n != '':
                k = 'ALT+' + n
            self.stdscr.nodelay(False)
        return k

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

