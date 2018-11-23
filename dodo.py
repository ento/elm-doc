import sys
import os.path
from tempfile import TemporaryDirectory
import tarfile
import subprocess
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from elm_doc import elm_platform, elm_project
from tests import conftest


def task_create_elm_core_fixture():
    elm_core_fixture_path = conftest.elm_core_fixture_path()
    elm_versions = ['0.19.0']
    for elm_version in elm_versions:
        tarball = str(elm_core_fixture_path(elm_version))
        yield {
            'basename': 'create_elm_core_fixutre:' + elm_version,
            'actions': [(create_elm_core_fixture, (elm_version, tarball))],
            'targets': [tarball],
            'uptodate': [True],
        }


def create_elm_core_fixture(elm_version: str, tarball: str):
    os.makedirs(os.path.dirname(tarball), exist_ok=True)
    workspace_path = Path(__file__).parent / 'workspace'
    # clear elm-stuff because something in there causes CORRUPT BINARY
    # if you run 'elm make' with a different ELM_HOME
    shutil.rmtree(workspace_path / elm_project.STUFF_DIRECTORY)
    with TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        elm_platform.install(root_path, elm_version)
        elm_path = root_path / 'node_modules' / '.bin' / 'elm'
        elm_home_path = root_path / '.elm'
        try:
            subprocess.run(
                [elm_path, 'make', workspace_path / 'src' / 'Main.elm'],
                env=dict(os.environ, **{'ELM_HOME': str(elm_home_path)}),
                cwd=workspace_path,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            print('\nSTDOUT:\n' + e.stdout.decode('utf8'))
            print('\nSTDERR:\n' + e.stderr.decode('utf8'))
            raise e

        with tarfile.open(tarball, "w:gz") as tar:
            tar.add(str(elm_home_path), arcname=elm_home_path.name)
