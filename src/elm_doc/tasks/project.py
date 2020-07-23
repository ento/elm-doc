from typing import List, Optional
import os.path
from pathlib import Path
from collections import ChainMap
import json

from click import BadParameter
from requests import Session
from doit.action import CmdAction
from doit.tools import create_folder, config_changed

from elm_doc import elm_project
from elm_doc import elm_codeshift
from elm_doc import elm_parser
from elm_doc.elm_project import ElmPackage, ElmProject, ProjectConfig, ModuleName
from elm_doc.run_config import RunConfig, Validate
from elm_doc.tasks import package as package_tasks
from elm_doc.utils import Namespace


class actions(Namespace):
    def write_project_elm_json(
            project: ElmProject,
            project_config: ProjectConfig,
            project_modules: List[ModuleName],
            build_path: Path):
        elm_project_with_exposed_modules = dict(ChainMap(
            {'exposed-modules': [module for module in project_modules]},
            project.as_package(project_config).as_json(),
        ))
        elm_json_path = build_path / ElmPackage.DESCRIPTION_FILENAME
        with open(str(elm_json_path), 'w') as f:
            json.dump(elm_project_with_exposed_modules, f)

    def run_elm_codeshift(src_dir: Path):
        for elm_file_path in src_dir.glob('**/*.elm'):
            if elm_parser.is_port_module(elm_file_path):
                elm_codeshift.strip_ports_from_file(elm_file_path)

    def validate_elm_path(elm_path: Optional[Path]):
        if not elm_path:
            raise BadParameter('please specify the elm executable to use with --elm-path')

    class ElmMake(CmdAction):
        def __init__(self, elm_path: Path, build_path: Path, output_path: Path):
            command = [str(elm_path), 'make', '--docs', str(output_path), '--output', '/dev/null']
            super().__init__(command, cwd=str(build_path), shell=False)

    class SyncSources(CmdAction):
        '''Copy source files to a single directory. This meets the requirement of Elm
        that a package project can only have a single source directory and gives
        us an isolated environment so that Elm can run in parallel with any invocation
        of Elm within the actual project.
        '''

        def __init__(self, project: ElmProject, target_directory: Path):
            sources = ['{}/./'.format(os.path.normpath(source_dir))
                       for source_dir in project.source_directories]
            command = ['rsync', '-a', '--delete', '--recursive', '--ignore-errors'] + sources + [str(target_directory)]
            super().__init__(command, cwd=str(project.path), shell=False)


def create_main_project_tasks(
        session: Session,
        project: ElmProject,
        project_config: ProjectConfig,
        run_config: RunConfig):
    task_name = '{}/{}'.format(project_config.fake_user, project_config.fake_project)
    project_modules = list(elm_project.glob_project_modules(
        project, project_config))
    project_as_package = project.as_package(project_config)
    file_dep = [run_config.elm_path] if run_config.elm_path else []
    file_dep.extend([module.path for module in project_modules])
    uptodate_config = {'elm_json': project_as_package.as_json()}

    build_src_dir = run_config.build_path / 'src'
    docs_actions = [
        (create_folder, (str(run_config.build_path),)),
        (actions.write_project_elm_json, (
            project,
            project_config,
            [module.name for module in project_modules],
            run_config.build_path,
        )),
        (create_folder, (str(build_src_dir),)),
        actions.SyncSources(project, build_src_dir),
        (actions.run_elm_codeshift, (build_src_dir,)),
        (actions.validate_elm_path, (run_config.elm_path,)),
    ]

    if isinstance(run_config, Validate):
        # don't update the final artifact; write to build dir instead
        docs_path = run_config.build_path / project.DOCS_FILENAME
        docs_actions.append(actions.ElmMake(run_config.elm_path, run_config.build_path, docs_path))
        yield {
            'basename': 'validate_docs_json',
            'name': task_name,
            'actions': docs_actions,
            'targets': [],
            'file_dep': file_dep,
            'uptodate': [config_changed(uptodate_config)],
        }
        return

    # project docs.json
    project_output_path = package_tasks.package_docs_root(
        run_config.output_path, project_as_package)
    docs_actions.insert(0, (create_folder, (str(project_output_path),)))
    docs_path = project_output_path / project.DOCS_FILENAME
    docs_actions.append(actions.ElmMake(run_config.elm_path, run_config.build_path, docs_path))

    yield {
        'basename': 'build_docs_json',
        'name': task_name,
        'actions': docs_actions,
        'targets': [docs_path],
        'file_dep': file_dep,
        'uptodate': [config_changed(uptodate_config)],
    }

    yield from package_tasks.create_package_page_tasks(
        package_tasks.Context.Project,
        session,
        project_as_package,
        [module.name for module in project_modules],
        run_config)
