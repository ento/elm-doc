'''
'''
import os
import os.path
import json
import pathlib
import urllib.parse


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

def get_page_package_flags(package_version, module=None):
    flags = {
        'user': package_version['user'],
        'project': package_version['project'],
        'version': package_version['version'],
        'allVersions': [package_version['version']],
        'moduleName': module,
    }
    return flags


def get_package_version(elm_package):
    repo_path = pathlib.Path(urllib.parse.urlparse(elm_package['repository']).path)
    return {
        'user': repo_path.parent.stem,
        'project': repo_path.stem,
        'version': elm_package['version'],
    }


def build_package_page(package_data):
    os.makedirs(os.path.dirname(package_data['output']), exist_ok=True)
    with open(package_data['output'], 'w') as f:
        f.write(PAGE_PACKAGE_TEMPLATE.format(
            flags=get_page_package_flags(package_data['package_version'], package_data['module_name'])
        ))


def load_elm_package(path: str):
    with open(path) as f:
        return json.load(f)


def build_elm_package_docs(output_dir: str, elm_package_path: str):
    elm_package = load_elm_package(elm_package_path)
    package_version = get_package_version(elm_package)

    package_docs_root = pathlib.Path(output_dir) / 'packages' / package_version['user'] / package_version['project'] / package_version['version']
    package_root = pathlib.Path(elm_package_path).parent

    # package root page
    package_data = {
        'output': package_docs_root / 'index.html',
        'module_name': None,
        'package_version': package_version,
    }
    yield {
        'basename': 'elm_package_doc:{}/{}'.format(package_version['user'], package_version['project']),
        'actions': [(build_package_page, (package_data,))],
        'targets': [package_data['output']],
        #'file_deps': [module['source_file']] #todo
    }
    # todo: yield task for package documentation.json
    # todo: yield task for package readme.md
    # todo: yield task to link from latest to this version's directory
    # todo: make mount point configurable: prepend path in page package html and in generated js

    # module pages
    for source_dir_name in elm_package['source-directories']:
        source_dir = package_root / source_dir_name
        elm_files = source_dir.glob('**/*.elm')
        for elm_file in elm_files:
            if elm_file.relative_to(package_root).parts[0] == 'elm-stuff':
                continue
            rel_path = elm_file.relative_to(source_dir)
            module_name = '.'.join(rel_path.parent.parts + (rel_path.stem,))
            package_data = {
                'output': package_docs_root / module_name.replace('.', '-'),
                'module_name': module_name,
                'package_version': package_version,
            }
            yield {
                'basename': 'elm_module_doc:{}'.format(elm_file),
                'actions': [(build_package_page, (package_data,))],
                'targets': [package_data['output']],
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
