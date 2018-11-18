from typing import List, Optional
import os
import os.path
from collections import ChainMap
from pathlib import Path
import json
import shutil
from tempfile import TemporaryDirectory
import subprocess
import urllib.error
import urllib.request

from doit.tools import create_folder
from retrying import retry

from elm_doc import elm_platform
from elm_doc import elm_package_overlayer_env
from elm_doc import elm_project
from elm_doc.elm_project import ElmProject, ModuleName
from elm_doc import page_template
from elm_doc.decorators import capture_subprocess_error


def get_page_package_flags(project: ElmProject, module: Optional[str] = None):
    flags = {
        'user': project.user,
        'project': project.project,
        'version': project.version,
        'allVersions': [project.version],
        'moduleName': module,
    }
    return flags


def build_project_page(project: ElmProject, output_path: Path, module: Optional[str] = None, mount_point: str = ''):
    os.makedirs(os.path.dirname(str(output_path)), exist_ok=True)
    with open(str(output_path), 'w') as f:
        f.write(page_template.render(
            'Package', flags=get_page_package_flags(project, module), mount_point=mount_point
        ))


def link_latest_project_dir(project_dir: Path, link_path: Path):
    os.makedirs(str(project_dir), exist_ok=True)
    # prefer relative path to make the built documentation directory relocatable
    link_path.symlink_to(project_dir.relative_to(link_path.parent), target_is_directory=True)


def copy_project_readme(project_readme: Path, output_path: Path):
    if project_readme.is_file():
        shutil.copy(str(project_readme), str(output_path))


@capture_subprocess_error
def build_project_docs_json(
        project: ElmProject,
        project_modules: List[ModuleName],
        output_path: Path = None,
        elm_make: Path = None,
        validate: bool = False):
    elm_project_with_exposed_modules = dict(ChainMap(
        {'exposed-modules': project_modules},
        project.description,
    ))
    with TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)

        overlayed_elm_project_path = root_path / elm_project.DESCRIPTION_FILENAME
        with open(str(overlayed_elm_project_path), 'w') as f:
            json.dump(elm_project_with_exposed_modules, f)

        if elm_make is None:
            elm_platform.install(root_path, project.elm_version)
            elm_make = elm_platform.get_npm_executable_path(root_path, 'elm-make')

        if validate:
            # todo: support windows if we want to
            output_path = '/dev/null'

        env = elm_package_overlayer_env(
            str(overlayed_elm_project_path),
            str(elm_project.description_path(project)),
            os.environ)
        subprocess.check_call(
            [str(elm_make), '--yes', '--docs', str(output_path), '--output', '/dev/null'],
            cwd=str(project.path),
            env=env)


@retry(
    retry_on_exception=lambda e: isinstance(e, urllib.error.URLError),
    wait_exponential_multiplier=1000,  # Wait 2^x * 1000 milliseconds between each retry,
    wait_exponential_max=30 * 1000,  # up to 30 seconds, then 30 seconds afterwards
    stop_max_attempt_number=10)
def download_project_docs_json(project: ElmProject, output_path: Path):
    url = 'https://package.elm-lang.org/packages/{name}/{version}/docs.json'.format(
        name=project.name, version=project.version
    )
    urllib.request.urlretrieve(url, str(output_path))


def project_task_basename_factory(project):
    return lambda name: '{}:{}/{}'.format(name, project.name, project.version)


def create_project_tasks(
        output_path: Optional[Path],
        project: ElmProject,
        elm_make: Path = None,
        include_paths: List[str] = [],
        exclude_modules: List[str] = [],
        force_exclusion: bool = False,
        mount_point: str = '',
        validate: bool = False):
    basename = project_task_basename_factory(project)

    if project.is_dep:
        project_modules = project.exposed_modules
    else:
        project_modules = list(elm_project.glob_project_modules(
            project, include_paths, exclude_modules, force_exclusion))

    if validate:
        yield {
            'basename': basename('validate_project_docs_json'),
            'actions': [(build_project_docs_json,
                         (project, project_modules),
                         {'elm_make': elm_make, 'validate': True})],
            'targets': [],
            # 'file_dep': [all_elm_files_in_source_dirs] # todo
        }
        return

    project_docs_root = _project_docs_root(output_path, project)

    # project documentation.json
    docs_json_path = project_docs_root / 'documentation.json'
    if project.is_dep:
        yield {
            'basename': basename('download_project_docs_json'),
            'actions': [(create_folder, (str(project_docs_root),)),
                        (download_project_docs_json, (project, docs_json_path))],
            'targets': [docs_json_path],
            # 'file_dep': [all_elm_files_in_source_dirs] # todo
            'uptodate': [True],
        }
    else:
        yield {
            'basename': basename('build_project_docs_json'),
            'actions': [(create_folder, (str(project_docs_root),)),
                        (build_project_docs_json,
                         (project, project_modules),
                         {'elm_make': elm_make, 'output_path': docs_json_path})],
            'targets': [docs_json_path],
            # 'file_dep': [all_elm_files_in_source_dirs] # todo
        }

    for page_task in _create_project_page_tasks(output_path, project, project_modules, mount_point):
        yield page_task


def _create_project_page_tasks(
        output_path: Optional[Path],
        project: ElmProject,
        project_modules: List[ModuleName],
        mount_point: str = '',):
    basename = project_task_basename_factory(project)
    project_docs_root = _project_docs_root(output_path, project)

    # project index page
    project_index_output = project_docs_root / 'index.html'
    yield {
        'basename': basename('project_page'),
        'actions': [(build_project_page, (project, project_index_output), {'mount_point': mount_point})],
        'targets': [project_index_output],
        # 'file_dep': [module['source_file']] #todo
        'uptodate': [True],
    }

    # project readme
    readme_filename = 'README.md'
    project_readme = project.path / readme_filename
    output_readme_path = project_docs_root / readme_filename
    if project_readme.is_file():
        yield {
            'basename': basename('project_readme'),
            'actions': [(copy_project_readme, (project_readme, output_readme_path))],
            'targets': [output_readme_path],
            'file_dep': [project_readme],
        }

    # link from /latest
    latest_path = project_docs_root.parent / 'latest'
    yield {
        'basename': basename('project_latest_link'),
        'actions': [(link_latest_project_dir, (project_docs_root, latest_path))],
        'targets': [latest_path],
        # 'file_dep': [], # todo
        'uptodate': [True]
    }

    # module pages
    for module in project_modules:
        module_output = project_docs_root / module.replace('.', '-')
        yield {
            'basename': basename('module_page') + ':' + module,
            'actions': [(build_project_page, (project, module_output, module), {'mount_point': mount_point})],
            'targets': [module_output],
            # 'file_dep': [module['source_file']] #todo
            'uptodate': [True],
        }


def _project_docs_root(output_path: Optional[Path], project: ElmProject) -> Path:
    return output_path / 'packages' / project.user / project.project / project.version
