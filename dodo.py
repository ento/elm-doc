import sys
import os.path
from tempfile import TemporaryDirectory
import tarfile
import json
import subprocess
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from elm_doc import elm_platform, elm_project, tasks
from tests import conftest


def task_create_elm_core_fixture():
    elm_core_fixture_path = conftest.elm_core_fixture_path()
    elm_versions = ['0.19.0']
    for elm_version in elm_versions:
        tarball = str(elm_core_fixture_path(elm_version))
        yield {
            'basename': 'create_elm_core_fixture:' + elm_version,
            'actions': [(_create_elm_core_fixture, (elm_version, tarball))],
            'targets': [tarball],
            'uptodate': [True],
        }


def _create_elm_core_fixture(elm_version: str, tarball: str):
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


def task_create_package_elm_lang_org_artifact_tarball():
    tarball_path = Path(__file__).parent.joinpath('src', 'elm_doc', 'assets', 'assets.tar.gz')
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
        ],
        'targets': [tarball_path],
        'actions': [(_create_package_elm_lang_org_artifact_tarball, (tarball_path,))],
    }


def _create_package_elm_lang_org_artifact_tarball(output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    build_artifacts_path = Path(__file__).parent.joinpath('build', 'package.elm-lang.org', 'artifacts')
    vendor_assets_path = Path(__file__).parent.joinpath('vendor', 'package.elm-lang.org', 'assets')
    vendor_license_path = Path(__file__).parent.joinpath('vendor', 'package.elm-lang.org', 'LICENSE')
    with tarfile.open(output_path, "w:gz") as tar:
        tar.add(str(build_artifacts_path), arcname=build_artifacts_path.name)
        tar.add(str(vendor_assets_path), arcname=vendor_assets_path.name)
        tar.add(str(vendor_license_path), arcname='assets/LICENSE')
        tar.add(str(vendor_license_path), arcname='artifacts/LICENSE')


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
    with open(elm_json_path) as f:
        elm_json = json.load(f)
    return elm_json['elm-version']


def _create_package_elm_lang_org_elm_js(output_path: Path):
    repo_path = Path(__file__).parent / 'vendor' / 'package.elm-lang.org'
    elm_version = _read_elm_version(repo_path / 'elm.json')
    with TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        elm_platform.install(root_path, elm_version)
        elm_path = root_path / 'node_modules' / '.bin' / 'elm'
        try:
            subprocess.run(
                [
                    elm_path,
                    'make',
                    repo_path / 'src' / 'frontend' / 'Main.elm',
                    '--output',
                    str(output_path),
                ],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            print('\nSTDOUT:\n' + e.stdout.decode('utf8'))
            print('\nSTDERR:\n' + e.stderr.decode('utf8'))
            raise e


workspace_path = Path(__file__).parent / 'workspace'
output_path = workspace_path / 'build' / 'docs'
elm_path = workspace_path / 'node_modules' / '.bin' / 'elm'
config = elm_project.ProjectConfig()


def task_build_workspace_docs():
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
