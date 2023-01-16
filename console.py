import terminal

term = terminal.Terminal()

while True:
    term.render()

    if not term.handle(term.key()):
        break

term.close()

