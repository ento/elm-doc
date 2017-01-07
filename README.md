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

You can further specify `--elm-make` to avoid the overhead of installing Elm:

    $ elm-doc . --output docs \
        --elm-make ui/node_modules/elm/Elm-Platform/*/.cabal-sandbox/bin/elm-make

`--validate` can check if you have all the necessary documentation in place:

    $ elm-doc . \
        --elm-make ui/node_modules/elm/Elm-Platform/*/.cabal-sandbox/bin/elm-make
        --validate

`elm-doc` assumes you're working on an app, not a package; it will try to generate
documentation for all modules regardless of what you have in `exposed-modules`.
You can `--exclude` modules from the list of all modules:

    $ elm-doc . --output docs \
        --elm-make ui/node_modules/elm/Elm-Platform/*/.cabal-sandbox/bin/elm-make
        --exclude 'Page.*'

For a full list of options, see:

    $ elm-doc --help

## Installation

    $ pip install --upgrade pip
    $ pip install elm-doc
