import sys


logging = True


def log(*args, **kwargs):
    if not logging:
        return

    kwargs["file"] = sys.stderr
    kwargs["flush"] = True

    print(*args, **kwargs)


def on(flag=True):
    global logging
    logging = flag
