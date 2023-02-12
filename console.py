#!/usr/bin/env python3

import fcntl
import os
import pty
import select
import signal
import struct
import sys
import tty

import debug
import mode
import options
import terminal


# Constants.
MULTI_LINE = b"multi-line: bash, type-ahead: "  # TODO: Replace with escape sequence.
STDIN_FILENO = 0
STDOUT_FILENO = 1
STDERR_FILENO = 2


def canonical_mode(lst):
    return lst[3] & tty.ICANON > 0


def main(term):
    """Parent copy loop.
    Copies
            child fd -> standard output   (read_child)
            standard input -> child fd    (read_fd)"""
    resize()

    canonical = True

    while True:
        if canonical:
            term.render()

        debug.log("waiting...")

        fds = [STDIN_FILENO, upstream_fd, pfds[0]]
        rfds, _, xfds = select.select(fds, [], fds)

        debug.log("got something...", rfds, xfds)

        if upstream_fd in rfds:
            # Handle EOF. Whether an empty byte string or OSError.
            try:
                data, eof = read_child(upstream_fd)
            except OSError:
                eof = True

            if eof:  # Reached EOF.
                debug.log("eof")

                # Assume the child process exited or is unreachable.
                break

            elif data:
                debug.log("<- ", data)
                if canonical:
                    s = data.split(MULTI_LINE)
                    if len(s) > 1:
                        term.command.multiline = True
                        data = s[0]

                        debug.log("checking for type ahead")
                        if s[1] and s[1] != b"\r\n":
                            debug.log("typeahead", s[1])
                            term.command.append(s[1])

                        os.kill(pid, signal.SIGCONT)

                    if data:
                        term.append(data)
                else:
                    write_all(STDOUT_FILENO, data)

        if STDIN_FILENO in rfds:
            if canonical:
                if not terminal_input(term, upstream_fd):
                    break

            else:
                data = read_fd(STDIN_FILENO)
                if data:
                    write_all(upstream_fd, data)

        if pfds[0] in rfds:
            data = os.read(pfds[0], 1024)
            if data == b"x":
                break

        if upstream_fd in xfds:
            canonical = canonical_mode(tty.tcgetattr(upstream_fd))
            if not canonical:
                resize()

            mode.print(tty.tcgetattr(upstream_fd))


def pipe():
    p = os.pipe()

    flags = fcntl.fcntl(p[0], fcntl.F_GETFL)
    fcntl.fcntl(p[0], fcntl.F_SETFL, flags | os.O_NONBLOCK)

    flags = fcntl.fcntl(p[1], fcntl.F_GETFL)
    fcntl.fcntl(p[1], fcntl.F_SETFL, flags | os.O_NONBLOCK)

    return p


def read_all(fd):
    data = b""
    while True:
        r, _, _ = select.select([fd], [], [], 0)
        if not r:
            break

        data += os.read(fd, 1024)
    return data


def read_child(fd):
    """Default read function."""
    b = os.read(fd, 1024)

    debug.log("pkt_read", len(b), b[0] if len(b) else None)
    if b:
        data = b[1:]
        return data, not b[0] and not data

    return None, False


def read_fd(fd):
    """Default read function."""
    b = os.read(fd, 1024)

    debug.log("read", len(b), b[0] if len(b) else None)

    return b


def resize():
    cols, rows = os.get_terminal_size()

    debug.log("TERMINAL SIZE =", cols, "x", rows)

    # Tell terminal (curses) about the new size.
    terminal.resize(rows, cols)

    # Tell pseudo-terminal (child process) about the new size.
    w = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(upstream_fd, tty.TIOCSWINSZ, w)


def sigchld(signum, frame):
    global exitcode

    cpid, status = os.wait()

    debug.log(f"pid {cpid}, status {status}")
    if cpid == pid:
        exitcode = os.waitstatus_to_exitcode(status)
        write_all(pfds[1], b"x")


def sigwinch(signum, frame):
    resize()

    debug.log("SIGWINCH")

    write_all(pfds[1], b"r")


def spawn(argv):
    """Create a spawned process."""
    if type(argv) == type(""):
        argv = (argv,)

    pid, upstream_fd = pty.fork()
    if not pid:
        # Child.
        ml = MULTI_LINE.decode('utf8')
        os.environ["PROMPT_COMMAND"] = '; '.join((
            'read -n8192 -t0.01 ta',
            f'echo "{ml}$ta"',
            'kill -sTSTP $$',
        ))

        os.environ["PS1"] = ""
        os.environ["PS2"] = ""

        os.execlp(argv[0], *argv)

    # Parent.
    fcntl.ioctl(upstream_fd, tty.TIOCPKT, "    ")

    return pid, upstream_fd


def terminal_input(term, fd):
    res = term.handle(term.key())
    if res:
        cmd = term.cmd()
        if cmd:
            write_all(fd, cmd)
    return res


def write_all(fd, data):
    """Write all the data to a descriptor."""
    while data:
        n = os.write(fd, data)
        data = data[n:]


exitcode = 0

pfds = pipe()

pid, upstream_fd = spawn(
    ["bash", "--noediting", "--noprofile", "--norc"]
)

signal.signal(signal.SIGCHLD, sigchld)
signal.signal(signal.SIGWINCH, sigwinch)

term = terminal.Terminal(filename=options.parsed["FILE"])
term.Run(main)

os.close(upstream_fd)

sys.exit(exitcode)
