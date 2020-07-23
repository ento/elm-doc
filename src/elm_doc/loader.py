'''
'''
from typing import Optional
from pathlib import Path

from doit import create_after

from elm_doc import elm_project
from elm_doc import tasks
from elm_doc.run_config import RunConfig, Build, Validate


def make_task_loader(
        project_path: Path,
        project_config: elm_project.ProjectConfig,
        run_config: RunConfig):
    project = elm_project.from_path(project_path)
    if isinstance(run_config, Build):
        project.add_direct_dependencies(
            tasks.catalog.missing_popular_packages(list(project.direct_dependency_names())))

    if run_config.build_path is None:
        run_config.build_path = project_path / '.elm-doc'

    task_loader = {}

    task_loader['task_main_project'] = make_main_project_task_loader(
        project, project_config, run_config)

    if isinstance(run_config, Build):
        task_loader['task_dependencies'] = make_dependencies_task_loader(
            project, project_config, run_config)
        task_loader['task_assets'] = make_assets_task_loader(run_config)

    return task_loader


def make_main_project_task_loader(
        project: elm_project.ElmProject,
        project_config: elm_project.ProjectConfig,
        run_config: RunConfig):
    def task_main_project():
        yield from tasks.project.create_main_project_tasks(
            project, project_config, run_config)
    return task_main_project


def make_dependencies_task_loader(
        project: elm_project.ElmProject,
        project_config: elm_project.ProjectConfig,
        run_config: Build):
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
                package, run_config)

        yield from tasks.catalog.create_catalog_tasks(
            all_packages, run_config)

    return task_dependencies


def make_assets_task_loader(run_config: Build):
    def task_assets():
        yield {
            'basename': 'assets',
            'actions': [(tasks.assets.actions.extract_assets, (run_config.output_path,))],
            'targets': [run_config.output_path / path for path in tasks.assets.bundled_assets],
            'file_dep': [tasks.assets.tarball]
        }
    return task_assets
