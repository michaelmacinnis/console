import screen

scr = screen.Screen()

while True:
    scr.render()

    key = scr.key()
    if key == 27:
        break

    scr.handle(key)

scr.close()

