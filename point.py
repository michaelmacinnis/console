class Point:
    def __init__(self, x=-1, y=-1):
        self.set(x, y)

    def __repr__(self):
        return f"Point({self.x}, {self.y})"

    def equal(self, x, y):
        return self.x == x and self.y == y

    def clear(self):
        self.x = -1
        self.y = -1

    def clip(self, maxx, maxy):
        self.x += correction(self.x, 0, maxx)
        self.y += correction(self.y, 0, maxy)

    def move(self, x, y):
        self.x += x
        self.y += y

    def set(self, x, y):
        self.x = x
        self.y = y

    def valid(self):
        return self.x >= 0 and self.y >= 0


def correction(element, lower, upper):
    if element < lower:
        return lower - element

    if element > upper:
        return upper - element

    return 0
