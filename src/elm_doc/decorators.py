import functools
import subprocess

from doit.exceptions import TaskFailed


def capture_subprocess_error(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            return TaskFailed('Error while executing {}'.format(' '.join(e.cmd)))
    return wrapper
