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

# TODO: Replace with escape sequence and also send back pid.
MULTI_LINE = b"multi-line: bash, type-ahead: "

STDIN_FILENO = 0
STDOUT_FILENO = 1
STDERR_FILENO = 2


def clear(term, canonical):
    resize()
    if canonical:
        term.stdscr.clear()


def extract_type_ahead(data):
    idx = data.find(MULTI_LINE)
    if idx < 0:
        return data, None

    return data[:idx], remove_suffix(data[idx + len(MULTI_LINE) :], b"\r\n")


def handle_mode_change(term, canonical, fd):
    lst = tty.tcgetattr(fd)

    icanon_set = lst[3] & tty.ICANON > 0
    if icanon_set != canonical:
        # Mode change.
        mode.print(lst)

        clear(term, True)

    return icanon_set


def remove_suffix(b, suffix):
    if suffix and b.endswith(suffix):
        return b[: -len(suffix)]
    return b


def main(term):
    """Main event loop.
    Handles
            input from program running in a pseudo-terminal (child_fd);
            input from the user through the terminal (STDIN_FILENO);
            special events sent using the self-pipe trick (pfds[0])."""

    canonical = True
    clear(term, canonical)

    while True:
        if canonical:
            term.render()

        debug.log("waiting...")

        fds = [STDIN_FILENO, child_fd, pfds[0]]
        rfds, _, xfds = select.select(fds, [], fds)

        # debug.log("got something...", rfds, xfds)

        # NOTE: We avoid continues as there may be other fds to handle.

        if child_fd in xfds:
            canonical = handle_mode_change(term, canonical, child_fd)
            debug.log("after mode change")

        if child_fd in rfds:
            data, eof = read_child(child_fd)
            if eof:
                # debug.log("eof")

                # Assume the child process exited or is unreachable.
                break

            if data:
                # debug.log("<- ", data)

                data, type_ahead = extract_type_ahead(data)
                if type_ahead is not None:
                    if not canonical:
                        clear(term, True)
                    canonical = True

                    term.type_ahead(type_ahead)

                    os.kill(pid, signal.SIGCONT)

                if canonical:
                    # TODO: Parse and look for specific escape codes.
                    if data.startswith(b"\x1b[?1049h") or data.startswith(b"\x1b["):
                        canonical = handle_mode_change(term, canonical, child_fd)
                        write_all(STDOUT_FILENO, data)
                    elif data:
                        term.output(data)
                else:
                    write_all(STDOUT_FILENO, data)

        if STDIN_FILENO in rfds:
            if canonical:
                data, eof = term.input()
                if eof:
                    break
            else:
                data = read_fd(STDIN_FILENO)

            if data:
                write_all(child_fd, data)

        if pfds[0] in rfds:
            data = read_fd(pfds[0])
            if data == b"x":
                break


def pipe():
    p = os.pipe()

    flags = fcntl.fcntl(p[0], fcntl.F_GETFL)
    fcntl.fcntl(p[0], fcntl.F_SETFL, flags | os.O_NONBLOCK)

    flags = fcntl.fcntl(p[1], fcntl.F_GETFL)
    fcntl.fcntl(p[1], fcntl.F_SETFL, flags | os.O_NONBLOCK)

    return p


def read_child(fd):
    # Handle EOF. Whether an empty byte string or OSError.
    try:
        data = os.read(fd, 1024)
        if data:
            return data[1:], False
    except OSError:
        pass

    return None, True


def read_fd(fd):
    return os.read(fd, 1024)


def resize():
    rows, cols, y, x = terminal.size(True)

    # debug.log("TERMINAL SIZE =", cols, "x", rows)

    # Tell pseudo-terminal (child process) about the new size.
    w = struct.pack("HHHH", rows, cols, y, x)
    fcntl.ioctl(child_fd, tty.TIOCSWINSZ, w)


def sigchld(signum, frame):
    global exitcode

    cpid, status = os.wait()

    # debug.log(f"pid {cpid}, status {status}")
    if cpid == pid:
        exitcode = waitstatus_to_exitcode(status)
        write_all(pfds[1], b"x")


def sigwinch(signum, frame):
    resize()

    # debug.log("SIGWINCH")

    write_all(pfds[1], b"r")


def spawn(argv):
    """Create a spawned process."""
    if type(argv) == type(""):
        argv = (argv,)

    pid, child_fd = pty.fork()
    if not pid:
        # Child.
        ml = MULTI_LINE.decode("utf8")
        os.environ["PROMPT_COMMAND"] = "; ".join(
            (
                "read -N8192 -t0.01 ta",
                f'echo "{ml}$ta"',
                "stty -echo",
                "kill -sTSTP $$",
            )
        )

        os.environ["PS1"] = ""
        os.environ["PS2"] = ""

        os.execlp(argv[0], *argv)

    # Parent.
    fcntl.ioctl(child_fd, tty.TIOCPKT, "    ")

    return pid, child_fd


def waitstatus_to_exitcode(status):
    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status)
    elif os.WIFSIGNALED(status):
        return -os.WTERMSIG(status)
    else:
        raise ValueError(f"invalid wait status: {status!r}")


def write_all(fd, data):
    while data:
        n = os.write(fd, data)
        data = data[n:]


exitcode = 0

pfds = pipe()

pid, child_fd = spawn(["bash", "--noediting", "--noprofile", "--norc"])

signal.signal(signal.SIGCHLD, sigchld)
signal.signal(signal.SIGWINCH, sigwinch)

terminal.Terminal(filename=options.parsed["FILE"]).run(main)

os.close(child_fd)

sys.exit(exitcode)
