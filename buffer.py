import curses
import curses.ascii
import os
import sys

bindings = {
    'KEY_BACKSPACE': 'delete_char',
}

# TODO: Make this something more efficient.
# Memory mapped file or ropes or something.
class Buffer:
    def __init__(self):
        self.clear()

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

    def render(self, stdscr, offset, rows, cols):
        if self.x < 0:
            self.x = 0
        elif self.x > cols-2: # Leave room for the cursor.
            self.x = cols-2

        col = self.col - self.x
        if col < 1:
            col = 1

        if self.y < 0:
            self.y = 0
        elif self.y > rows-1:
            self.y = rows-1

        row = self.row - self.y
        if row < 1:
            row = 1

        for line in self.buffer[row-1:][:rows]:
            stdscr.addstr(offset, 0, line[col-1:][:cols-1])
            offset += 1

        curses.setsyx(self.y, self.x)

    # Actions.
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
                if self.y:
                    self.y -= 1
            return

        line = self.buffer[self.row-1]
        self.buffer[self.row-1] = line[:self.col-1] + line[self.col:]
        self.col -= 1
        if self.x:
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

