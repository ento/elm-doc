import functools
import subprocess

from doit.exceptions import TaskFailed, TaskError


def capture_subprocess_error_as_task_failure(fn):
    return _wrap_subprocess_call(fn, TaskFailed)


def capture_subprocess_error_as_task_error(fn):
    return _wrap_subprocess_call(fn, TaskError)


def _wrap_subprocess_call(fn, exception_class):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            command_string = e.cmd if isinstance(e.cmd, str) else ' '.join(e.cmd)
            return exception_class(
                'Error while executing {}:\nstdout:\n{}\n\nstderr:\n{}'.format(
                    command_string,
                    e.stdout.decode('utf8') if e.stdout else '',
                    e.stderr.decode('utf8') if e.stderr else ''))
    return wrapper
