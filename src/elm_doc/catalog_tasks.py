from typing import List, Iterator, Tuple
from pathlib import Path
import json

import requests
from retrying import retry

from elm_doc.elm_project import ElmPackage, ExactVersion
from elm_doc import elm_project
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


def write_search_json(packages: List[ElmPackage], output_path: Path):
    all_packages = map(
        lambda package: {
            'name': package.name,
            'summary': package.summary,
            'license': package.license,
            'versions': [package.version],
        },
        packages)
    with open(str(output_path), 'w') as f:
        json.dump(list(all_packages), f)


def create_catalog_tasks(packages: List[ElmPackage], output_path: Path, mount_point: str = ''):
    # index
    index_path = output_path / 'index.html'
    yield {
        'basename': 'index',
        'actions': [(page_tasks.write_page, (index_path, mount_point))],
        'targets': [index_path],
        'uptodate': [True],
    }

    # search.json
    search_json_path = output_path / 'search.json'
    yield {
        'basename': 'search_json',
        'actions': [(write_search_json, (packages, search_json_path))],
        'targets': [search_json_path],
        'file_dep': [package.json_path for package in packages],
    }

    # help pages
    for help_file in asset_tasks.bundled_helps:
        url_path =  Path(help_file).relative_to('assets').with_suffix('')
        help_output_path = (output_path / url_path)
        yield {
            'basename': 'help',
            'name': url_path,
            'actions': [(page_tasks.write_page, (help_output_path, mount_point))],
            'targets': [help_output_path],
            'file_dep': [output_path / help_file],
        }
