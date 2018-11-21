from typing import List, Optional
import os
from collections import ChainMap
from pathlib import Path
import json
from tempfile import TemporaryDirectory
import subprocess

from dirsync import sync
from doit.tools import create_folder

from elm_doc import elm_platform
from elm_doc import elm_project
from elm_doc import package_tasks
from elm_doc.elm_project import ElmPackage, ElmProject, ProjectConfig, ModuleName
from elm_doc.decorators import capture_subprocess_error

@capture_subprocess_error
def build_project_docs_json(
        project: ElmProject,
        project_config: ProjectConfig,
        project_modules: List[ModuleName],
        output_path: Path = None,
        elm_make: Path = None,
        validate: bool = False):
    elm_project_with_exposed_modules = dict(ChainMap(
        {'exposed-modules': project_modules},
        project.as_package(project_config).as_json(),
    ))
    with TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)

        elm_json_path = root_path / ElmPackage.DESCRIPTION_FILENAME
        with open(str(elm_json_path), 'w') as f:
            json.dump(elm_project_with_exposed_modules, f)

        package_src_dir = root_path / 'src'
        for source_dir in project.source_directories:
            sync(project.path / source_dir, package_src_dir, 'sync', create=True, purge=True)

        if elm_make is None:
            elm_platform.install(root_path, project.elm_version)
            elm_make = elm_platform.get_node_modules_elm_path(root_path)

        if validate:
            output_path = root_path / 'docs.json'

        subprocess.run(
            [str(elm_make), 'make', '--docs', str(output_path), '--output', '/dev/null'],
            cwd=str(root_path),
            check=True,
            capture_output=True,
        )


def _project_task_basename_factory(_project):
    return lambda name: '{}:project'.format(name)


def create_main_project_tasks(
        project: ElmProject,
        project_config: ProjectConfig,
        output_path: Optional[Path],
        elm_make: Path = None,
        mount_point: str = '',
        validate: bool = False):
    basename = _project_task_basename_factory(project)

    project_modules = list(elm_project.glob_project_modules(
        project, project_config))

    if validate:
        yield {
            'basename': basename('validate_project_docs_json'),
            'actions': [(build_project_docs_json,
                         (project, project_config, project_modules),
                         {'elm_make': elm_make, 'validate': True})],
            'targets': [],
            # 'file_dep': [all_elm_files_in_source_dirs] # todo
        }
        return

    project_as_package = project.as_package(project_config)
    project_output_path = package_tasks.package_docs_root(output_path, project_as_package)

    # project documentation.json
    docs_json_path = project_output_path / 'documentation.json'
    yield {
        'basename': basename('build_project_docs_json'),
        'actions': [(create_folder, (str(project_output_path),)),
                    (build_project_docs_json,
                     (project, project_config, project_modules),
                     {'elm_make': elm_make, 'output_path': docs_json_path})],
        'targets': [docs_json_path],
        # 'file_dep': [all_elm_files_in_source_dirs] # todo
    }

    for page_task in package_tasks.create_package_page_tasks(
            output_path, project_as_package, project_modules, mount_point):
        yield page_task
