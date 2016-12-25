'''
'''
from typing import Dict, NamedTuple, Iterator, Optional
import os
import os.path
import json
from pathlib import Path
import shutil
import urllib.parse


PackageVersion = NamedTuple('PackageVersion', [('user', str), ('project', str), ('version', str)])
ModuleName = str


PAGE_PACKAGE_TEMPLATE = '''
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <link rel="shortcut icon" size="16x16, 32x32, 48x48, 64x64, 128x128, 256x256" href="/assets/favicon.ico">
    <link rel="stylesheet" href="/assets/highlight/styles/default.css">
    <link rel="stylesheet" href="/assets/style.css">
    <script src="/assets/highlight/highlight.pack.js"></script>
    <script src="/artifacts/Page-Package.js"></script>
  </head>
  <body>
  <script>
    var page = Elm.Page.Package.fullscreen({flags});
  </script>
  </body>
</html>
'''

def get_page_package_flags(package_version: PackageVersion, module : Optional[str] = None):
    flags = {
        'user': package_version.user,
        'project': package_version.project,
        'version': package_version.version,
        'allVersions': [package_version.version],
        'moduleName': module,
    }
    return flags


def get_package_version(elm_package: Dict) -> PackageVersion:
    repo_path = Path(urllib.parse.urlparse(elm_package['repository']).path)
    return PackageVersion(
        repo_path.parent.stem,
        repo_path.stem,
        elm_package['version'],
    )


def build_package_page(package_version: PackageVersion, output_path: Path, module : Optional[str] = None):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(PAGE_PACKAGE_TEMPLATE.format(
            flags=get_page_package_flags(package_version, module)
        ))


def link_latest_package_dir(package_dir: Path, link_path: Path):
    os.makedirs(package_dir, exist_ok=True)
    link_path.symlink_to(package_dir, target_is_directory=True)


def copy_package_readme(package_readme: Path, output_path: Path):
    if package_readme.is_file():
        shutil.copy(package_readme, output_path)


def iter_package_modules(package_dir: Path, elm_package: Dict) -> Iterator[ModuleName]:
    for source_dir_name in elm_package['source-directories']:
        source_dir = package_dir / source_dir_name
        elm_files = source_dir.glob('**/*.elm')
        for elm_file in elm_files:
            if elm_file.relative_to(package_dir).parts[0] == 'elm-stuff':
                continue
            rel_path = elm_file.relative_to(source_dir)
            module_name = '.'.join(rel_path.parent.parts + (rel_path.stem,))
            yield module_name


def load_elm_package(path: str):
    with open(path) as f:
        return json.load(f)


def build_elm_package_docs(output_dir: str, elm_package_path: str):
    package_dir = Path(elm_package_path).parent

    elm_package = load_elm_package(elm_package_path)
    package_version = get_package_version(elm_package)
    package_identifier = '/'.join((package_version.user, package_version.project, package_version.version))

    package_docs_root = Path(output_dir) / 'packages' / package_version.user / package_version.project / package_version.version

    # package index page
    package_index_output = package_docs_root / 'index.html'
    yield {
        'basename': 'package_page:' + package_identifier,
        'actions': [(build_package_page, (package_version, package_index_output))],
        'targets': [package_index_output],
        #'file_deps': [module['source_file']] #todo
    }

    # todo: yield task for package documentation.json: expose all modules based on pattern if project package

    # package readme
    readme_filename = 'README.md'
    package_readme = package_dir / readme_filename
    output_readme_path = package_docs_root / readme_filename
    yield {
        'basename': 'package_readme:' + package_identifier,
        'actions': [(copy_package_readme, (package_readme, output_readme_path))],
        'targets': [output_readme_path],
        'file_deps': [package_readme],
    }

    # link from /latest
    latest_path = package_docs_root.parent / 'latest'
    yield {
        'basename': 'package_latest_link:' + package_identifier,
        'actions': [(link_latest_package_dir, (package_docs_root, latest_path))],
        'targets': [latest_path],
        #'file_deps': [], # todo
    }

    # todo: make mount point configurable: prepend path in page package html and in generated js

    # module pages
    package_modules = list(iter_package_modules(package_dir, elm_package))
    for module in package_modules:
        module_output = package_docs_root / module.replace('.', '-')
        yield {
            'basename': 'module_page:{}:{}'.format(package_identifier, module),
            'actions': [(build_package_page, (package_version, module_output, module))],
            'targets': [module_output],
            #'file_deps': [module['source_file']] #todo
        }



def create_tasks(output_dir, elm_packages):
    # todo: yield task for building elm apps and copying assets
    # todo: yield task for all-packages
    # todo: yield task for new-packages

    for elm_package in elm_packages:
        for task in build_elm_package_docs(output_dir, elm_package):
            yield task



def task_elm_docs():
    elm_packages = [
        'elm-package.json',
        'ui/elm-package.json',
    ]
    create_tasks(elm_packages)
