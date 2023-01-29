#!/usr/bin/env python3

import fcntl
import os
import pty
import select
import signal
import struct
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

def pipe():
    p = os.pipe()

    flags = fcntl.fcntl(p[0], fcntl.F_GETFL)
    fcntl.fcntl(p[0], fcntl.F_SETFL, flags | os.O_NONBLOCK)

    flags = fcntl.fcntl(p[1], fcntl.F_GETFL)
    fcntl.fcntl(p[1], fcntl.F_SETFL, flags | os.O_NONBLOCK)

    return p

def print_mode(lst):
    print("mode change:", file=sys.stderr)

    modes = [input_modes, output_modes, control_modes, local_modes]
    for i in range(4):
        flags = lst[i]
        for flag, description in modes[i].items():
            if flag & flags:
                print(description, file=sys.stderr)

    print(file=sys.stderr)

def read_child(fd):
    """Default read function."""
    b = os.read(fd, 1024)

    print("pkt_read", len(b), b[0] if len(b) else None, file=sys.stderr)
    if b:
        data = b[1:]
        return data, not b[0] and not data

    return None, False

def read_stdin(fd):
    """Default read function."""
    b = os.read(fd, 1024)

    print("read", len(b), b[0] if len(b) else None, file=sys.stderr)

    return b

def resize(rows, cols):
    w = struct.pack('HHHH', rows, cols, 0, 0)
    fcntl.ioctl(child_fd, tty.TIOCSWINSZ, w)

def write_all(fd, data):
    """Write all the data to a descriptor."""
    while data:
        n = os.write(fd, data)
        data = data[n:]

def run(in_cb, out_cb):
    """Parent copy loop.
    Copies
            child fd -> standard output   (read_child)
            standard input -> child fd    (read_stdin)"""
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
            return False
        elif data:
            print("<- ", data, file=sys.stderr)
            out_cb(data)

    if STDIN_FILENO in rfds:
        if not in_cb(child_fd):
            return False

    if pfds[0] in rfds:
        data = os.read(pfds[0], 1024)
        if data == b'x':
            return False

    if child_fd in xfds:
        print_mode(tty.tcgetattr(child_fd))

    return True

def spawn(argv):
    """Create a spawned process."""
    if type(argv) == type(''):
        argv = (argv,)

    pid, fd = pty.fork()
    if pid == CHILD:
        os.environ.setdefault('PS1', '')
        os.execlp(argv[0], *argv)

    fcntl.ioctl(fd, tty.TIOCPKT, "    ")

    return pid, fd

pid, child_fd = spawn(["sh"])

print("pid", pid, file=sys.stderr)

pfds = pipe()
status = 0

def sigchld(signum, frame):
    global status

    cpid, status = os.wait()
    if cpid == pid:
        write_all(pfds[1], b"x")

resize_cb = lambda: None

def on_resize(resize_func):
    global resize_cb
    resize_cb = resize_func

def sigwinch(signum, frame):
    cols, rows = os.get_terminal_size()
    resize_cb(rows, cols)
    print("SIGWINCH", file=sys.stderr)
    write_all(pfds[1], b"r")

signal.signal(signal.SIGCHLD, sigchld)
signal.signal(signal.SIGWINCH, sigwinch)

def cleanup():
    os.close(child_fd)
    return os.waitstatus_to_exitcode(status)

#sys.exit(cleanup())
