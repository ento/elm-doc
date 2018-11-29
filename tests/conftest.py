import os
import os.path
import json
from pathlib import Path
import tarfile

import pytest
import py


def pytest_addoption(parser):
    parser.addoption("--elm-version", default='0.19.0',
                     help="specify the version of Elm to test")


def pytest_generate_tests(metafunc):
    if 'elm_version' in metafunc.fixturenames:
        metafunc.parametrize("elm_version", [metafunc.config.getoption('elm_version')])


@pytest.fixture
def elm_stuff_fixture_path():
    def for_version(elm_version):
        filename = '{}-core-elm-stuff.tar.gz'.format(elm_version)
        return py.path.local(__file__).dirpath('fixtures', filename)
    return for_version


@pytest.fixture
def elm_core_fixture_path():
    def for_version(elm_version):
        filename = '{}-elm-core.tar.gz'.format(elm_version)
        return py.path.local(__file__).dirpath('fixtures', filename)
    return for_version


@pytest.fixture
def module_fixture_path():
    def for_version(elm_version):
        return py.path.local(__file__).dirpath('fixtures', elm_version)
    return for_version


@pytest.fixture
def make_elm_project(mocker, elm_stuff_fixture_path, elm_core_fixture_path, module_fixture_path):
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
                tarball = elm_stuff_fixture_path(elm_version)
                _extract_tarball(tarball, project_dir)
            else:
                tarball = elm_core_fixture_path(elm_version)
                _extract_tarball(tarball, root_dir)

        module_root = module_fixture_path(elm_version)
        for source_dir, modules in sources.items():
            project_dir.ensure(source_dir, dir=True)
            for module in modules:
                project_dir.join(source_dir, module).write(module_root.join(module).read())

        elm_home = str(root_dir.join('.elm'))
        mocker.patch('elm_doc.elm_platform.ELM_HOME', Path(elm_home))
        mocker.patch.dict(os.environ, {'ELM_HOME': elm_home})
        return project_dir

    return for_version


def _extract_tarball(tarball, dest):
    with dest.as_cwd():
        with tarfile.open(str(tarball)) as tar:
            tar.extractall()


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
