import os
import os.path
import shutil

import click
import magic
from doit.doit_cmd import DoitMain
from doit.cmd_base import ModuleTaskLoader

from elm_doc.tasks import create_tasks


class DoitException(click.ClickException):
    def __init__(self, message, exit_code):
        click.ClickException.__init__(self, message)
        self.exit_code = exit_code


def validate_mount_at(ctx, param, value):
    if len(value) == 0 or value.startswith('/'):
        return value
    else:
        raise click.BadParameter('should be an absolute path, like /{}'.format(value))


def validate_elm_make(ctx, param, value):
    if value is None:
        return value

    realpath = os.path.realpath(value)
    if not os.path.isfile(realpath):
        realpath = shutil.which(value)

    if realpath is None or not os.path.isfile(realpath):
        raise click.BadParameter('{} not found'.format(value))

    elm_make_mimetype = magic.from_file(realpath, mime=True)
    if not elm_make_mimetype.startswith('text'):
        return value

    perhaps_binwrap_of = os.path.normpath(
        os.path.join(
            os.path.dirname(realpath),
            os.pardir,
            'elm',
            'Elm-Platform',
            '*',
            '.cabal-sandbox',
            'bin',
            'elm-make'))
    raise click.BadParameter('''should be the real elm-make binary; this looks like a text file.
if you installed Elm through npm, then try {}'''.format(perhaps_binwrap_of))


@click.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.option('--output', '-o',
              metavar='dir')
@click.option('--elm-make',
              metavar='path/to/elm-make',
              callback=validate_elm_make,
              help=('specify which elm-make to use. if not specified, '
                    'elm will be installed afresh in a temporary directory'))
@click.option('--mount-at',
              metavar='/path',
              default='',
              callback=validate_mount_at,
              help='url path at which the docs will be served')
@click.option('--exclude', '-x',
              metavar='module1,module2.*',
              help='comma-separated fnmatch pattern of modules to exclude')
@click.option('--validate/--no-validate',
              default=False,
              help='validate all doc comments are in place without generating docs')
@click.argument('project_path')
@click.argument('doit_args', nargs=-1, type=click.UNPROCESSED)
def main(output, elm_make, mount_at, exclude, validate, project_path, doit_args):
    """Generate static documentation for your Elm project"""

    if not validate and output is None:
        raise click.BadParameter('please specify --output directory')

    def task_build():
        exclude_modules = exclude.split(',') if exclude else []
        return create_tasks(
            os.path.abspath(project_path),
            os.path.abspath(output) if output is not None else None,
            elm_make=os.path.abspath(elm_make) if elm_make is not None else None,
            exclude_modules=exclude_modules,
            mount_point=mount_at,
            validate=validate)

    result = DoitMain(ModuleTaskLoader(locals())).run(doit_args)
    if result is not None and result > 0:
        raise DoitException('', result)


if __name__ == '__main__':
    main()
