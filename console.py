#!/usr/bin/env python3

import sys

import terminal

filename = None
if len(sys.argv) == 2:
    filename = sys.argv[1]

term = terminal.Terminal(filename=filename)

while True:
    term.render()

    if not term.handle(term.key()):
        break

term.close()

