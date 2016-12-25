import os.path
from tempfile import TemporaryDirectory
import tarfile
import json
import subprocess

import conftest


def task_create_elm_stuff_fixture():
    elm_stuff_fixture_path = conftest.elm_stuff_fixture_path()
    elm_versions = ['0.18.0']
    for elm_version in elm_versions:
        tarball = str(elm_stuff_fixture_path(elm_version))
        yield {
            'basename': 'create_elm_stuff_fixutre:' + elm_version,
            'actions': [(create_elm_stuff_fixture, (elm_version, tarball))],
            'targets': [tarball],
        }


def create_elm_stuff_fixture(elm_version, tarball):
    os.makedirs(os.path.dirname(tarball), exist_ok=True)
    with TemporaryDirectory() as tmpdir:
        npm_package = {'dependencies': {'elm': elm_version}}
        with open(os.path.join(tmpdir, 'package.json'), 'w') as f:
            json.dump(npm_package, f)
        subprocess.check_call(['yarn', 'install'], cwd=tmpdir)
        subprocess.check_call(['./node_modules/.bin/elm-package', 'install', '--yes'], cwd=tmpdir)
        elm_stuff = os.path.join(tmpdir, 'elm-stuff')
        with tarfile.open(tarball, "w:gz") as tar:
            tar.add(elm_stuff, arcname=os.path.basename(elm_stuff))
