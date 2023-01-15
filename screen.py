import curses
import curses.ascii

class Screen:
    def __init__(self):
        self.buffer = ''
        self.command = ''
        self.editing = False
        self.status = ''

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
        self.status = 'key = {}'.format(curses.keyname(key))
        if key == curses.KEY_MOUSE:
            id, x, y, z, bstate = curses.getmouse()
            self.status += ' id = {} x = {} y = {} z = {} bstate = {}'.format(
                id, x, y, z, bstate
            )

            rows, _ = self.stdscr.getmaxyx()
            self.editing = y < rows - 2

        if curses.ascii.isprint(key):
            if self.editing:
                self.buffer += chr(key)
            else:
                self.command += chr(key)

    def key(self):
        return self.stdscr.getch()

    def render(self):
        rows, cols = self.stdscr.getmaxyx()
        self.stdscr.clear()

        if rows > 2:
            self.stdscr.addstr(rows-2, 0, self.status, curses.A_REVERSE)
            self.stdscr.chgat(-1, curses.A_REVERSE)

            if self.editing:
                self.stdscr.addstr(rows-1, 0, self.command)
                self.stdscr.addstr(0, 0, self.buffer)
            else:
                self.stdscr.addstr(0, 0, self.buffer)
                self.stdscr.addstr(rows-1, 0, self.command)


        self.stdscr.refresh()

        if self.editing:
            curses.setsyx(0, len(self.buffer))
        else:
            curses.setsyx(rows-1, len(self.command))

