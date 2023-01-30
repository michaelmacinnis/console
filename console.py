#!/usr/bin/env python3

import fcntl
import os
import pty
import select
import signal
import struct
import sys
import tty

import terminal

STDIN_FILENO = 0
STDOUT_FILENO = 1


def canonical_mode(lst):
    return lst[3] & tty.ICANON > 0


def main():
    """Parent copy loop.
    Copies
            child fd -> standard output   (read_child)
            standard input -> child fd    (read_fd)"""
    canonical = True

    while True:
        if canonical:
            term.render()

        fds = [STDIN_FILENO, child_fd, pfds[0]]
        rfds, _, xfds = select.select(fds, [], fds)

        print("got something...", rfds, xfds, file=sys.stderr)

        if child_fd in rfds:
            # Handle EOF. Whether an empty byte string or OSError.
            try:
                data, eof = read_child(child_fd)
            except OSError:
                eof = True

            if eof:  # Reached EOF.
                print("eof", file=sys.stderr)

                # Assume the child process exited or is unreachable.
                break

            elif data:
                print("<- ", data, file=sys.stderr)
                if canonical:
                    term.append(data)
                else:
                    write_all(STDOUT_FILENO, data)

        if STDIN_FILENO in rfds:
            if canonical:
                if not terminal_input(child_fd):
                    break

            else:
                data = read_fd(STDIN_FILENO)
                if data:
                    write_all(child_fd, data)

        if pfds[0] in rfds:
            data = os.read(pfds[0], 1024)
            if data == b"x":
                break

        if child_fd in xfds:
            canonical = canonical_mode(tty.tcgetattr(child_fd))
            if not canonical:
                resize()

            # print_mode(tty.tcgetattr(child_fd))


def pipe():
    p = os.pipe()

    flags = fcntl.fcntl(p[0], fcntl.F_GETFL)
    fcntl.fcntl(p[0], fcntl.F_SETFL, flags | os.O_NONBLOCK)

    flags = fcntl.fcntl(p[1], fcntl.F_GETFL)
    fcntl.fcntl(p[1], fcntl.F_SETFL, flags | os.O_NONBLOCK)

    return p


def read_child(fd):
    """Default read function."""
    b = os.read(fd, 1024)

    print("pkt_read", len(b), b[0] if len(b) else None, file=sys.stderr)
    if b:
        data = b[1:]
        return data, not b[0] and not data

    return None, False


def read_fd(fd):
    """Default read function."""
    b = os.read(fd, 1024)

    print("read", len(b), b[0] if len(b) else None, file=sys.stderr)

    return b


def resize():
    cols, rows = os.get_terminal_size()

    print("TERMINAL SIZE =", cols, "x", rows, file=sys.stderr)

    # Tell terminal (curses) about the new size.
    terminal.resize(rows, cols)

    # Tell pseudo-terminal (child process) about the new size.
    w = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(child_fd, tty.TIOCSWINSZ, w)


def sigchld(signum, frame):
    global status

    cpid, status = os.wait()
    if cpid == pid:
        write_all(pfds[1], b"x")


def sigwinch(signum, frame):
    resize()
    print("SIGWINCH", file=sys.stderr)
    write_all(pfds[1], b"r")


def spawn(argv):
    """Create a spawned process."""
    if type(argv) == type(""):
        argv = (argv,)

    pid, fd = pty.fork()
    if not pid:
        # Child.
        os.environ.setdefault("PS1", "")
        os.execlp(argv[0], *argv)

    fcntl.ioctl(fd, tty.TIOCPKT, "    ")

    return pid, fd


def terminal_input(fd):
    res = term.handle(term.key())
    if res:
        cmd = term.cmd()
        if cmd:
            write_all(fd, cmd.encode("utf-8"))
            write_all(fd, b"\n")
    return res


def write_all(fd, data):
    """Write all the data to a descriptor."""
    while data:
        n = os.write(fd, data)
        data = data[n:]


filename = None
if len(sys.argv) == 2:
    filename = sys.argv[1]

pid, child_fd = spawn(["sh"])

pfds = pipe()
status = 0

signal.signal(signal.SIGCHLD, sigchld)
signal.signal(signal.SIGWINCH, sigwinch)

term = terminal.Terminal(filename=filename)
term.Run(main)

os.close(child_fd)
print(os.waitstatus_to_exitcode(status))


# Unused.

control_modes = {
    tty.CSIZE: "Character size",
    tty.CSTOPB: "Send two stop bits, else one",
    tty.CREAD: "Enable receiver",
    tty.PARENB: "Parity enable",
    tty.PARODD: "Odd parity, else even",
    tty.HUPCL: "Hang up on last close",
    tty.CLOCAL: "Ignore modem status lines",
}

input_modes = {
    tty.BRKINT: "Signal interrupt on break",
    tty.ICRNL: "Map CR to NL on input",
    tty.IGNBRK: "Ignore break condition",
    tty.IGNCR: "Ignore CR",
    tty.IGNPAR: "Ignore characters with parity errors",
    tty.INLCR: "Map NL to CR on input",
    tty.INPCK: "Enable input parity check",
    tty.ISTRIP: "Strip character",
    tty.IXANY: "Enable any character to restart output",
    tty.IXOFF: "Enable start/stop input control",
    tty.IXON: "Enable start/stop output control",
    tty.PARMRK: "Mark parity errors",
}

local_modes = {
    tty.ECHO: "Enable echo",
    tty.ECHOE: "Echo erase character as error-correcting backspace",
    tty.ECHOK: "Echo KILL",
    tty.ECHONL: "Echo NL",
    tty.ICANON: "Canonical input (erase and kill processing)",
    tty.IEXTEN: "Enable extended input character processing",
    tty.ISIG: "Enable signals",
    tty.NOFLSH: "Disable flush after interrupt or quit",
    tty.TOSTOP: "Send SIGTTOU for background output",
}

output_modes = {
    tty.OPOST: "Post-process output",
    tty.ONLCR: "Map NL to CR-NL on output",
    tty.OCRNL: "Map CR to NL on output",
    tty.ONOCR: "No CR output at column 0",
    tty.ONLRET: "NL performs CR function",
    tty.OFILL: "Use fill characters for delay",
    tty.NLDLY: "Newline delay",
    tty.CRDLY: "Carriage-return delay",
    tty.TABDLY: "Horizontal-tab delay",
    tty.BSDLY: "Backspace delay",
    tty.VTDLY: "Vertical-tab delay",
    tty.FFDLY: "Form-feed delay",
}


def print_mode(lst):
    print("mode change:", file=sys.stderr)

    modes = [input_modes, output_modes, control_modes, local_modes]
    for i in range(4):
        flags = lst[i]
        for flag, description in modes[i].items():
            if flag & flags:
                print(description, file=sys.stderr)

    print(file=sys.stderr)
