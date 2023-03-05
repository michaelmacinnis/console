import collections
import re

import debug
import point


class Buffer(collections.UserList):
    def __init__(self, data):
        super().__init__(data)

    def append(self, raw):
        self.insert(point.Point(len(self[-1]), len(self) - 1), raw)

    def insert(self, cursor, raw):
        lines = split(raw)
        debug.log(f"BUFFER inserting: {repr(lines)} at {cursor}")
        if len(lines) == 1:
            self[cursor.y] = (
                self[cursor.y][: cursor.x] + lines[0] + self[cursor.y][cursor.x :]
            )
            return

        self.data = (
            self[: cursor.y]
            + [self[cursor.y][: cursor.x] + lines[0]]
            + lines[1:-1]
            + [lines[-1] + self[cursor.y][cursor.x :]]
            + self[cursor.y + 1 :]
        )

    def raw(self):
        return join(self)

    def remove(self, p0, p1):
        delta = 0
        remainder = self[p1.y + 1 :]

        if p1.x > len(self[p1.y]):
            delta = 1
            remainder = self[p1.y + 2 :]

            self[p0.y] = self[p0.y][: p0.x] + self[p1.y + 1]
        else:
            self[p0.y] = self[p0.y][: p0.x] + self[p1.y][p1.x :]

        self.data = self[: p0.y + 1] + remainder

    def select(self, p0, p1):
        if p0.y == p1.y:
            lines = [self[p0.y][p0.x : p1.x]]
        else:
            lines = [self[p0.y][p0.x :]]
            lines.extend(self[p0.y + 1 : p1.y])
            lines.append(self[p1.y][: p1.x])

        raw = join(lines)
        if p1.x > len(self[p1.y]):
            raw += b"\n"

        return raw


delim = re.compile(rb"\r?\n")


def join(lines):
    return "\n".join(lines).encode("utf8")


def split(raw):
    return list(line.decode("utf8") for line in delim.split(raw))
