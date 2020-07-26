#!/usr/bin/env bash

set -exuo pipefail

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
poetry run tox -v -e "py${PYTHON_VERSION:?}${TOX_EXTRA_ENVS:-}"

# format coverage report
if [ "$REPORT_COVERAGE" == "true" ]; then
    poetry run coverage xml
fi

# check installability
virtualenv env
. env/bin/activate
pip install --upgrade pip
pip install .
python -c 'import elm_doc.tasks.assets; assert elm_doc.tasks.assets.tarball.exists()'

# print diagnostic info
pip list
python -c 'import elm_doc; print(elm_doc.__file__)'
elm-doc --help
