#!/usr/bin/env python3

import fcntl
import os
import pty
import select
import sys
import tty

CHILD = 0

STDIN_FILENO = 0
STDOUT_FILENO = 1
STDERR_FILENO = 2

def _writen(fd, data):
    """Write all the data to a descriptor."""
    while data:
        n = os.write(fd, data)
        data = data[n:]

def _read(fd):
    """Default read function."""
    return os.read(fd, 1024)

def _pkt_read(fd):
    """Default read function."""
    b = os.read(fd, 1024)
    if b:
        b = b[1:]

    return b

def _copy(child_fd, child_read=_pkt_read, stdin_read=_read):
    """Parent copy loop.
    Copies
            child fd -> standard output   (child_read)
            standard input -> child fd    (stdin_read)"""
    fds = [child_fd, STDIN_FILENO]
    while fds:
        rfds, _, xfds = select.select(fds, [], fds)

        if child_fd in rfds:
            # Some OSes signal EOF by returning an empty byte string,
            # some throw OSErrors.
            try:
                data = child_read(child_fd)
            except OSError:
                data = b""
            if not data:  # Reached EOF.
                return    # Assume the child process has exited and is
                          # unreachable, so we clean up.
            else:
                os.write(STDOUT_FILENO, data)

        if STDIN_FILENO in rfds:
            data = stdin_read(STDIN_FILENO)
            if not data:
                fds.remove(STDIN_FILENO)
            else:
                _writen(child_fd, data)

        if child_fd in xfds:
            print("mode change", tty.tcgetattr(child_fd), file=sys.stderr)

def spawn(argv, child_read=_read, stdin_read=_read):
    """Create a spawned process."""
    if type(argv) == type(''):
        argv = (argv,)
    sys.audit('pty.spawn', argv)

    pid, child_fd = pty.fork()
    if pid == CHILD:
        os.execlp(argv[0], *argv)

    try:
        mode = tty.tcgetattr(STDIN_FILENO)
        tty.setraw(STDIN_FILENO)
        restore = True
    except tty.error:    # This is the same as termios.error
        restore = False

    fcntl.ioctl(child_fd, tty.TIOCPKT, "    ")

    try:
        _copy(child_fd, child_read, stdin_read)
    finally:
        if restore:
            tty.tcsetattr(STDIN_FILENO, tty.TCSAFLUSH, mode)

    os.close(child_fd)
    return os.waitpid(pid, 0)[1]

def request(fd):
    return os.read(fd, 65536)

def response(fd):
    return os.read(fd, 65536)

status = spawn(["sh"], response, request)

print(status)

status = os.waitstatus_to_exitcode(status)

print(status)

sys.exit(status)
