from typing import List, Iterator, Tuple
from pathlib import Path
import json

import attr
from requests import Session
from doit.tools import config_changed

from elm_doc.elm_project import ElmPackage, ExactVersion, fetch_releases
from elm_doc.run_config import Build
from elm_doc.tasks import assets as assets_tasks
from elm_doc.tasks import html as html_tasks
from elm_doc.utils import Namespace


popular_packages = [
    'elm/core',
    'elm/html',
    'elm/json',
    'elm/browser',
    'elm/url',
    'elm/http',
]


def missing_popular_packages(
        session: Session,
        package_names: List[str]) -> Iterator[Tuple[str, ExactVersion]]:
    missing_names = set(popular_packages) - set(package_names)
    for missing_name in missing_names:
        releases = fetch_releases(session, missing_name)
        latest_version = sorted(releases.keys())[-1]
        yield (missing_name, latest_version)


@attr.s
class SearchEntry:
    name = attr.ib()  # str
    summary = attr.ib()  # str
    license = attr.ib()  # str
    version = attr.ib()  # ExactVersion

    @classmethod
    def from_package(cls, package: ElmPackage) -> 'SearchEntry':
        return SearchEntry(
            name=package.name,
            summary=package.summary,
            license=package.license,
            version=package.version,
        )


class actions(Namespace):
    def write_search_json(entries: List[SearchEntry], output_path: Path):
        with open(str(output_path), 'w') as f:
            json.dump([attr.asdict(entry) for entry in entries], f)


def create_catalog_tasks(packages: List[ElmPackage], run_config: Build):
    page_flags = {'mount_point': run_config.mount_point}

    # index
    index_path = run_config.output_path / 'index.html'
    yield {
        'basename': 'index',
        'actions': [(html_tasks.actions.write, (index_path,), page_flags)],
        'targets': [index_path],
        'uptodate': [config_changed(page_flags)],
    }

    # search.json
    search_json_path = run_config.output_path / 'search.json'
    search_entries = list(map(SearchEntry.from_package, packages))
    yield {
        'basename': 'search_json',
        'actions': [(actions.write_search_json, (search_entries, search_json_path))],
        'targets': [search_json_path],
        'uptodate': [config_changed({'entries': [attr.asdict(entry) for entry in search_entries]})],
    }

    # help pages
    for help_file in assets_tasks.bundled_helps:
        url_path = Path(help_file).relative_to('assets').with_suffix('')
        help_output_path = run_config.output_path / url_path
        yield {
            'basename': 'help',
            'name': url_path,
            'actions': [(html_tasks.actions.write, (help_output_path,), page_flags)],
            'targets': [help_output_path],
            'file_dep': [run_config.output_path / help_file],
            'uptodate': [config_changed(page_flags)],
        }
