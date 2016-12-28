'''
'''
from typing import List
from pathlib import Path

from elm_docs import elm_package
from elm_docs import package_tasks
from elm_docs import asset_tasks
from elm_docs import catalog_tasks


def create_tasks(project_path: str, output_dir: str, exclude_modules: List[str] = []):
    output_path = Path(output_dir).resolve()
    project_package = elm_package.from_path(Path(proejct_path).resolve())
    packages = [project_package]

    for package in packages:
        for task in package_tasks.create_package_tasks(output_path, package, exclude_modules):
            yield task

    for task in catalog_tasks.create_catalog_tasks(packages, output_path):
        yield task

    yield {
        'basename': 'assets',
        'actions': [(asset_tasks.build_assets, (output_path,))],
        'targets': [output_path / 'assets', output_path / 'artifacts'],
        'uptodate': [True],
    }
