class Point:
    def __init__(self, x=-1, y=-1):
        self.set(x, y)

    def equal(self, x, y):
        return self.x == x and self.y == y

    def clear(self):
        self.x = -1
        self.y = -1

    def move(self, x, y):
        self.x += x
        self.y += y

    def set(self, x, y):
        self.x = x
        self.y = y

    def valid(self):
        return self.x >= 0 and self.y >= 0
