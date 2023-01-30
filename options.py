"""Console - a less surprising terminal experience.

Usage:
  console.py [-d] [FILE]

Options:
  -h --help     Show this help output.
  --version     Show version.
  -d --debug    Debug mode. (Log to stderr).

"""
import docopt

import debug

parsed = docopt.docopt(__doc__, version="Console 0.1")

debug.on(parsed.pop("--debug", False))
