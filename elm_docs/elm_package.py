from typing import NamedTuple, Dict, List, Iterator
from pathlib import Path
import fnmatch
import json
import urllib.parse


ModuleName = str
DESCRIPTION_FILENAME = 'elm-package.json'
STUFF_DIRECTORY = 'elm-stuff'


ElmPackageBase = NamedTuple('ElmPackageBase', [
    ('path', Path),
    ('description', Dict),
    ('name', str),
    ('user', str),
    ('project', str),
])


class ElmPackage(ElmPackageBase):
    def __getattr__(self, name):
        return self.description[name.replace('_', '-')]


def from_path(path: Path) -> ElmPackage:
    description = load_description(path / DESCRIPTION_FILENAME)
    repo_path = Path(urllib.parse.urlparse(description['repository']).path)
    user = repo_path.parent.stem
    project = repo_path.stem
    return ElmPackage(
        path=path,
        description=description,
        name='{0}/{1}'.format(user, project),
        user=user,
        project=project,
    )


def description_path(elm_package: ElmPackage) -> Path:
    return elm_package.path / DESCRIPTION_FILENAME


def load_description(path: Path) -> Dict:
    with open(path) as f:
        return json.load(f)


# todo: if project package: expose all modules based on pattern
# todo: if dep package: read exposed-modules of package.json
def iter_package_modules(package: ElmPackage, exclude_patterns: List[str] = []) -> Iterator[ModuleName]:
    for source_dir_name in package.source_directories:
        source_dir = package.path / source_dir_name
        elm_files = source_dir.glob('**/*.elm')
        for elm_file in elm_files:
            if elm_file.relative_to(package.path).parts[0] == STUFF_DIRECTORY:
                continue
            rel_path = elm_file.relative_to(source_dir)
            module_name = '.'.join(rel_path.parent.parts + (rel_path.stem,))
            if any(fnmatch.fnmatch(module_name, pattern)
                   for pattern in exclude_patterns):
                continue
            yield module_name
