'''
'''
from typing import List
from pathlib import Path

from elm_docs import elm_package
from elm_docs import package_tasks
from elm_docs import asset_tasks
from elm_docs import catalog_tasks


def create_tasks(project_path: str, output_dir: str, elm_make: str = None, exclude_modules: List[str] = []):
    output_path = Path(output_dir).resolve()
    elm_make = Path(elm_make).resolve() if elm_make is not None else None
    project_package = elm_package.from_path(Path(project_path).resolve())
    deps = list(elm_package.iter_dependencies(project_package))
    all_packages = [project_package] + deps

    for task in package_tasks.create_package_tasks(
            output_path, project_package, elm_make=elm_make, exclude_modules=exclude_modules):
        yield task

    for package in deps:
        for task in package_tasks.create_package_tasks(output_path, package, elm_make=elm_make):
            yield task

    for task in catalog_tasks.create_catalog_tasks(all_packages, output_path):
        yield task

    yield {
        'basename': 'assets',
        'actions': [(asset_tasks.build_assets, (output_path,))],
        'targets': [output_path / 'assets', output_path / 'artifacts'],
        'uptodate': [True],
    }
