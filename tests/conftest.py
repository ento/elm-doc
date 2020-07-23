import os
import os.path
import json
from pathlib import Path
import subprocess
import tarfile

import pytest
import py


def pytest_addoption(parser):
    parser.addoption("--elm-version", default='0.19.1',
                     help="specify the version of Elm to test")


def pytest_generate_tests(metafunc):
    if 'elm_version' in metafunc.fixturenames:
        metafunc.parametrize(
            "elm_version",
            [metafunc.config.getoption('elm_version')],
            scope='session')


def elm_stuff_fixture_path(elm_version):
    filename = '{}-core-elm-stuff.tar.gz'.format(elm_version)
    return py.path.local(__file__).dirpath('fixtures', filename)


def elm_core_fixture_path(elm_version):
    filename = '{}-elm-core.tar.gz'.format(elm_version)
    return py.path.local(__file__).dirpath('fixtures', filename)


# Helper function for use in tests
def install_elm(to: Path, elm_version: str) -> Path:
    npm_package = {
        'dependencies': {
            'elm': _get_npm_version(elm_version)
        }
    }
    with open(str(to / 'package.json'), 'w') as f:
        json.dump(npm_package, f)
    subprocess.check_call(('npm', 'install'), cwd=str(to))
    return to / 'node_modules' / '.bin' / 'elm'


def _get_npm_version(elm_version: str) -> str:
    if _is_exact(elm_version):
        if elm_version == '0.19.0':
            # use a version without graceful-fs, which can cause issues like
            # https://github.com/nodejs/node/issues/32799
            return '{v}-no-deps'.format(v=elm_version)
        return 'latest-{v}'.format(v=elm_version)
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


@pytest.fixture
def fixture_path():
    return py.path.local(__file__).dirpath('fixtures')


@pytest.fixture
def module_fixture_path(elm_version):
    return py.path.local(__file__).dirpath('fixtures', elm_version)


@pytest.fixture
def mock_popular_packages(mocker):
    mocker.patch('elm_doc.tasks.catalog.missing_popular_packages', return_value=[])


@pytest.fixture(scope='session')
def elm(tmpdir_factory, elm_version):
    tmpdir = tmpdir_factory.mktemp('elm-{}'.format(elm_version))
    return str(install_elm(Path(str(tmpdir)), elm_version))


@pytest.fixture
def make_elm_project(mocker, module_fixture_path):
    def for_version(elm_version, root_dir, sources={}, package_overrides={}, copy_elm_stuff=False):
        '''
        :param elm_version: Version of Elm to specify in elm.json
        :param root_dir: Directory to create an Elm project in
        :param sources: A mapping of source directory relative to root_dir to source files to copy
                        from tests/fixtures/{elm_version}/
        :param package_overrides: Properties to override in the generated elm.json
        :param copy_elm_stuff: Whether to copy a cache of core Elm libraries
        '''
        root_dir.ensure('project', dir=True)
        project_dir = root_dir.join('project')
        source_dirs = list(sources.keys())
        elm_package = dict(default_elm_package[elm_version], **{'source-directories': source_dirs})
        elm_package.update(package_overrides)
        elm_package_filename = 'elm-package.json' if elm_version == '0.18.0' else 'elm.json'
        project_dir.join(elm_package_filename).write(json.dumps(elm_package))

        if copy_elm_stuff:
            if elm_version == '0.18.0':
                _extract_tarball(elm_stuff_fixture_path(elm_version), project_dir)
            else:
                _extract_tarball(elm_core_fixture_path(elm_version), root_dir)

        for source_dir, modules in sources.items():
            project_dir.ensure(source_dir, dir=True)
            for module in modules:
                project_dir.join(source_dir, module).write(module_fixture_path.join(module).read())

        elm_home = str(root_dir.join('.elm'))
        mocker.patch('elm_doc.elm_platform.ELM_HOME', Path(elm_home))
        mocker.patch.dict(os.environ, {'ELM_HOME': elm_home})
        return project_dir

    return for_version


def _extract_tarball(tarball, dest):
    with dest.as_cwd():
        with tarfile.open(str(tarball)) as tar:
            tar.extractall()


# How to add a new entry: run `elm init` or its equivalent and
# bring in the content of the elm-package.json/elm.json file that was created.
# Then set the source directory to `"."`.
default_elm_package = {}

default_elm_package['0.18.0'] = {
    "version": "1.0.0",
    "summary": "helpful summary of your project, less than 80 characters",
    "repository": "https://github.com/user/project.git",
    "license": "BSD3",
    "source-directories": [
        "."
    ],
    "exposed-modules": [],
    "dependencies": {
        "elm-lang/core": "5.0.0 <= v < 6.0.0",
        "elm-lang/html": "2.0.0 <= v < 3.0.0"
    },
    "elm-version": "0.18.0 <= v < 0.19.0"
}

default_elm_package['0.19.0'] = {
    "type": "application",
    "source-directories": [
        "."
    ],
    "elm-version": "0.19.0",
    "dependencies": {
        "direct": {
            "elm/core": "1.0.2",
            "elm/html": "1.0.0"
        },
        "indirect": {
            "elm/json": "1.1.2",
            "elm/virtual-dom": "1.0.2"
        }
    },
    "test-dependencies": {
        "direct": {},
        "indirect": {}
    }
}

default_elm_package['0.19.1'] = {
    "type": "application",
    "source-directories": [
        "."
    ],
    "elm-version": "0.19.1",
    "dependencies": {
        "direct": {
            "elm/browser": "1.0.2",
            "elm/core": "1.0.5",
            "elm/html": "1.0.0"
        },
        "indirect": {
            "elm/json": "1.1.3",
            "elm/time": "1.0.0",
            "elm/url": "1.0.0",
            "elm/virtual-dom": "1.0.2"
        }
    },
    "test-dependencies": {
        "direct": {},
        "indirect": {}
    }
}
