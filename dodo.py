from typing import Dict
import sys
import os.path
import io
import contextlib
import logging
from tempfile import TemporaryDirectory
import tarfile
import gzip
import hashlib
import json
import subprocess
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from elm_doc import elm_platform, elm_project, tasks
from tests import conftest


logger = logging.getLogger(__name__)


def task_create_elm_core_fixture():
    workspace_path = Path(__file__).parent / 'workspace'
    elm_versions = ['0.19.0']
    for elm_version in elm_versions:
        build_tarball_path = Path(__file__).parent / 'build' / 'elm-core-fixture-{}.tar.gz'.format(elm_version)
        dist_tarball_path = Path(str(conftest.elm_core_fixture_path(elm_version)))
        yield {
            'basename': 'create_elm_core_fixture',
            'name': elm_version,
            'actions': [
                (_create_elm_core_fixture, (elm_version, build_tarball_path)),
                (_copy_if_tarball_changed, (build_tarball_path, dist_tarball_path)),
            ],
            'targets': [dist_tarball_path],
            'file_dep': [workspace_path / 'elm.json'],
        }


def _create_elm_core_fixture(elm_version: str, tarball: str):
    tarball.parent.mkdir(parents=True, exist_ok=True)
    workspace_path = Path(__file__).parent / 'workspace'
    # clear elm-stuff because something in there causes CORRUPT BINARY
    # if you run 'elm make' with a different ELM_HOME
    shutil.rmtree(str(workspace_path / elm_project.STUFF_DIRECTORY), ignore_errors=True)
    with TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        elm_path = elm_platform.install(root_path, elm_version)
        elm_home_path = root_path / '.elm'
        try:
            subprocess.check_output(
                [str(elm_path), 'make', str(workspace_path / 'src' / 'Main.elm')],
                env=dict(os.environ, **{'ELM_HOME': str(elm_home_path)}),
                cwd=str(workspace_path),
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            print('\nSTDOUT:\n' + e.stdout.decode('utf8'))
            print('\nSTDERR:\n' + e.stderr.decode('utf8'))
            raise e

        with _create_tarball(tarball) as tar:
            tar.add(str(elm_home_path), arcname=elm_home_path.name, filter=_tar_filter_without_registry)


def _tar_filter_without_registry(tarinfo):
    if Path(tarinfo.name).name == 'versions.dat':
        return
    return tarinfo


def task_create_package_elm_lang_org_artifact_tarball():
    build_tarball_path = Path(__file__).parent.joinpath('build', 'assets.tar.gz')
    dist_tarball_path = Path(__file__).parent.joinpath('src', 'elm_doc', 'assets', 'assets.tar.gz')
    return {
        'file_dep': [
            'build/package.elm-lang.org/artifacts/elm.js',
            'vendor/package.elm-lang.org/assets/favicon.ico',
            'vendor/package.elm-lang.org/assets/highlight/highlight.pack.js',
            'vendor/package.elm-lang.org/assets/highlight/LICENSE',
            'vendor/package.elm-lang.org/assets/highlight/styles/default.css',
            'vendor/package.elm-lang.org/assets/style.css',
            'vendor/package.elm-lang.org/assets/help/documentation-format.md',
            'vendor/package.elm-lang.org/assets/help/design-guidelines.md',
            'vendor/package.elm-lang.org/LICENSE',
        ],
        'targets': [dist_tarball_path],
        'actions': [
            (_create_package_elm_lang_org_artifact_tarball, (build_tarball_path,)),
            (_copy_if_tarball_changed, (build_tarball_path, dist_tarball_path)),
        ],
    }


def _copy_if_tarball_changed(source_path: Path, target_path: Path):
    if _is_tarball_different(source_path, target_path):
        shutil.copyfile(str(source_path), str(target_path))


def _is_tarball_different(source_path: Path, target_path: Path) -> bool:
    if not target_path.exists():
        return True
    source_md5s = _get_tarball_md5s(source_path)
    target_md5s = _get_tarball_md5s(target_path)
    if source_md5s != target_md5s:
        for name in (set(source_md5s.keys()) | set(target_md5s.keys())):
            if source_md5s.get(name) != target_md5s.get(name):
                logger.info('hash of {} differ between {} and {}'.format(name, source_path, target_path))
        return True
    return False


def _get_tarball_md5s(path: Path) -> Dict[str, str]:
    res = {}
    with tarfile.open(str(path), 'r') as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            f = tar.extractfile(member)
            md5 = hashlib.md5()
            block_size = 128 * md5.block_size
            while True:
                data = f.read(block_size)
                if not data:
                    break
                md5.update(data)
            res[member.name] = md5.hexdigest()
    return res


def _create_package_elm_lang_org_artifact_tarball(output_path: Path):
    build_artifacts_path = Path(__file__).parent.joinpath('build', 'package.elm-lang.org', 'artifacts')
    vendor_assets_path = Path(__file__).parent.joinpath('vendor', 'package.elm-lang.org', 'assets')
    vendor_license_path = Path(__file__).parent.joinpath('vendor', 'package.elm-lang.org', 'LICENSE')
    with _create_tarball(output_path) as tar:
        tar.add(str(build_artifacts_path), arcname=build_artifacts_path.name)
        tar.add(str(vendor_assets_path), arcname=vendor_assets_path.name)
        tar.add(str(vendor_license_path), arcname='assets/LICENSE')
        tar.add(str(vendor_license_path), arcname='artifacts/LICENSE')


@contextlib.contextmanager
def _create_tarball(output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tar_bytes = io.BytesIO()
    with tarfile.open(fileobj=tar_bytes, mode="w") as tar:
        yield tar
    tar_bytes.seek(0)
    # Hardcode filename and mtime so that the output is deterministic
    # as much as possible.  This is equivalent to doing `tar .. | gzip
    # -n` on the command line.  We *could* strip mtime from the
    # tarball entries as well, but having that information included
    # may be useful for debugging in the future, so we avoid updating
    # the tarball by checking the md5 of the contents above instead.
    with open(str(output_path), 'wb') as f:
        with gzip.GzipFile(filename='', mode='wb', fileobj=f, mtime=0) as z:
            z.write(tar_bytes.read())


def task_package_elm_lang_org_elm_js():
    root_path = Path(__file__).parent.joinpath('vendor', 'package.elm-lang.org')
    output_path = Path(__file__).parent.joinpath('build', 'package.elm-lang.org', 'artifacts', 'elm.js')
    return {
        'file_dep': list(root_path.joinpath('src/frontend').glob('**/*.elm')) + [root_path / 'elm.json'],
        'targets': [
            'build/package.elm-lang.org/artifacts/elm.js',
        ],
        'actions': [(_create_package_elm_lang_org_elm_js, (output_path,))]
    }


def _read_elm_version(elm_json_path: Path) -> str:
    elm_json = json.loads(elm_json_path.read_text('utf8'))
    return elm_json['elm-version']


def _create_package_elm_lang_org_elm_js(output_path: Path):
    repo_path = Path(__file__).parent / 'vendor' / 'package.elm-lang.org'
    elm_version = _read_elm_version(repo_path / 'elm.json')
    with TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        elm_path = elm_platform.install(root_path, elm_version)
        try:
            subprocess.check_output(
                [
                    str(elm_path),
                    'make',
                    str(repo_path / 'src' / 'frontend' / 'Main.elm'),
                    '--output',
                    str(output_path),
                ],
                cwd=str(repo_path),
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            print('\nSTDOUT:\n' + e.stdout.decode('utf8'))
            print('\nSTDERR:\n' + e.stderr.decode('utf8'))
            raise e

# build docs for the workspace project

workspace_path = Path(__file__).parent / 'workspace'
output_path = workspace_path / 'build' / 'docs'
elm_path = workspace_path / 'node_modules' / '.bin' / 'elm'
config = elm_project.ProjectConfig()


def task_install_workspace_elm():
    yield {
        'name': 'install_elm',
        'file_dep': [workspace_path / 'elm.json'],
        'targets': [elm_path],
        'actions': [(_install_elm, (workspace_path,))]
    }


def _install_elm(project_path: Path):
    elm_version = _read_elm_version(project_path / 'elm.json')
    elm_platform.install(project_path, elm_version)


for creator_name, creator_func in tasks.build_task_creators(
        workspace_path,
        config,
        output_path,
        elm_path=elm_path,
        mount_point='/docs',
).items():
    globals()[creator_name] = creator_func
