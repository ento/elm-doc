from typing import Dict, List, Iterator, Optional
from pathlib import Path
import fnmatch
import itertools
import json
import urllib.parse

import attr

from elm_doc import elm_platform


ModuleName = str
STUFF_DIRECTORY = 'elm-stuff'


@attr.s(auto_attribs=True)
class ElmProject:
    path: Path
    elm_version: str
    source_directories: [str]

    @property
    def json_path(self) -> Path:
        return self.path / self.DESCRIPTION_FILENAME

    @property
    def name(self) -> str:
        return '{}/{}'.format(self.user, self.project)

    def iter_dependencies(self) -> Iterator['ElmPackage']:
        raise NotImplementedError


@attr.s(auto_attribs=True)
class ElmPackage(ElmProject):
    user: str
    project: str
    version: str
    summary: str
    repository: str
    license: str
    exposed_modules: [str]
    dependencies: Dict[str, str]


class Elm18Package(ElmPackage):
    DESCRIPTION_FILENAME = 'elm-package.json'
    EXACT_DEPS_FILENAME = 'exact-dependencies.json'
    PACKAGES_DIRECTORY = 'packages'

    @classmethod
    def from_path(cls, path: Path) -> Optional['Elm18Package']:
        json_path = path / cls.DESCRIPTION_FILENAME
        if not json_path.exists():
            return
        description = _load_json(json_path)
        repo_path = Path(urllib.parse.urlparse(description['repository']).path)
        user = repo_path.parent.stem
        project = repo_path.stem
        return cls(
            path=path,
            user=user,
            project=project,
            version=description['version'],
            summary=description['summary'],
            repository=description['repository'],
            license=description['license'],
            source_directories=description['source-directories'],
            exposed_modules=description['exposed-modules'],
            dependencies=description['dependencies'],
            elm_version=description['elm-version'],
        )

    def as_json(self):
        fields = [
            ('version', 'version'),
            ('summary', 'summary'),
            ('repository', 'repository'),
            ('license', 'license'),
            ('source-directories', 'source_directories'),
            ('exposed-modules', 'exposed_modules'),
            ('dependencies', 'dependencies'),
            ('elm-version', 'elm_version'),
        ]
        return {json_prop: getattr(self, attr) for json_prop, attr in fields}

    def iter_dependencies(self) -> Iterator[ElmPackage]:
        exact_deps_path = self.path / STUFF_DIRECTORY / self.EXACT_DEPS_FILENAME
        exact_deps = {}
        try:
            with open(str(exact_deps_path)) as f:
                exact_deps = json.load(f)
        except OSError:
            # todo: warn about missing exact deps
            pass
        for name, version in exact_deps.items():
            yield from_path(self.path / STUFF_DIRECTORY / self.PACKAGES_DIRECTORY / name / version)


@attr.s(auto_attribs=True)
class ElmApplication(ElmProject):
    DESCRIPTION_FILENAME = 'elm.json'
    PACKAGES_DIRECTORY = 'package'

    direct_dependencies: Dict[str, str]
    indirect_dependencies: Dict[str, str]
    direct_test_dependencies: Dict[str, str]
    indirect_test_dependencies: Dict[str, str]

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

    def as_json(self):
        json = {
            'type': 'application',
            'name': self.name,
            'source-directories': self.source_directories,
            'elm-version': self.elm_version,
        }

        if self.direct_dependencies or self.indirect_dependencies:
            json['dependencies'] = {}
            if self.direct_dependencies:
                json['dependencies']['direct'] = self.direct_dependencies
            if self.indirect_dependencies:
                json['dependencies']['indirect'] = self.indirect_dependencies

        if self.direct_test_dependencies or self.indirect_test_dependencies:
            json['test-dependencies'] = {}
            if self.direct_test_dependencies:
                json['test-dependencies']['direct'] = self.direct_test_dependencies
            if self.indirect_test_dependencies:
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


def from_path(path: Path) -> ElmProject:
    # todo: Elm19Package
    classes = [
        Elm18Package,
        ElmApplication,
    ]
    for cls in classes:
        project = cls.from_path(path)
        if project:
            return project


def _load_json(path: Path) -> Dict:
    with open(str(path)) as f:
        return json.load(f)


@attr.s(auto_attribs=True)
class ProjectConfig:
    include_paths: List[str] = attr.Factory(list)
    exclude_modules: List[str] = attr.Factory(list)
    force_exclusion: bool = False


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
