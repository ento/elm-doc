from typing import List, Optional
from collections import ChainMap
from pathlib import Path
import json
from tempfile import TemporaryDirectory
import subprocess

from dirsync import sync
from doit.tools import create_folder, config_changed

from elm_doc import elm_platform
from elm_doc import elm_project
from elm_doc import elm_codeshift
from elm_doc import package_tasks
from elm_doc.elm_project import ElmPackage, ElmProject, ProjectConfig, ModuleName
from elm_doc.decorators import capture_subprocess_error


@capture_subprocess_error
def build_project_docs_json(
        project: ElmProject,
        project_config: ProjectConfig,
        project_modules: List[ModuleName],
        output_path: Path = None,
        build_path: Path = None,
        elm_path: Path = None,
        validate: bool = False):
    elm_project_with_exposed_modules = dict(ChainMap(
        {'exposed-modules': [module for module in project_modules]},
        project.as_package(project_config).as_json(),
    ))
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        build_path.mkdir(parents=True, exist_ok=True)

        elm_json_path = build_path / ElmPackage.DESCRIPTION_FILENAME
        with open(str(elm_json_path), 'w') as f:
            json.dump(elm_project_with_exposed_modules, f)

        package_src_dir = build_path / 'src'
        changed_files = set()
        for source_dir in project.source_directories:
            changed_files |= sync(
                str(project.path / source_dir), str(package_src_dir), 'sync', create=True)

        for elm_file in changed_files:
            elm_file_path = Path(elm_file)
            if elm_file_path.suffix == '.elm' and elm_file_path.exists():
                elm_codeshift.strip_ports_from_file(Path(elm_file))

        if elm_path is None:
            elm_platform.install(tmp_path, project.elm_version)
            elm_path = elm_platform.get_node_modules_elm_path(tmp_path)

        if validate:
            # don't update the final artifact; write to build dir instead
            output_path = build_path / project.DOCS_FILENAME

        subprocess.check_output(
            [str(elm_path), 'make', '--docs', str(output_path), '--output', '/dev/null'],
            cwd=str(build_path),
            stderr=subprocess.STDOUT,
        )


def create_main_project_tasks(
        project: ElmProject,
        project_config: ProjectConfig,
        output_path: Optional[Path],
        build_path: Path = None,
        elm_path: Path = None,
        mount_point: str = '',
        validate: bool = False):
    task_name = '{}/{}'.format(project_config.fake_user, project_config.fake_project)
    project_modules = list(elm_project.glob_project_modules(
        project, project_config))
    project_as_package = project.as_package(project_config)
    file_dep = [elm_path] if elm_path else []
    file_dep.extend([module.path for module in project_modules])
    uptodate_config = {'elm_json': project_as_package.as_json()}

    if validate:
        yield {
            'basename': 'validate_docs_json',
            'name': task_name,
            'actions': [(build_project_docs_json,
                         (project, project_config, [module.name for module in project_modules]),
                         {'build_path': build_path, 'elm_path': elm_path, 'validate': True})],
            'targets': [],
            'file_dep': file_dep,
            'uptodate': [config_changed(uptodate_config)],
        }
        return

    project_output_path = package_tasks.package_docs_root(output_path, project_as_package)

    # project docs.json
    docs_json_path = project_output_path / project.DOCS_FILENAME
    yield {
        'basename': 'build_docs_json',
        'name': task_name,
        'actions': [(create_folder, (str(project_output_path),)),
                    (build_project_docs_json,
                     (project, project_config, [module.name for module in project_modules]),
                     {'build_path': build_path, 'elm_path': elm_path, 'output_path': docs_json_path})],
        'targets': [docs_json_path],
        'file_dep': file_dep,
        'uptodate': [config_changed(uptodate_config)],
    }

    for page_task in package_tasks.create_package_page_tasks(
            package_tasks.Context.Project,
            output_path,
            project_as_package,
            [module.name for module in project_modules],
            mount_point):
        yield page_task
