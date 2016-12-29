import os
import os.path
import json
import tarfile

import pytest
import py

import elm_doc


@pytest.fixture(scope='session')
def overlayer():
    elm_doc.__path__.append(os.path.normpath(os.path.dirname(__file__)))


@pytest.fixture
def elm_stuff_fixture_path():
    def for_version(elm_version):
        filename = '{}-core-elm-stuff.tar.gz'.format(elm_version)
        return py.path.local(__file__).dirpath('tests', 'fixtures', filename)
    return for_version


@pytest.fixture
def module_fixture_path():
    def for_version(elm_version):
        return py.path.local(__file__).dirpath('tests', 'fixtures', elm_version)
    return for_version


@pytest.fixture
def make_elm_project(elm_stuff_fixture_path, module_fixture_path):
    def for_version(elm_version, root_dir, package_overrides={}, copy_elm_stuff=False, modules=[]):
        elm_package = dict(default_elm_package, **package_overrides)
        elm_package['elm-version'] = '{v} <= v <= {v}'.format(v=elm_version)
        root_dir.join('elm-package.json').write(json.dumps(elm_package))
        if copy_elm_stuff:
            with root_dir.as_cwd():
                with tarfile.open(elm_stuff_fixture_path(elm_version)) as tar:
                    tar.extractall()

        module_root = module_fixture_path(elm_version)
        for module in modules:
            root_dir.join(module).write(module_root.join(module).read())

    return for_version


default_elm_package = {
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
