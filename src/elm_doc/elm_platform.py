import os
import subprocess
from pathlib import Path
import json

from elm_doc import node_modules
from elm_doc.decorators import capture_subprocess_error


# See: https://github.com/elm/compiler/blob/0.19.0/builder/src/Elm/PerUserCache.hs#L44
# Note: this implementation is not exactly the same as the above, which uses
# getAppUserDataDirectory:
# http://hackage.haskell.org/package/directory-1.3.3.1/docs/System-Directory.html#v:getAppUserDataDirectory
# On Windows, this is something like 'C:/Users/<user>/AppData/Roaming/<app>'.
# elm-doc currently don't support Windows, so this is fine for now.
ELM_HOME = Path(os.environ['ELM_HOME']) if 'ELM_HOME' in os.environ else (Path.home() / '.elm')


def install(to: Path, elm_version: str):
    npm_package = {
        'dependencies': {
            'elm': get_npm_version_range(elm_version)
        }
    }
    with open(str(to / 'package.json'), 'w') as f:
        json.dump(npm_package, f)
    node_modules.install(cwd=str(to))


@capture_subprocess_error
def get_node_modules_elm_path(project_root: Path):
    script = 'console.log(require.resolve("elm"))'
    # e.g. path/to/node_modules/elm/index.js
    elm_index_path = subprocess.check_output(
        ['node', '-e', script],
        cwd=str(project_root),
    )
    # e.g. path/to/node_modules/elm/unpacked_bin/elm
    return Path(elm_index_path.decode('utf-8').strip()).parent / 'unpacked_bin' / 'elm'


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
