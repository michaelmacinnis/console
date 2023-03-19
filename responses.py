import debug

# Responses.
def exit(terminal):
    return yes(terminal.status.complete)

def line_number(terminal):
    n = natural(terminal.status.complete)
    debug.log("line number:", n)
    if n > 0:
        if terminal.editing:
            terminal.buf.goto_line(n)
        else:
            terminal.cli.goto_line(n)

    return False

def send_eof(terminal):
    if yes(terminal.status.complete):
        terminal.cli.complete = b"\x04"
        terminal.cli.clear()

    return False

# Helpers.
def natural(s):
    try:
        return int(s)
    except:
        return 0

def yes(s):
    return s.lower()[:1] == "y"

