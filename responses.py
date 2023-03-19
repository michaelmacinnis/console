import debug

# Responses.
def exit(terminal):
    return yes(terminal.status.command())

def forward_search(terminal):
    text = terminal.status.command()
    if terminal.editing:
        terminal.buf.goto_text(text)
    else:
        terminal.cli.goto_text(text)

    return False

def line_number(terminal):
    n = natural(terminal.status.command())
    debug.log("line number:", n)
    if n > 0:
        n -= 1
        if terminal.editing:
            terminal.buf.goto_line(n)
        else:
            terminal.cli.goto_line(n)

    return False

def reverse_search(terminal):
    text = terminal.status.command()
    if terminal.editing:
        terminal.buf.goto_text(text, -1)
    else:
        terminal.cli.goto_text(text, -1)

    return False

def send_eof(terminal):
    if yes(terminal.status.command()):
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

