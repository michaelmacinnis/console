#!/usr/bin/env python3

import fcntl
import os
import select
import sys
import tty

def log(*args):
  print(*args, file=sys.stderr)

def nonblocking(fd):
  fl = fcntl.fcntl(fd, fcntl.F_GETFL)
  fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

def raw(fd):
    prev = tty.tcgetattr(fd)

    tty.setraw(fd)

    return lambda : tty.tcsetattr(fd, tty.TCSADRAIN, prev)

def read(fd, n=65536):
  try:
    b = os.read(fd, n)
    if len(b) == 0:
        return None
    return b
  except BlockingIOError:
    return ''
  except OSError:
    return None

def write(fd, b):
  while b:
    n = os.write(fd, b)
    b = b[n:]

def launch():
  try:
    child_pid, fd = os.forkpty()
  except OSError as ex:
    print(str(ex))
    return 255 # TODO: Replace with correct status code.

  if child_pid == 0:
    try:
      #os.execlp("cat", "cat", "-v")
      os.execlp("/home/michael/Workspace/oh/oh", "oh")
    except Exception as ex:
      log("cannot launch oh", ex)
      sys.exit(255) # TODO: Replace with correct status code.
  else:
    print("In Parent Process: PID# %s" % os.getpid())

    nonblocking(fd)

    stdin = sys.stdin.fileno()
    restore = raw(stdin)
    nonblocking(stdin)

    while True:
      select.select([fd, stdin], [], [])

      prompt = read(fd)
      while prompt:
        write(1, prompt)
        prompt = read(fd)

      if prompt is None:
        break

      command = read(stdin)
      while command:
        write(fd, command)
        command = read(stdin)

      if command is None:
        os.close(fd)
        write(1, b"\r\n")
        break

    _, status = os.waitpid(child_pid, 0)

    restore()

    return status

if __name__ == "__main__":
    sys.exit(launch())
