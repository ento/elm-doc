from typing import List, Optional
import os
import os.path
from pathlib import Path
import json
import shutil
from tempfile import TemporaryDirectory
import subprocess

from doit.tools import create_folder

from elm_docs import elm_package_overlayer_path
from elm_docs import elm_package
from elm_docs.elm_package import ElmPackage, ModuleName


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

def get_page_package_flags(package: ElmPackage, module : Optional[str] = None):
    flags = {
        'user': package.user,
        'project': package.project,
        'version': package.version,
        'allVersions': [package.version],
        'moduleName': module,
    }
    return flags


def build_package_page(package: ElmPackage, output_path: Path, module : Optional[str] = None):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(PAGE_PACKAGE_TEMPLATE.format(
            flags=get_page_package_flags(package, module)
        ))


def link_latest_package_dir(package_dir: Path, link_path: Path):
    os.makedirs(package_dir, exist_ok=True)
    link_path.symlink_to(package_dir, target_is_directory=True)


def copy_package_readme(package_readme: Path, output_path: Path):
    if package_readme.is_file():
        shutil.copy(package_readme, output_path)


def build_package_docs_json(package: ElmPackage, output_path: Path, package_modules: List[ModuleName]):
    here = os.path.abspath(os.path.dirname(__file__))
    # todo: use my own elm
    elm_make = os.environ['ELM_MAKE']
    elm_package_with_exposed_modules = {**package.description, **{'exposed-modules': package_modules}}
    overlayer_path = elm_package_overlayer_path()
    with TemporaryDirectory() as tmpdir:
        elm_package_path = Path(tmpdir) / elm_package.DESCRIPTION_FILENAME
        with open(elm_package_path, 'w') as f:
            json.dump(elm_package_with_exposed_modules, f)
        env = {
            **os.environ,
            **{
                'USE_ELM_PACKAGE': elm_package_path,
                'INSTEAD_OF_ELM_PACKAGE': elm_package.description_path(package),
                'DYLD_INSERT_LIBRARIES': overlayer_path,
            }
        }
        subprocess.check_call([elm_make, '--yes', '--docs', output_path], cwd=package.path, env=env)


def create_package_tasks(output_path: Path, package: ElmPackage, exclude_modules: List[str]):
    basename = lambda name: '{}:{}/{}'.format(name, package.name, package.version)

    package_docs_root = output_path / 'packages' / package.user / package.project / package.version
    package_modules = list(elm_package.iter_package_modules(package, exclude_modules))

    # package documentation.json
    docs_json_path = package_docs_root / 'documentation.json'
    yield {
        'basename': basename('package_docs_json'),
        'actions': [(create_folder, (package_docs_root,)),
                    (build_package_docs_json, (package, docs_json_path, package_modules))],
        'targets': [docs_json_path],
        #'file_dep': [all_elm_files_in_source_dirs] # todo
    }

    # package index page
    package_index_output = package_docs_root / 'index.html'
    yield {
        'basename': basename('package_page'),
        'actions': [(build_package_page, (package, package_index_output))],
        'targets': [package_index_output],
        #'file_dep': [module['source_file']] #todo
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
        #'file_dep': [], # todo
        'uptodate': [True]
    }

    # todo: make mount point configurable: prepend path in page package html and in generated js

    # module pages
    for module in package_modules:
        module_output = package_docs_root / module.replace('.', '-')
        yield {
            'basename': basename('module_page') + ':' + module,
            'actions': [(build_package_page, (package, module_output, module))],
            'targets': [module_output],
            #'file_dep': [module['source_file']] #todo
        }
