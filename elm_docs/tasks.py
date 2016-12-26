'''
'''
from typing import List
from pathlib import Path

from elm_docs import elm_package
from elm_docs import package_tasks
from elm_docs import asset_tasks


def create_tasks(output_dir: str, project_paths: List[str]):
    output_path = Path(output_dir).resolve()

    yield {
        'basename': 'assets',
        'actions': [(asset_tasks.build_assets, (output_path,))],
        'targets': [output_path / 'assets', output_path / 'artifacts'],
        'uptodate': [True],
    }

    packages = list(map(elm_package.from_path,
                            map(lambda path: Path(path).resolve(), project_paths)))
    for package in packages:
        # todo: yield task to install elm for this package
        for task in package_tasks.create_package_tasks(output_path, package):
            yield task

    # all-packages
    all_packages_path = output_path / 'all-packages'
    yield {
        'basename': 'all_packages',
        'actions': [(package_tasks.write_all_packages, (packages, all_packages_path))],
        'targets': [all_packages_path],
        'file_deps': map(elm_package.description_path, packages),
    }

    # new-packages
    new_packages_path = output_path / 'new-packages'
    yield {
        'basename': 'new_packages',
        'actions': [(package_tasks.write_new_packages, (packages, new_packages_path))],
        'targets': [new_packages_path],
        'file_deps': map(elm_package.description_path, packages),
    }


def task_elm_docs():
    project_paths = [
        '.',
        'ui',
    ]
    create_tasks(project_paths)
