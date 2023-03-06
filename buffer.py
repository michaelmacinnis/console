import collections
import re

import debug
import point


class Buffer(collections.UserList):
    def __init__(self, data):
        super().__init__(data)

    def append(self, raw):
        self.insert(self.end(), raw)

    def end(self):
        return point.Point(len(self[-1]), len(self) - 1)

    def chunks(self, width, row, col, p0, p1):
        blank = " " * width
        shift = 0

        if 0 <= row < len(self):
            line = self[row]

            if row < p0.y or p1.y < row:
                # The line is not within the selected region.
                unselected = line[col:][:width]
                yield Chunk(0, False, unselected)

                shift += len(unselected)
                width -= len(unselected)

            if p0.y < row < p1.y:
                # The line is completely within the selected region.
                selected = (line[col:] + blank[:1])[:width]
                yield Chunk(0, True, selected)

                shift += len(selected)
                width -= len(selected)

            if row == p0.y:
                # The line is at the start of the selected region.
                if col < p0.x:
                    unselected = line[col : p0.x][:width]
                    yield Chunk(0, False, unselected)

                    shift += len(unselected)
                    width -= len(unselected)

                if width > 0 and row < p1.y:
                    selected = (line[col + shift :] + blank[:1])[:width]
                    yield Chunk(shift, True, selected)

                    shift += len(selected)
                    width -= len(selected)

            if row == p1.y:
                # The line is at the end of the selected region.
                if width > 0 and col + shift < p1.x:
                    selected = line[col + shift : p1.x][:width]
                    yield Chunk(shift, True, selected)

                    shift += len(selected)
                    width -= len(selected)

                if width > 0:
                    if len(line) < p1.x:
                        # The "newline" is also selected.
                        yield Chunk(shift, True, blank[:1])

                        shift += 1
                        width -= 1

                    else:
                        unselected = line[p1.x :][:width]
                        yield Chunk(shift, False, unselected)

                        shift += len(unselected)
                        width -= len(unselected)

        if width:
            yield Chunk(shift, False, blank[:width])

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
        remainder = self[p1.y + 1 :]

        if p1.x > len(self[p1.y]):
            below = ""
            if len(remainder):
                below = remainder[:1][0]
                remainder = remainder[1:]

            self[p0.y] = self[p0.y][: p0.x] + below
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


# A display chunk.
Chunk = collections.namedtuple("Chunk", "col sel str")

delim = re.compile(rb"\r?\n")


def join(lines):
    return "\n".join(lines).encode("utf8")


def split(raw):
    return list(line.expandtabs().decode("utf8") for line in delim.split(raw))
