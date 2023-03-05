class Point:
    def __init__(self, x, y):
        self.set(x, y)

    def equal(self, x, y):
        return self.x == x and self.y == y

    def invalid(self):
        return self.x < 0 or self.y < 0

    def move(self, x, y):
        self.x += x
        self.y += y

    def set(self, x, y):
        self.x = x
        self.y = y
