#!/usr/bin/env bash

set -euo pipefail

poetry install
poetry run doit --verbosity 2

if [ ! -z "$(git status --porcelain)" ]; then
  git status
  python tests/dump_modified_tarballs.py
  echo Tasks in dodo.py created files untracked by git or modified files tracked by git.
  echo See git status above.
  exit 1
fi

# run tests
poetry run tox -v -e "py${PYTHON_VERSION:?}"

# check installability
python -m venv env
. env/bin/activate
pip install --upgrade pip
pip install .
python -c 'import elm_doc.asset_tasks; assert elm_doc.asset_tasks.tarball.exists()'

# print diagnostic info
pip list
python -c 'import elm_doc; print(elm_doc.__file__)'
elm-doc --help
