from typing import List, Iterator, Tuple
from pathlib import Path
import json

import attr
import requests
from retrying import retry
from doit.tools import config_changed

from elm_doc.elm_project import ElmPackage, ExactVersion
from elm_doc import asset_tasks
from elm_doc import page_tasks


popular_packages = [
    'elm/core',
    'elm/html',
    'elm/json',
    'elm/browser',
    'elm/url',
    'elm/http',
]


def missing_popular_packages(package_names: List[str]) -> Iterator[Tuple[str, ExactVersion]]:
    missing_names = set(popular_packages) - set(package_names)
    for missing_name in missing_names:
        latest_version = _fetch_latest_version(missing_name)
        yield (missing_name, latest_version)


@retry(
    retry_on_exception=lambda e: isinstance(e, requests.RequestException),
    wait_exponential_multiplier=1000,  # Wait 2^x * 1000 milliseconds between each retry,
    wait_exponential_max=30 * 1000,  # up to 30 seconds, then 30 seconds afterwards
    stop_max_attempt_number=10)
def _fetch_latest_version(package_name: str) -> ExactVersion:
    releases_url = 'https://package.elm-lang.org/packages/{}/releases.json'.format(package_name)
    releases = requests.get(releases_url).json()
    return sorted(releases.keys())[-1]


@attr.s
class SearchEntry:
    name = attr.ib()  # str
    summary = attr.ib()  # str
    license = attr.ib()  # str
    versions = attr.ib()  # List[ExactVersion]

    @classmethod
    def from_package(cls, package: ElmPackage) -> 'SearchEntry':
        return SearchEntry(
            name=package.name,
            summary=package.summary,
            license=package.license,
            versions=[package.version],
        )


def write_search_json(entries: List[SearchEntry], output_path: Path):
    with open(str(output_path), 'w') as f:
        json.dump([attr.asdict(entry) for entry in entries], f)


def create_catalog_tasks(packages: List[ElmPackage], output_path: Path, mount_point: str = ''):
    page_flags = {'mount_point': mount_point}

    # index
    index_path = output_path / 'index.html'
    yield {
        'basename': 'index',
        'actions': [(page_tasks.write_page, (index_path,), page_flags)],
        'targets': [index_path],
        'uptodate': [config_changed(page_flags)],
    }

    # search.json
    search_json_path = output_path / 'search.json'
    search_entries = list(map(SearchEntry.from_package, packages))
    yield {
        'basename': 'search_json',
        'actions': [(write_search_json, (search_entries, search_json_path))],
        'targets': [search_json_path],
        'uptodate': [config_changed({'entries': [attr.asdict(entry) for entry in search_entries]})],
    }

    # help pages
    for help_file in asset_tasks.bundled_helps:
        url_path = Path(help_file).relative_to('assets').with_suffix('')
        help_output_path = (output_path / url_path)
        yield {
            'basename': 'help',
            'name': url_path,
            'actions': [(page_tasks.write_page, (help_output_path,), page_flags)],
            'targets': [help_output_path],
            'file_dep': [output_path / help_file],
            'uptodate': [config_changed(page_flags)],
        }
