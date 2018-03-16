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
from elm_doc import elm_package
from elm_doc.elm_package import ElmPackage, ModuleName
from elm_doc import page_template
from elm_doc.decorators import capture_subprocess_error


def get_page_package_flags(package: ElmPackage, module: Optional[str] = None):
    flags = {
        'user': package.user,
        'project': package.project,
        'version': package.version,
        'allVersions': [package.version],
        'moduleName': module,
    }
    return flags


def build_package_page(package: ElmPackage, output_path: Path, module: Optional[str] = None, mount_point: str = ''):
    os.makedirs(os.path.dirname(str(output_path)), exist_ok=True)
    with open(str(output_path), 'w') as f:
        f.write(page_template.render(
            'Package', flags=get_page_package_flags(package, module), mount_point=mount_point
        ))


def link_latest_package_dir(package_dir: Path, link_path: Path):
    os.makedirs(str(package_dir), exist_ok=True)
    # prefer relative path to make the built documentation directory relocatable
    link_path.symlink_to(package_dir.relative_to(link_path.parent), target_is_directory=True)


def copy_package_readme(package_readme: Path, output_path: Path):
    if package_readme.is_file():
        shutil.copy(str(package_readme), str(output_path))


@capture_subprocess_error
def build_package_docs_json(
        package: ElmPackage,
        package_modules: List[ModuleName],
        output_path: Path = None,
        elm_make: Path = None,
        validate: bool = False):
    elm_package_with_exposed_modules = dict(ChainMap(
        {'exposed-modules': package_modules},
        package.description,
    ))
    with TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)

        overlayed_elm_package_path = root_path / elm_package.DESCRIPTION_FILENAME
        with open(str(overlayed_elm_package_path), 'w') as f:
            json.dump(elm_package_with_exposed_modules, f)

        if elm_make is None:
            elm_platform.install(root_path, package.elm_version)
            elm_make = elm_platform.get_npm_executable_path(root_path, 'elm-make')

        if validate:
            # todo: support windows if we want to
            output_path = '/dev/null'

        env = elm_package_overlayer_env(
            str(overlayed_elm_package_path),
            str(elm_package.description_path(package)),
            os.environ)
        subprocess.check_call(
            [str(elm_make), '--yes', '--docs', str(output_path), '--output', '/dev/null'],
            cwd=str(package.path),
            env=env)


@retry(
    retry_on_exception=lambda e: isinstance(e, urllib.error.URLError),
    wait_exponential_multiplier=1000,  # Wait 2^x * 1000 milliseconds between each retry,
    wait_exponential_max=30 * 1000,  # up to 30 seconds, then 30 seconds afterwards
    stop_max_attempt_number=10)
def download_package_docs_json(package: ElmPackage, output_path: Path):
    url = 'http://package.elm-lang.org/packages/{name}/{version}/documentation.json'.format(
        name=package.name, version=package.version
    )
    urllib.request.urlretrieve(url, str(output_path))


def package_task_basename_factory(package):
    return lambda name: '{}:{}/{}'.format(name, package.name, package.version)


def create_package_tasks(
        output_path: Optional[Path],
        package: ElmPackage,
        elm_make: Path = None,
        include_paths: List[str] = [],
        exclude_modules: List[str] = [],
        force_exclusion: bool = False,
        mount_point: str = '',
        validate: bool = False):
    basename = package_task_basename_factory(package)

    if package.is_dep:
        package_modules = package.exposed_modules
    else:
        package_modules = list(elm_package.glob_package_modules(
            package, include_paths, exclude_modules, force_exclusion))

    if validate:
        yield {
            'basename': basename('validate_package_docs_json'),
            'actions': [(build_package_docs_json,
                         (package, package_modules),
                         {'elm_make': elm_make, 'validate': True})],
            'targets': [],
            # 'file_dep': [all_elm_files_in_source_dirs] # todo
        }
        return

    package_docs_root = output_path / 'packages' / package.user / package.project / package.version

    # package documentation.json
    docs_json_path = package_docs_root / 'documentation.json'
    if package.is_dep:
        yield {
            'basename': basename('download_package_docs_json'),
            'actions': [(create_folder, (str(package_docs_root),)),
                        (download_package_docs_json, (package, docs_json_path))],
            'targets': [docs_json_path],
            # 'file_dep': [all_elm_files_in_source_dirs] # todo
            'uptodate': [True],
        }
    else:
        yield {
            'basename': basename('build_package_docs_json'),
            'actions': [(create_folder, (str(package_docs_root),)),
                        (build_package_docs_json,
                         (package, package_modules),
                         {'elm_make': elm_make, 'output_path': docs_json_path})],
            'targets': [docs_json_path],
            # 'file_dep': [all_elm_files_in_source_dirs] # todo
        }

    # package index page
    package_index_output = package_docs_root / 'index.html'
    yield {
        'basename': basename('package_page'),
        'actions': [(build_package_page, (package, package_index_output), {'mount_point': mount_point})],
        'targets': [package_index_output],
        # 'file_dep': [module['source_file']] #todo
        'uptodate': [True],
    }

    # package readme
    readme_filename = 'README.md'
    package_readme = package.path / readme_filename
    output_readme_path = package_docs_root / readme_filename
    if package_readme.is_file():
        yield {
            'basename': basename('package_readme'),
            'actions': [(copy_package_readme, (package_readme, output_readme_path))],
            'targets': [output_readme_path],
            'file_dep': [package_readme],
        }

    # link from /latest
    latest_path = package_docs_root.parent / 'latest'
    yield {
        'basename': basename('package_latest_link'),
        'actions': [(link_latest_package_dir, (package_docs_root, latest_path))],
        'targets': [latest_path],
        # 'file_dep': [], # todo
        'uptodate': [True]
    }

    # module pages
    for module in package_modules:
        module_output = package_docs_root / module.replace('.', '-')
        yield {
            'basename': basename('module_page') + ':' + module,
            'actions': [(build_package_page, (package, module_output, module), {'mount_point': mount_point})],
            'targets': [module_output],
            # 'file_dep': [module['source_file']] #todo
            'uptodate': [True],
        }
