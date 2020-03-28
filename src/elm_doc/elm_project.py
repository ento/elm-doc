from typing import Dict, List, Iterator, Optional, Tuple
import os.path
from pathlib import Path
import re
import fnmatch
import itertools
import json

import attr
from click import BadParameter

from elm_doc import elm_platform


ModuleName = str
ExactVersion = str
VersionRange = str
STUFF_DIRECTORY = 'elm-stuff'
module_name_re = re.compile(r'^[A-Z][a-zA-Z0-9_]*$')


@attr.s
class ElmProject:
    DOCS_FILENAME = 'docs.json'

    path = attr.ib()

    @property
    def json_path(self) -> Path:
        return self.path / self.DESCRIPTION_FILENAME

    def iter_direct_dependencies(self) -> Iterator['ElmPackage']:
        raise NotImplementedError


@attr.s
class ElmPackage(ElmProject):
    DESCRIPTION_FILENAME = 'elm.json'
    PACKAGES_DIRECTORY = 'packages'

    user = attr.ib()  # str
    project = attr.ib()  # str
    version = attr.ib()  # str
    summary = attr.ib()  # str
    license = attr.ib()  # str
    elm_version = attr.ib()  # VersionRange
    exposed_modules = attr.ib()  # Union[List[ModuleName], Dict[str, List[ModuleName]]]
    dependencies = attr.ib()  # Dict[str, VersionRange]
    test_dependencies = attr.ib()  # Dict[str, VersionRange]

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

    def without_license(self) -> 'ElmPackage':
        asdict = attr.asdict(self)
        asdict['license'] = ''
        return ElmPackage(**asdict)

    def sorted_exposed_modules(self):
        if isinstance(self.exposed_modules, dict):
            modules = [module for modules in self.exposed_modules.values()
                       for module in modules]
        else:
            modules = list(self.exposed_modules)
        return sorted(modules)


@attr.s
class ElmApplication(ElmProject):
    DESCRIPTION_FILENAME = 'elm.json'
    PACKAGES_DIRECTORY = 'packages'

    source_directories = attr.ib()  # [str]
    elm_version = attr.ib()  # ExactVersion
    direct_dependencies = attr.ib()  # Dict[str, ExactVersion]
    indirect_dependencies = attr.ib()  # Dict[str, ExactVersion]
    direct_test_dependencies = attr.ib()  # Dict[str, ExactVersion]
    indirect_test_dependencies = attr.ib()  # Dict[str, ExactVersion]

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
                self.direct_dependencies),
            test_dependencies=_as_package_dependencies(
                self.direct_test_dependencies),
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

    def add_direct_dependencies(self, deps: List[Tuple[str, ExactVersion]]):
        for name, version in deps:
            self.direct_dependencies[name] = version

    def direct_dependency_names(self) -> Iterator[str]:
        return itertools.chain(
            self.direct_dependencies.keys(),
            self.direct_test_dependencies.keys(),
        )

    def iter_direct_dependencies(self) -> Iterator[ElmPackage]:
        deps = itertools.chain(
            self.direct_dependencies.items(),
            self.direct_test_dependencies.items(),
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
    raise BadParameter('{} does not look like an Elm project'.format(path))


def _load_json(path: Path) -> Dict:
    with open(str(path)) as f:
        return json.load(f)


@attr.s
class ProjectConfig:
    include_paths = attr.ib(factory=list)  # List[str]
    exclude_modules = attr.ib(factory=list)  # List[str]
    exclude_source_directories = attr.ib(factory=list)  # List[str]
    force_exclusion = attr.ib(default=False)  # bool
    fake_user = attr.ib(default='user')  # str
    fake_project = attr.ib(default='project')  # str
    fake_version = attr.ib(default='1.0.0')  # str
    fake_summary = attr.ib(default='summary')  # str
    fake_license = attr.ib(default='BSD-3-Clause')  # str


@attr.s
class ElmModule:
    path = attr.ib()  # Path
    name = attr.ib()  # ModuleName


def glob_project_modules(
        project: ElmProject, config: ProjectConfig) -> Iterator[ElmModule]:
    # check for excludes if there's no explicit includes, or if
    # there are explicit includes and exclusion is requested specifically.
    check_excludes = (not config.include_paths) or config.force_exclusion

    exclude_source_directories = [os.path.normpath(src) for src in config.exclude_source_directories]
    for source_dir_name in project.source_directories:
        if check_excludes and exclude_source_directories \
           and (os.path.normpath(source_dir_name) in exclude_source_directories):
            continue
        source_dir = project.path / source_dir_name
        elm_files = source_dir.glob('**/*.elm')
        for elm_file in elm_files:
            if elm_file.relative_to(project.path).parts[0] == STUFF_DIRECTORY:
                continue

            if config.include_paths and not any(_matches_include_path(elm_file, include_path)
                                                for include_path in config.include_paths):
                continue

            rel_path = elm_file.relative_to(source_dir)
            module_name_parts = rel_path.parent.parts + (rel_path.stem,)
            if not all(map(_valid_module_name, module_name_parts)):
                continue

            module_name = '.'.join(module_name_parts)

            if check_excludes and any(fnmatch.fnmatch(module_name, module_pattern)
                                      for module_pattern in config.exclude_modules):
                continue

            yield ElmModule(path=elm_file, name=module_name)


def _valid_module_name(name):
    return module_name_re.match(name)


def _matches_include_path(source_path: Path, include_path: Path):
    try:
        source_path.relative_to(include_path)
    except ValueError:
        return False
    else:
        return True
