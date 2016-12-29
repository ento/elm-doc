import os.path
from tempfile import TemporaryDirectory
import tarfile
import subprocess
from pathlib import Path

import conftest
from elm_doc import elm_platform, elm_package


def task_create_elm_stuff_fixture():
    elm_stuff_fixture_path = conftest.elm_stuff_fixture_path()
    elm_versions = ['0.18.0']
    for elm_version in elm_versions:
        tarball = str(elm_stuff_fixture_path(elm_version))
        yield {
            'basename': 'create_elm_stuff_fixutre:' + elm_version,
            'actions': [(create_elm_stuff_fixture, (elm_version, tarball))],
            'targets': [tarball],
            'uptodate': [True],
        }


def create_elm_stuff_fixture(elm_version: str, tarball: str):
    os.makedirs(os.path.dirname(tarball), exist_ok=True)
    with TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        elm_platform.install(root_path, elm_version)
        subprocess.check_call(['./node_modules/.bin/elm-package', 'install', '--yes'], cwd=root_path)
        elm_stuff = root_path / elm_package.STUFF_DIRECTORY
        with tarfile.open(tarball, "w:gz") as tar:
            tar.add(elm_stuff, arcname=os.path.basename(elm_stuff))
