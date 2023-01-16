import terminal

term = terminal.Terminal()

while True:
    term.render()

    key = term.key()
    if key == chr(4):
        break

    term.handle(key)

term.close()

