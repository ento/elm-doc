import sys
import functools
import subprocess


def print_subprocess_error(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            print(e.output, file=sys.stderr)
            raise
    return wrapper
