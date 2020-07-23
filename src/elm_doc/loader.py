'''
'''
from typing import Optional
from pathlib import Path

from doit import create_after

from elm_doc import elm_project
from elm_doc import tasks


def make_task_loader(
        project_path: Path,
        project_config: elm_project.ProjectConfig,
        elm_path: Optional[Path],
        output_path: Optional[Path] = None,
        build_path: Optional[Path] = None,
        mount_point: str = '',
        validate: bool = False):
    project = elm_project.from_path(project_path)
    if not validate:
        project.add_direct_dependencies(
            tasks.catalog.missing_popular_packages(list(project.direct_dependency_names())))

    if build_path is None:
        build_path = project_path / '.elm-doc'

    task_loader = {}

    task_loader['task_main_project'] = make_main_project_task_loader(
        project,
        project_config,
        elm_path,
        output_path,
        build_path,
        mount_point,
        validate,
    )

    if validate:
        return task_loader

    task_loader['task_dependencies'] = make_dependencies_task_loader(
        project,
        project_config,
        output_path,
        mount_point,
    )
    task_loader['task_assets'] = make_assets_task_loader(output_path)

    return task_loader


def make_main_project_task_loader(
        project: elm_project.ElmProject,
        project_config: elm_project.ProjectConfig,
        elm_path: Optional[Path],
        output_path: Optional[Path] = None,
        build_path: Optional[Path] = None,
        mount_point: str = '',
        validate: bool = False):
    def task_main_project():
        yield from tasks.project.create_main_project_tasks(
            project,
            project_config,
            elm_path,
            output_path,
            build_path,
            mount_point=mount_point,
            validate=validate)
    return task_main_project


def make_dependencies_task_loader(
        project: elm_project.ElmProject,
        project_config: elm_project.ProjectConfig,
        output_path: Optional[Path] = None,
        mount_point: str = ''):
    @create_after(executed='build_docs_json', creates=[
        # package tasks
        'dep_copy_docs_json', 'dep_top_page', 'dep_elm_json', 'dep_readme',
        'dep_releases', 'dep_latest_link', 'dep_module_page',
        # catalog tasks
        'index', 'search_json', 'help',
    ])
    def task_dependencies():
        deps = list(project.iter_direct_dependencies())
        deps.sort(key=lambda dep: dep.name)
        all_packages = [project.as_package(project_config).without_license()] + deps

        for package in deps:
            yield from tasks.package.create_dependency_tasks(
                output_path, package, mount_point)

        yield from tasks.catalog.create_catalog_tasks(
            all_packages, output_path, mount_point=mount_point)

    return task_dependencies


def make_assets_task_loader(output_path: Optional[Path] = None):
    def task_assets():
        yield {
            'basename': 'assets',
            'actions': [(tasks.assets.actions.extract_assets, (output_path,))],
            'targets': [output_path / path for path in tasks.assets.bundled_assets],
            'file_dep': [tasks.assets.tarball]
        }
    return task_assets
