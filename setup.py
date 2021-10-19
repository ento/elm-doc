# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['elm_doc', 'elm_doc.elm_parser', 'elm_doc.tasks']

package_data = \
{'': ['*'], 'elm_doc': ['assets/*']}

install_requires = \
['attrs>=19.3.0,<20.0.0',
 'cachecontrol>=0.12.6,<0.13.0',
 'click>=7.1.2,<8.0.0',
 'doit>=0.32.0,<0.33.0',
 'parsy>=1.3.0,<2.0.0',
 'requests>=2.24.0,<3.0.0',
 'retrying>=1.3.3,<2.0.0']

entry_points = \
{'console_scripts': ['elm-doc = elm_doc.cli:main']}

setup_kwargs = {
    'name': 'elm-doc',
    'version': '1.0.0',
    'description': 'Generate static documentation for your Elm application',
    'long_description': "# elm-doc\n\nGenerate static documentation of your Elm application project.\n\nRequires Python >= 3.6, rsync >= 2.6.7, and macOS or Linux. It may work on Windows but it's untested.\n\nSupported Elm versions:\n\n- elm-doc version < 1.0: Elm 0.18\n- elm-doc version >= 1.0.0: Elm 0.19\n\n## Usage\n\nSimplest invocation:\n\n    $ elm-doc . --output docs --fake-license 'SPDX license name'\n\nThe license name is required because elm-doc uses the official Elm binary to\nvalidate and generate docs; the official Elm binary only generates\ndocs for a package project, and a package project requires a license to be set.\nWhile the license name will not be part of the generated doc, it will be\nassociated with the project in the temporary elm.json file elm-doc generates\nduring the build / validation.\n\nDo no use elm-doc if you'd rather not risk the legal consequences of this fact.\n(IANAL: my understanding is OSS license doesn't take effect unless you distribute\nthe code it's attached to.)\n\nTo view the generated docs, you'll need an HTTP server that can detect mimetypes\nbased on file contents, rather than file extensions.\n\nI personally use [spark](https://github.com/rif/spark):\n\n    $ (cd doc && ~/go/bin/spark)\n\nYou can specify other attributes of the project with `--fake-user`, `--fake-project`,\nand `--fake-version`.\n\nelm-doc creates a build directory named `.elm-doc` at the root of the project.\nYou may want to ignore it in your SCM config, or you can change its path with `--build-dir`.\n\n`--validate` can check if you have all the necessary documentation in place:\n\n    $ elm-doc . \\\n        --elm-path ./node_modules/.bin/elm \\\n        --validate\n\n`elm-doc` assumes you're working on an app, not a package; it will try to generate\ndocumentation for all modules found in the application source directories.\n\nYou can `--exclude-modules` by using [fnmatch](https://docs.python.org/3/library/fnmatch.html)\npatterns:\n\n    $ elm-doc . --output docs --fake-license 'SPDX license name' \\\n        --exclude-modules '*.Private.*,Blacklist.*'\n\nor `--exclude-source-directories` entirely:\n\n    $ elm-doc . --output docs --fake-license 'SPDX license name' \\\n        --exclude-source-directories generated\n\nYou can also specify which files and directories to _include_ in the list of modules:\n\n    $ elm-doc . --output docs \\\n        src/Whitelist src/Main.elm\n\nNote that the `--exclude` flag takes no effect if you explicitly specify which\nfiles to include, unless you add the `--force-exclusion` flag:\n\n    $ elm-doc . --output docs --fake-license 'SPDX license name' \\\n        --exclude-modules '*.Private.*,Blacklist.*' \\\n        --force-exclusion \\\n        src/Whitelist src/Main.elm\n\nFor a full list of options, see:\n\n    $ elm-doc --help\n\n## Installation\n\nIn a Python (>=3.6) [virtualenv](https://docs.python.org/3.6/library/venv.html#creating-virtual-environments) or globally:\n\n    $ pip install --upgrade pip setuptools\n    $ pip install elm-doc\n\n## How it works\n\nThis is the rough build process:\n\n- Generate a temporary elm.json file in the build directory\n  - Change the type to `package` and restructure / reformat to match the schema for a package project's elm.json\n  - Populate `--fake-*` fields, including the license: these are required for a package project but not included in an application project's elm.json\n  - Add dependencies that are listed as popular packages in the sidebar, making HTTP requests to look up the latest versions\n  - This means the actual build / validation process will have its own elm-stuff directory\n- Copy source files into the build directory's `src` directory using rsync\n  - An application project supports multiple source directories, while a package project supports only `src`\n- For each file that was copied, rewrite port delcarations to be normal functions\n  - This is needed because ports are not allowed in package projects\n- Run `elm make` with the `--doc` flag on\n- If validating docs, exit here\n- Generate the top page of the package, individual module pages, and other files required for the package website to function\n- For each dependency, copy docs.json from the per-user package cache. This is generally in `~/.elm`\n- For each dependency, also generate files required for the package website to function\n- Generate site-wide search index in a JSON format that the frontend expects\n- Generate help pages hosted by the package website\n- Extract frontend code that is prebuilt and distributed as part of the elm-doc Python package\n  - It is a [fork](https://github.com/ento/package.elm-lang.org/tree/elm-doc) of the elm/package.elm-lang.org repo that takes a flag that specifies which URL path the frontend app is mounted at\n- These are all implemented as [doit](https://github.com/pydoit/doit) tasks\n\n## Development\n\nRunning tests:\n\n    $ nix-shell\n    $ poetry install\n    $ poetry run tox -e py36,...\n\nUpdating the prebuilt frontend code and test fixture:\n\n    $ poetry run doit\n",
    'author': 'ento',
    'author_email': 'ento+github@i.pearlwaffles.xyz',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/ento/elm-doc',
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.6,<4.0',
}


setup(**setup_kwargs)
