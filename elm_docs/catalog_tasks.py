from typing import List
from pathlib import Path

from elm_docs.elm_package import ElmPackage
from elm_docs import elm_package


INDEX_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <link rel="shortcut icon" size="16x16, 32x32, 48x48, 64x64, 128x128, 256x256" href="/assets/favicon.ico">
    <link rel="stylesheet" href="/assets/highlight/styles/default.css">
    <link rel="stylesheet" href="/assets/style.css">
    <script src="/assets/highlight/highlight.pack.js"></script>
    <script src="/artifacts/Page-Catalog.js"></script>
  </head>
  <body>
  <script>
    var page = Elm.Page.Catalog.fullscreen();
  </script>
  </body>
</html>
'''

def write_index_page(output_path: Path):
    with open(output_path, 'w') as f:
        f.write(INDEX_PAGE_TEMPLATE)



def write_all_packages(packages: List[ElmPackage], output_path: Path):
    all_packages = map(
        lambda package: {
            'name': package.name,
            'summary': package.summary,
            'versions': [package.version],
        },
        packages)
    with open(output_path, 'w') as f:
        json.dump(list(all_packages), f)


def write_new_packages(packages: List[ElmPackage], output_path: Path):
    new_packages = map(lambda package: package.name, packages)
    with open(output_path, 'w') as f:
        json.dump(list(new_packages), f)


def create_catalog_tasks(packages: List[ElmPackage], output_path: Path):
    # index
    index_path = output_path / 'index.html'
    yield {
        'basename': 'index',
        'actions': [(write_index_page, (index_path,))],
        'targets': [index_path],
        'uptodate': [True],
    }

    # all-packages
    all_packages_path = output_path / 'all-packages'
    yield {
        'basename': 'all_packages',
        'actions': [(write_all_packages, (packages, all_packages_path))],
        'targets': [all_packages_path],
        'file_dep': list(map(elm_package.description_path, packages)),
    }

    # new-packages
    new_packages_path = output_path / 'new-packages'
    yield {
        'basename': 'new_packages',
        'actions': [(write_new_packages, (packages, new_packages_path))],
        'targets': [new_packages_path],
        'file_dep': list(map(elm_package.description_path, packages)),
    }
