#!/usr/bin/env python3

import sys

import shell
import terminal

filename = None
if len(sys.argv) == 2:
    filename = sys.argv[1]

term = terminal.Terminal(filename=filename)

def in_cb(fd):
    res = term.handle(term.key())
    if res:
        cmd = term.cmd()
        if cmd:
            shell.write_all(fd, cmd.encode('utf-8'))
            shell.write_all(fd, b"\n")
    return res

def out_cb(data):
    term.append(data)

def cycle():
    if shell.canonical:
        term.render()

    return shell.run(in_cb, out_cb)

shell.on_resize(terminal.resize)

term.Run(shell.resize, cycle)

shell.cleanup()
