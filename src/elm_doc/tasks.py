'''
'''
from typing import List, Optional
from pathlib import Path

from elm_doc import elm_project
from elm_doc import project_tasks
from elm_doc import package_tasks
from elm_doc import asset_tasks
from elm_doc import catalog_tasks


def create_tasks(
        project_path: Path,
        project_config: elm_project.ProjectConfig,
        output_path: Optional[Path] = None,
        elm_path: Optional[Path] = None,
        mount_point: str = '',
        validate: bool = False):
    # todo: gracefully handle missing elm-package.json
    project = elm_project.from_path(project_path)
    # todo: gracefully handle missing exact-dependencies.json

    for task in project_tasks.create_main_project_tasks(
            project,
            project_config,
            output_path,
            elm_path=elm_path,
            mount_point=mount_point,
            validate=validate):
        yield task

    if validate:
        return

    deps = list(project.iter_dependencies())
    all_packages = [project.as_package(project_config)] + deps

    for package in deps:
        for task in package_tasks.create_dependency_tasks(
                output_path, package, mount_point):
            yield task

    for task in catalog_tasks.create_catalog_tasks(all_packages, output_path, mount_point=mount_point):
        yield task

    yield {
        'basename': 'assets',
        'actions': [(asset_tasks.build_assets, (project.elm_version, output_path, mount_point))],
        'targets': [output_path / 'assets', output_path / 'artifacts'],
        'uptodate': [True],
    }
