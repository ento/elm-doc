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
    description: Dict
    user: str
    project: str

    def __getattr__(self, name):
        return self.description[name.replace('_', '-')]

    @property
    def json_path(self) -> Path:
        return self.path / self.DESCRIPTION_FILENAME

    @property
    def name(self) -> str:
        return '{}/{}'.format(self.user, self.project)

    def iter_dependencies(self) -> Iterator['ElmPackage']:
        raise NotImplementedError


class ElmPackage(ElmProject):
    pass


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
            description=description,
            user=user,
            project=project,
        )

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


class ElmApplication(ElmProject):
    DESCRIPTION_FILENAME = 'elm.json'
    PACKAGES_DIRECTORY = 'package'

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
            description=description,
            user='user',
            project='project',
        )

    def iter_dependencies(self) -> Iterator[ElmPackage]:
        deps = itertools.chain(
            self.dependencies.get('direct', {}).items(),
            self.dependencies.get('indirect', {}).items(),
            self.test_dependencies.get('direct', {}).items(),
            self.test_dependencies.get('indirect', {}).items(),
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


def glob_project_modules(
        project: ElmProject,
        include_paths: List[Path] = [],
        exclude_patterns: List[str] = [],
        force_exclusion: bool = False) -> Iterator[ModuleName]:
    for source_dir_name in project.source_directories:
        source_dir = project.path / source_dir_name
        elm_files = source_dir.glob('**/*.elm')
        for elm_file in elm_files:
            if elm_file.relative_to(project.path).parts[0] == STUFF_DIRECTORY:
                continue

            if include_paths and not any(_matches_include_path(elm_file, include_path)
                                         for include_path in include_paths):
                continue

            rel_path = elm_file.relative_to(source_dir)
            module_name = '.'.join(rel_path.parent.parts + (rel_path.stem,))

            # check for excludes if there's no explicit includes, or if
            # there are explicit includes and exclusion is requested specifically.
            check_excludes = (not include_paths) or force_exclusion
            if check_excludes and any(fnmatch.fnmatch(module_name, module_pattern)
                                      for module_pattern in exclude_patterns):
                continue

            yield module_name


def _matches_include_path(source_path: Path, include_path: Path):
    try:
        source_path.relative_to(include_path)
    except ValueError:
        return False
    else:
        return True
