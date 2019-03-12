# elm-doc

Generate static documentation of your Elm application project.

Requires Python >= 3.5, rsync >= 2.6.7, and macOS or Linux. It may work on Windows but it's untested.

Supported Elm versions:

- elm-doc version < 1.0: Elm 0.18
- elm-doc version 1.0: Elm 0.19

## Usage

Simplest invocation:

    $ elm-doc . --output docs --fake-license 'SPDX license name'

The license name is required because elm-doc uses the official Elm binary to
validate and generate docs; the official Elm binary only generates
docs for a package project, and a package project requires a license to be set.
While the license name will not be part of the generated doc, it will be
associated with the project in the temporary elm.json file elm-doc generates
during the build / validation.

Do no use elm-doc if you'd rather not risk the legal consequences of this fact.
(IANAL: my understanding is OSS license doesn't take effect unless you distribute
the code it's attached to.)

To view the generated docs, you'll need an HTTP server that can detect mimetypes
based on file contents, rather than file extensions.

I personally use [spark](https://github.com/rif/spark):

    $ (cd doc && ~/go/bin/spark)

You can specify other attributes of the project with `--fake-user`, `--fake-project`,
and `--fake-version`.

elm-doc creates a build directory named `.elm-doc` at the root of the project.
You may want to ignore it in your SCM config, or you can change its path with `--build-dir`.

You can further point `--elm-path` at your existing installation of `elm` binary
to avoid the overhead of installing Elm:

    $ elm-doc . --output docs \
        --elm-path ui/node_modules/.bin/elm

`--validate` can check if you have all the necessary documentation in place:

    $ elm-doc . \
        --elm-path ui/node_modules/.bin/elm \
        --validate

`elm-doc` assumes you're working on an app, not a package; it will try to generate
documentation for all modules found in the application source directories.

You can `--exclude-modules` by using [fnmatch](https://docs.python.org/3/library/fnmatch.html)
patterns:

    $ elm-doc . --output docs \
        --elm-path ui/node_modules/.bin/elm \
        --exclude-modules '*.Private.*,Blacklist.*'

or `--exclude-source-directories` entirely:

    $ elm-doc . --output docs \
        --elm-path ui/node_modules/.bin/elm \
        --exclude-source-directories generated

You can also specify which files and directories to _include_ in the list of modules:

    $ elm-doc . --output docs \
        --elm-path ui/node_modules/.bin/elm \
        src/Whitelist src/Main.elm

Note that the `--exclude` flag takes no effect if you explicitly specify which
files to include, unless you add the `--force-exclusion` flag:

    $ elm-doc . --output docs \
        --elm-path ui/node_modules/.bin/elm \
        --exclude-modules '*.Private.*,Blacklist.*' \
        --force-exclusion \
        src/Whitelist src/Main.elm

For a full list of options, see:

    $ elm-doc --help

## Installation

In a Python (>=3.5) [virtualenv](https://docs.python.org/3.6/library/venv.html#creating-virtual-environments) or globally:

    $ pip install --upgrade pip setuptools
    $ pip install elm-doc

## How it works

This is the rough build process:

- Generate a temporary elm.json file in the build directory
  - Change the type to `package` and restructure / reformat to match the schema for a package project's elm.json
  - Populate `--fake-*` fields, including the license: these are required for a package project but not included in an application project's elm.json
  - Add dependencies that are listed as popular packages in the sidebar, making HTTP requests to look up the latest versions
  - This means the actual build / validation process will have its own elm-stuff directory
- Copy source files into the build directory's `src` directory using [dirsync](https://bitbucket.org/tkhyn/dirsync/)
  - An application project supports multiple source directories, while a package project supports only `src`
- For each file that were copied, rewrite port delcarations to be normal functions
  - This is needed because ports are not allowed in package projects
- Run `elm make` with the `--doc` flag on
- If validating docs, exit here
- Generate the top page of the package, individual module pages, and other files required for the package website to function
- For each dependency, copy docs.json from the per-user package cache. This is generally in `~/.elm`
- For each dependency, also generate files required for the package website to function
- Generate site-wide search index in a JSON format that the frontend expects
- Generate help pages hosted by the package website
- Extract frontend code that is prebuilt and distributed as part of the elm-doc Python package
  - It is a [fork](https://github.com/ento/package.elm-lang.org/tree/elm-doc) of the elm/package.elm-lang.org repo that takes a flag that specifies which URL path the frontend app is mounted at
- These are all implemented as [doit](https://github.com/pydoit/doit) tasks

## Development

Running tests:

    $ pipenv install --dev
    $ pipenv run tox -e py35,...

Updating the prebuild frontend code and test fixture:

    $ pipenv run doit
