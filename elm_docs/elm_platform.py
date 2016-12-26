import subprocess
from pathlib import Path
import json


def install(to: Path, elm_version: str):
    npm_package = {
        'dependencies': {
            'elm': get_npm_version_range(elm_version)
        }
    }
    with open(to / 'package.json', 'w') as f:
        json.dump(npm_package, f)
    subprocess.check_call(['yarn', 'install'], cwd=to)


def get_npm_version_range(elm_version: str) -> str:
    if _is_exact(elm_version):
        return elm_version
    min_version, gt_op, _, lt_op, max_version = elm_version.split(' ')
    return '{gt_op}{min_version} {lt_op}{max_version}'.format(
        min_version=min_version,
        gt_op=_flip_inequality_op(gt_op),
        lt_op=lt_op,
        max_version=max_version,
    )


def _is_exact(elm_version: str) -> bool:
    return ' ' not in elm_version


def _flip_inequality_op(op: str) -> str:
    # assume there's only one < or >
    return op.replace('>', '<').replace('<', '>')
