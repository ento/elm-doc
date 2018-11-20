from typing import Dict, List, Iterator, Optional, Union
from pathlib import Path
import fnmatch
import itertools
import json
import urllib.parse

import attr

from elm_doc import elm_platform


ModuleName = str
ExactVersion = str
VersionRange = str
STUFF_DIRECTORY = 'elm-stuff'


@attr.s(auto_attribs=True)
class ElmProject:
    path: Path

    @property
    def json_path(self) -> Path:
        return self.path / self.DESCRIPTION_FILENAME

    def iter_dependencies(self) -> Iterator['ElmPackage']:
        raise NotImplementedError


@attr.s(auto_attribs=True)
class ElmPackage(ElmProject):
    DESCRIPTION_FILENAME = 'elm.json'
    PACKAGES_DIRECTORY = 'packages'

    user: str
    project: str
    version: str
    summary: str
    license: str
    elm_version: VersionRange
    exposed_modules: Union[List[ModuleName], Dict[str, List[ModuleName]]]
    dependencies: Dict[str, VersionRange]
    test_dependencies: Dict[str, VersionRange]

    @classmethod
    def from_path(cls, path: Path) -> Optional['ElmPackage']:
        json_path = path / cls.DESCRIPTION_FILENAME
        if not json_path.exists():
            return

        description = _load_json(json_path)
        if description['type'] != 'package':
            return

        name_parts = description['name'].split('/')
        return cls(
            path=path,
            user=name_parts[0],
            project=name_parts[1],
            version=description['version'],
            summary=description['summary'],
            license=description['license'],
            exposed_modules=description['exposed-modules'],
            dependencies=description['dependencies'],
            test_dependencies=description['test-dependencies'],
            elm_version=description['elm-version'],
        )

    @property
    def name(self) -> str:
        return '{}/{}'.format(self.user, self.project)

    def as_package(self, config):
        return self

    def as_json(self):
        fields = [
            ('name', 'name'),
            ('version', 'version'),
            ('summary', 'summary'),
            ('license', 'license'),
            ('exposed-modules', 'exposed_modules'),
            ('dependencies', 'dependencies'),
            ('test-dependencies', 'test_dependencies'),
            ('elm-version', 'elm_version'),
        ]
        props = {json_prop: getattr(self, attr) for json_prop, attr in fields}
        props['type'] = 'package'
        return props


@attr.s(auto_attribs=True)
class ElmApplication(ElmProject):
    DESCRIPTION_FILENAME = 'elm.json'
    PACKAGES_DIRECTORY = 'package'

    source_directories: [str]
    elm_version: ExactVersion
    direct_dependencies: Dict[str, ExactVersion]
    indirect_dependencies: Dict[str, ExactVersion]
    direct_test_dependencies: Dict[str, ExactVersion]
    indirect_test_dependencies: Dict[str, ExactVersion]

    @classmethod
    def from_path(cls, path: Path) -> Optional['ElmApplication']:
        json_path = path / cls.DESCRIPTION_FILENAME
        if not json_path.exists():
            return

        description = _load_json(json_path)
        if description['type'] != 'application':
            return

        return cls(
            path=path,
            source_directories=description['source-directories'],
            elm_version=description['elm-version'],
            direct_dependencies=description['dependencies'].get('direct', {}),
            indirect_dependencies=description['dependencies'].get('indirect', {}),
            direct_test_dependencies=description['test-dependencies'].get('direct', {}),
            indirect_test_dependencies=description['test-dependencies'].get('indirect', {}),
        )

    def as_package(self, overrides: 'ProjectConfig') -> 'ElmPackage':
        return ElmPackage(
            path=self.path,
            user=overrides.fake_user,
            project=overrides.fake_project,
            version=overrides.fake_version,
            summary=overrides.fake_summary,
            license=overrides.fake_license,
            exposed_modules=[],
            dependencies=_as_package_dependencies(
                self.direct_dependencies, self.indirect_dependencies),
            test_dependencies=_as_package_dependencies(
                self.direct_test_dependencies, self.indirect_test_dependencies),
            elm_version=_as_version_range(self.elm_version),
        )

    def as_json(self):
        json = {
            'type': 'application',
            'source-directories': self.source_directories,
            'elm-version': self.elm_version,
        }

        json['dependencies'] = {}
        json['dependencies']['direct'] = self.direct_dependencies
        json['dependencies']['indirect'] = self.indirect_dependencies

        json['test-dependencies'] = {}
        json['test-dependencies']['direct'] = self.direct_test_dependencies
        json['test-dependencies']['indirect'] = self.indirect_test_dependencies

        return json

    def iter_dependencies(self) -> Iterator[ElmPackage]:
        deps = itertools.chain(
            self.direct_dependencies.items(),
            self.indirect_dependencies.items(),
            self.direct_test_dependencies.items(),
            self.indirect_test_dependencies.items(),
        )
        for name, version in deps:
            # e.g. ~/.elm/0.19.0/package/elm/core/1.0.0
            yield from_path(elm_platform.ELM_HOME / self.elm_version / self.PACKAGES_DIRECTORY / name / version)


def _as_package_dependencies(*app_dependencies: Dict[str, ExactVersion]) -> Dict[str, VersionRange]:
    package_deps = {}
    for app_deps in app_dependencies:
        for package_name, exact_version in app_deps.items():
            package_deps[package_name] = _as_version_range(exact_version)
    return package_deps


def _as_version_range(exact_version: ExactVersion) -> VersionRange:
    major, minor, patch = exact_version.split('.')
    next_version = '{}.{}.{}'.format(major, minor, int(patch, 10) + 1)
    return '{} <= v < {}'.format(exact_version, next_version)


def from_path(path: Path) -> ElmProject:
    classes = [
        ElmApplication,
        ElmPackage,
    ]
    for cls in classes:
        project = cls.from_path(path)
        if project:
            return project
    raise Exception('{} does not look like an Elm project'.format(path))


def _load_json(path: Path) -> Dict:
    with open(str(path)) as f:
        return json.load(f)


@attr.s(auto_attribs=True)
class ProjectConfig:
    include_paths: List[str] = attr.Factory(list)
    exclude_modules: List[str] = attr.Factory(list)
    force_exclusion: bool = False
    fake_user: str = 'author'
    fake_project: str = 'project'
    fake_version: str = '1.0.0'
    fake_summary: str = 'summary'
    fake_license: str = 'BSD-3-Clause'


def glob_project_modules(
        project: ElmProject, config: ProjectConfig) -> Iterator[ModuleName]:
    for source_dir_name in project.source_directories:
        source_dir = project.path / source_dir_name
        elm_files = source_dir.glob('**/*.elm')
        for elm_file in elm_files:
            if elm_file.relative_to(project.path).parts[0] == STUFF_DIRECTORY:
                continue

            if config.include_paths and not any(_matches_include_path(elm_file, include_path)
                                         for include_path in config.include_paths):
                continue

            rel_path = elm_file.relative_to(source_dir)
            module_name = '.'.join(rel_path.parent.parts + (rel_path.stem,))

            # check for excludes if there's no explicit includes, or if
            # there are explicit includes and exclusion is requested specifically.
            check_excludes = (not config.include_paths) or config.force_exclusion
            if check_excludes and any(fnmatch.fnmatch(module_name, module_pattern)
                                      for module_pattern in config.exclude_modules):
                continue

            yield module_name


def _matches_include_path(source_path: Path, include_path: Path):
    try:
        source_path.relative_to(include_path)
    except ValueError:
        return False
    else:
        return True
