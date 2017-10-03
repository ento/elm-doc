# elm-doc

Generate static documentation of your Elm project.

Requires Python >= 3.4, yarn, and macOS or Linux.

## Usage

Simplest invocation:

    $ elm-doc . --output docs

To view the generated docs, you'll need an HTTP server that can detect mimetypes
based on file contents, rather than file extensions.

I personally use [spark](https://github.com/rif/spark):

    $ (cd doc && ~/go/bin/spark)

You can further point `--elm-make` at your existing installation of `elm-make` binary
to avoid the overhead of installing Elm:

    $ elm-doc . --output docs \
        --elm-make ui/node_modules/elm/Elm-Platform/*/.cabal-sandbox/bin/elm-make

`--validate` can check if you have all the necessary documentation in place:

    $ elm-doc . \
        --elm-make ui/node_modules/elm/Elm-Platform/*/.cabal-sandbox/bin/elm-make \
        --validate

`elm-doc` assumes you're working on an app, not a package; it will try to generate
documentation for all modules regardless of what you have in the `exposed-modules` of
your `elm-package.json`.

You can `--exclude` modules by using [fnmatch](https://docs.python.org/3/library/fnmatch.html)
patterns:

    $ elm-doc . --output docs \
        --elm-make ui/node_modules/elm/Elm-Platform/*/.cabal-sandbox/bin/elm-make \
        --exclude '*.Private.*,Blacklist.*'

You can also specify which files and directories to include in the list of modules:

    $ elm-doc . --output docs \
        --elm-make ui/node_modules/elm/Elm-Platform/*/.cabal-sandbox/bin/elm-make \
        src/Whitelist src/Main.elm

Note that the `--exclude` flag takes no effect if you explicitly specify which
files to include, unless you add the `--force-exclusion` flag:

    $ elm-doc . --output docs \
        --elm-make ui/node_modules/elm/Elm-Platform/*/.cabal-sandbox/bin/elm-make \
        --exclude '*.Private.*,Blacklist.*' \
        --force-exclusion \
        src/Whitelist src/Main.elm

For a full list of options, see:

    $ elm-doc --help

## Installation

Make sure you have [yarn](https://yarnpkg.com/en/docs/install).

In a Python (>=3.4) [virtualenv](https://docs.python.org/3.6/library/venv.html#creating-virtual-environments) or globally:

    $ pip install --upgrade pip setuptools
    $ pip install elm-doc

Dependency on `python-magic` may require you to [install more stuff](https://github.com/ahupp/python-magic#dependencies).

## Development

Running tests:

    $ pip install -r dev-requirements.txt
    $ tox -e py35,...
