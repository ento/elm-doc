import subprocess
from pathlib import Path
import json


def install(to: Path, elm_version: str):
    npm_package = {
        'dependencies': {
            'elm': elm_version
        }
    }
    with open(to / 'package.json', 'w') as f:
        json.dump(npm_package, f)
    subprocess.check_call(['yarn', 'install'], cwd=to)
