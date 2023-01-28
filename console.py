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
    term.render()

    return shell.run(in_cb, out_cb)

term.Run(cycle)

shell.cleanup()
