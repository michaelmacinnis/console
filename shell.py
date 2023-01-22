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

control_modes = {
    tty.CSIZE:  "Character size",
    tty.CSTOPB: "Send two stop bits, else one",
    tty.CREAD:  "Enable receiver",
    tty.PARENB: "Parity enable",
    tty.PARODD: "Odd parity, else even",
    tty.HUPCL:  "Hang up on last close",
    tty.CLOCAL: "Ignore modem status lines",
}

input_modes = {
    tty.BRKINT: "Signal interrupt on break",
    tty.ICRNL:  "Map CR to NL on input",
    tty.IGNBRK: "Ignore break condition",
    tty.IGNCR:  "Ignore CR",
    tty.IGNPAR: "Ignore characters with parity errors",
    tty.INLCR:  "Map NL to CR on input",
    tty.INPCK:  "Enable input parity check",
    tty.ISTRIP: "Strip character",
    tty.IXANY:  "Enable any character to restart output",
    tty.IXOFF:  "Enable start/stop input control",
    tty.IXON:   "Enable start/stop output control",
    tty.PARMRK: "Mark parity errors",
}

local_modes = {
    tty.ECHO:   "Enable echo",
    tty.ECHOE:  "Echo erase character as error-correcting backspace",
    tty.ECHOK:  "Echo KILL",
    tty.ECHONL: "Echo NL",
    tty.ICANON: "Canonical input (erase and kill processing)",
    tty.IEXTEN: "Enable extended input character processing",
    tty.ISIG:   "Enable signals",
    tty.NOFLSH: "Disable flush after interrupt or quit",
    tty.TOSTOP: "Send SIGTTOU for background output",
}

output_modes = {
    tty.OPOST:  "Post-process output",
    tty.ONLCR:  "Map NL to CR-NL on output",
    tty.OCRNL:  "Map CR to NL on output",
    tty.ONOCR:  "No CR output at column 0",
    tty.ONLRET: "NL performs CR function",
    tty.OFILL:  "Use fill characters for delay",
    tty.NLDLY:  "Newline delay",
    tty.CRDLY:  "Carriage-return delay",
    tty.TABDLY: "Horizontal-tab delay",
    tty.BSDLY:  "Backspace delay",
    tty.VTDLY:  "Vertical-tab delay",
    tty.FFDLY:  "Form-feed delay",
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

def _copy(child_fd, child_read, stdin_read):
    """Parent copy loop.
    Copies
            child fd -> standard output   (child_read)
            standard input -> child fd    (stdin_read)"""
    fds = [STDIN_FILENO, child_fd]
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
            print_mode(tty.tcgetattr(child_fd))

def spawn(argv):
    """Create a spawned process."""
    if type(argv) == type(''):
        argv = (argv,)

    pid, fd = pty.fork()
    if pid == CHILD:
        os.execlp(argv[0], *argv)

    return pid, fd

pid, fd = spawn(["sh"])

try:
    mode = tty.tcgetattr(STDIN_FILENO)
    tty.setraw(STDIN_FILENO)
    restore = True
except tty.error:    # This is the same as termios.error
    restore = False

fcntl.ioctl(fd, tty.TIOCPKT, "    ")

try:
    _copy(fd, _pkt_read, _read)
finally:
    if restore:
        tty.tcsetattr(STDIN_FILENO, tty.TCSAFLUSH, mode)

os.close(fd)

status = os.waitpid(pid, 0)[1]

print(status)

status = os.waitstatus_to_exitcode(status)

print(status)

sys.exit(status)
