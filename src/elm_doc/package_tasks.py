from typing import List, Optional
import enum
from pathlib import Path
import json
import shutil

from doit.tools import create_folder, config_changed

from elm_doc import page_tasks
from elm_doc.elm_project import ElmPackage, ModuleName


def build_package_releases(output_path: Path, version: str, timestamp: int):
    releases = {version: timestamp}
    with open(str(output_path), 'w') as f:
        json.dump(releases, f)


def link_latest_package_dir(output_path: Path, package_dir: Path):
    package_dir.mkdir(parents=True, exist_ok=True)
    # prefer relative path to make the built documentation directory relocatable
    if output_path.is_symlink():
        output_path.unlink()
    output_path.symlink_to(package_dir.relative_to(output_path.parent), target_is_directory=True)


def copy_package_readme(package_readme: Path, output_path: Path):
    if package_readme.is_file():
        shutil.copy(str(package_readme), str(output_path))


def copy_package_docs_json(package: ElmPackage, output_path: Path):
    source = package.path / package.DOCS_FILENAME
    shutil.copy(str(source), str(output_path))


def _package_task_name(package):
    return '{}/{}'.format(package.name, package.version)


def create_dependency_tasks(
        output_path: Optional[Path],
        package: ElmPackage,
        mount_point: str = ''):
    task_name = _package_task_name(package)
    package_modules = package.sorted_exposed_modules()
    package_output_path = package_docs_root(output_path, package)

    # package docs.json
    docs_json_path = package_output_path / package.DOCS_FILENAME
    yield {
        'basename': Context.Dependency.basename('copy_docs_json'),
        'name': task_name,
        'actions': [(create_folder, (str(package_output_path),)),
                    (copy_package_docs_json, (package, docs_json_path))],
        'targets': [docs_json_path],
        'file_dep': [package.path / package.DOCS_FILENAME]
    }

    for page_task in create_package_page_tasks(Context.Dependency, output_path, package, package_modules, mount_point):
        yield page_task


class Context(enum.Enum):
    '''In order to delay the creation of tasks for project dependencies,
    the basenames of the delayed tasks need to be different than those
    for the main project tasks for doit to correctly pick up.

    This enum provides a way for differentiating those two contexts when
    creating tasks in this module, which are shared between the two.
    '''
    Project = 'project'
    Dependency = 'dep'

    def basename(self, suffix):
        return '{}_{}'.format(self.value, suffix)


def create_package_page_tasks(
        context: Context,
        output_path: Optional[Path],
        package: ElmPackage,
        package_modules: List[ModuleName],
        mount_point: str = '',):
    task_name = _package_task_name(package)
    package_output_path = package_docs_root(output_path, package)
    page_flags = {'mount_point': mount_point}

    # package index page
    package_index_output = package_output_path / 'index.html'
    yield {
        'basename': context.basename('top_page'),
        'name': task_name,
        'actions': [(page_tasks.write_page, (package_index_output,), page_flags)],
        'targets': [package_index_output],
        'uptodate': [config_changed(page_flags)],
    }

    # package readme
    readme_filename = 'README.md'
    package_readme = package.path / readme_filename
    output_readme_path = package_output_path / readme_filename
    if package_readme.is_file():
        yield {
            'basename': context.basename('readme'),
            'name': task_name,
            'actions': [(copy_package_readme, (package_readme, output_readme_path))],
            'targets': [output_readme_path],
            'file_dep': [package_readme],
        }

    # package releases
    package_releases_output = package_output_path.parent / 'releases.json'
    # generated docs will only ever include one version per package, so we hardcode
    # the timestamp.
    content = {'version': package.version, 'timestamp': 1}
    yield {
        'basename': context.basename('releases'),
        'name': task_name,
        'actions': [(build_package_releases, (package_releases_output,), content)],
        'targets': [package_releases_output],
        'uptodate': [config_changed(content)]
    }

    # link from /latest
    latest_path = package_output_path.parent / 'latest'
    uptodate_config = {'link_target': str(package_output_path.relative_to(output_path))}
    yield {
        'basename': context.basename('latest_link'),
        'name': task_name,
        'actions': [(link_latest_package_dir, (latest_path, package_output_path))],
        'targets': [latest_path],
        'uptodate': [config_changed(uptodate_config)]
    }

    # module pages
    for module_name in package_modules:
        module_output = package_output_path / module_name.replace('.', '-')
        yield {
            'basename': context.basename('module_page'),
            'name': '{}:{}'.format(task_name, module_name),
            'actions': [(page_tasks.write_page, (module_output,), page_flags)],
            'targets': [module_output],
            'uptodate': [config_changed(page_flags)],
        }


def package_docs_root(output_path: Optional[Path], package: ElmPackage) -> Path:
    return output_path / 'packages' / package.user / package.project / package.version
