import curses
import curses.ascii
import os
import sys

bindings = {
    'KEY_BACKSPACE': 'delete_char',
    'KEY_DOWN': 'cursor_down',
    'KEY_LEFT': 'cursor_left',
    'KEY_RIGHT': 'cursor_right',
    'KEY_UP': 'cursor_up',
    '^S': 'save_file'
}

def adjust(maximum, minimum, n):
    return minimum - n if n < minimum else maximum - n if n > maximum else 0

def clip(maximum, minimum, n):
    return n + adjust(maximum, minimum, n)

# TODO: Make this something more efficient.
# Memory mapped file or ropes or something.
class Buffer:
    def __init__(self, filename=None):
        self.clear()

        if filename:
            self.filename = filename
            with open(filename, 'r') as file:
                self.buffer = [line.rstrip("\n\r") for line in file]

    def clear(self):
        self.buffer = ['']
        self.col = 0
        self.row = 1
        self.x = 0
        self.y = 0

    def close(self):
        pass

    def handle(self, key):
        action = bindings.get(key, 'insert_char')

        getattr(self, action)(key)

        print('after', action, file=sys.stderr)
        self.print()

    def print(self):
        print(self.buffer, file=sys.stderr)

    def render(self, stdscr, offset, maxy, maxx):
        print("rendering", maxx, "x", maxy, file=sys.stderr)
        print("buffer cursor at", str(self.col)+","+str(self.row), file=sys.stderr)
        print("screen cursor at", str(self.x)+","+str(self.y), file=sys.stderr)

        n = adjust(len(self.buffer), 1, self.row)
        self.row += n
        self.y += n

        print("buffer cursor at", str(self.col)+","+str(self.row), file=sys.stderr)

        n = adjust(len(self.buffer[self.row-1]), 0, self.col)
        self.col += n
        self.x += n

        print("adjusted buffer cursor", str(self.col)+","+str(self.row), file=sys.stderr)
        print("adjusted screen cursor", str(self.x)+","+str(self.y), file=sys.stderr)

        self.x = clip(maxx-1, 0, self.x)
        self.y = clip(maxy-1, 0, self.y)

        print("clipped screen cursor", str(self.x)+","+str(self.y), file=sys.stderr)

        col = max(1, self.col - self.x + 1)
        row = max(1, self.row - self.y)

        last = self.y+offset
        print("adjusted", str(col)+","+str(row),file=sys.stderr)

        for line in self.buffer[row-1:][:maxy]:
            print("line", offset, row-1, line, file=sys.stderr)

            stdscr.addstr(offset, 0, line[col-1:][:maxx-1])
            offset += 1

        stdscr.move(last, self.x)

        print(file=sys.stderr)

    # Actions.
    def cursor_down(self, key):
        self.row += 1
        self.y += 1

    def cursor_left(self, key):
        self.col -= 1
        self.x -= 1

    def cursor_right(self, key):
        self.col += 1
        self.x += 1

    def cursor_up(self, key):
        self.row -= 1
        self.y -= 1

    def delete_char(self, key):
        if not self.col:
            # At the beginning of a line.
            prev = self.row - 1
            if prev > 0:
                # There are previous lines.
                self.col = len(self.buffer[prev-1])
                self.buffer[prev-1] += self.buffer[self.row-1]
                self.buffer = self.buffer[:prev] + self.buffer[self.row:]
                self.row = prev
                self.x = self.col
                self.y -= 1
            return

        line = self.buffer[self.row-1]
        self.buffer[self.row-1] = line[:self.col-1] + line[self.col:]
        self.col -= 1
        self.x -= 1

    def insert_char(self, key):
        if key == '^J':
            self.buffer = self.buffer[:self.row-1] + [self.buffer[self.row-1][:self.col]] + [self.buffer[self.row-1][self.col:]] + self.buffer[self.row:]
            self.col = 0
            self.row += 1
            self.x = 0
            self.y += 1
            return

        if len(key) == 1 and curses.ascii.isprint(ord(key)):
            line = self.buffer[self.row-1]
            self.buffer[self.row-1] = line[:self.col] + key + line[self.col:]
            self.col += 1
            self.x += 1

    def save_file(self, key):
        if self.filename:
            with open(self.filename, 'w') as file:
                file.write('\n'.join(self.buffer))
                file.write('\n')

