#!/usr/bin/env python3

import sys

import terminal

filename = None
if len(sys.argv) == 2:
    filename = sys.argv[1]

term = terminal.Terminal(filename=filename)

def cycle():
    term.render()

    return term.handle(term.key())

term.Run(cycle)
