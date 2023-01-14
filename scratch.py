import curses
import curses.ascii

stdscr = curses.initscr()

curses.curs_set(2)
curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)

curses.cbreak()
curses.noecho()
curses.raw()

#if curses.has_colors():
#    curses.start_color()

stdscr.keypad(True)

def render(stdscr, buffer, status, command, editing):
    rows, cols = stdscr.getmaxyx()
    stdscr.clear()

    if rows > 2:
        stdscr.addstr(rows-2, 0, status, curses.A_REVERSE)
        stdscr.chgat(-1, curses.A_REVERSE)

        if editing:
            stdscr.addstr(rows-1, 0, command)
            stdscr.addstr(0, 0, buffer)
        else:
            stdscr.addstr(0, 0, buffer)
            stdscr.addstr(rows-1, 0, command)


    stdscr.refresh()

    if editing:
        curses.setsyx(0, len(buffer))
    else:
        curses.setsyx(rows-1, len(command))

buffer = ''
command = ''
editing = False
status = ''

while True:
    render(stdscr, buffer, status, command, editing)

    key = stdscr.getch()
    if key == 27:
        break

    status = 'key = {}'.format(curses.keyname(key))
    if key == curses.KEY_MOUSE:
        id, x, y, z, bstate = curses.getmouse()
        status += ' id = {} x = {} y = {} z = {} bstate = {}'.format(
            id, x, y, z, bstate
        )

        rows, _ = stdscr.getmaxyx()
        editing = y < rows - 2

    if curses.ascii.isprint(key):
        if editing:
            buffer += chr(key)
        else:
            command += chr(key)

stdscr.keypad(False)

curses.noraw()
curses.nocbreak()
curses.echo()

curses.endwin()
curses.flushinp()
