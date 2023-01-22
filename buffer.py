import curses
import curses.ascii
import os

bindings = {
    b'KEY_BACKSPACE': 'delete_char',
}

# TODO: Make this something more efficient.
# Memory mapped file or ropes or something.
class Buffer:
    def __init__(self):
        self.clear()

    def clear(self):
        self.buffer = ''
        self.cursor = 0

    def close(self):
        pass

    def handle(self, key):
        action = bindings.get(key, None)
        if action is None:
            if len(key) == 1 and curses.ascii.isprint(ord(key)):
                self.buffer += key
                self.cursor += 1

            return

        getattr(self, action)()

    def render(self):
        return self.buffer

    # Actions.
    def delete_char(self):
        if self.cursor:
            cursor = self.cursor - 1
            self.buffer = self.buffer[:cursor] + self.buffer[self.cursor:]
            self.cursor -= 1
