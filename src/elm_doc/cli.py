import sys
import os
import os.path
import shutil
import subprocess
from pathlib import Path
import functools
import re

import click
from doit.doit_cmd import DoitMain
from doit.cmd_base import ModuleTaskLoader
from doit.runner import ERROR

from elm_doc.tasks import build_task_creators
from elm_doc.elm_project import ProjectConfig


class DoitException(click.ClickException):
    def __init__(self, message, exit_code):
        click.ClickException.__init__(self, message)
        self.exit_code = exit_code


def validate_mount_at(ctx, param, value):
    if len(value) == 0 or value.startswith('/'):
        return value
    else:
        raise click.BadParameter('should be an absolute path, like /{}'.format(value))


def validate_elm_path(ctx, param, value):
    if value is None:
        return value

    realpath = os.path.realpath(value)
    if not os.path.isfile(realpath):
        realpath = shutil.which(value)

    if realpath is None or not os.path.isfile(realpath):
        raise click.BadParameter('{} not found'.format(value))

    return value


REQUIRED_RSYNC_VERSION = (2, 6, 7)


def check_rsync_version() -> bool:
    output = subprocess.check_output(['rsync', '--version'], universal_newlines=True)
    first_line = output.splitlines()[0]
    match = re.search(r'version (?P<major>\d)\.(?P<minor>\d)\.(?P<patch>\d)', first_line)
    if not match:
        raise click.Abort(
            'could not extract the version of rsync from: {}'.format(first_line))
    version = (int(match.group('major')),
               int(match.group('minor')),
               int(match.group('patch')))
    return version >= REQUIRED_RSYNC_VERSION


def _resolve_path(path: str) -> Path:
    # not using Path.resolve() for now because we don't expect strict
    # existence checking. maybe we should.
    return Path(os.path.normpath(os.path.abspath(path)))


def _translate_click_exception_exit_code(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except click.ClickException as e:
            if not isinstance(e, DoitException):
                e.exit_code = ERROR
            raise e
    return wrapper


class LazyOutfile:
    def write(self, *args, **kwargs):
        sys.stdout.write(*args, **kwargs)


@click.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.option('--output', '-o',
              metavar='dir')
@click.option('--build-dir',
              metavar='dir',
              help=('temporary build directory. source files will be copied here. '
                    'default: <project_path>/.elm-doc/'))
@click.option('--elm-path',
              metavar='path/to/elm',
              callback=validate_elm_path,
              help=('specify which elm binary to use. if not specified, '
                    'elm will be installed afresh in a temporary directory'))
@click.option('--mount-at',
              metavar='/path',
              default='',
              callback=validate_mount_at,
              help='url path at which the docs will be served')
@click.option('--exclude-modules', '-x',
              metavar='module1,module2.*',
              help='comma-separated fnmatch pattern of modules to exclude from the list of included modules')
@click.option('--exclude-source-directories', '-X',
              metavar='dir1,dir2',
              help='comma-separated paths of source-directories to exclude from the list of included modules')
@click.option('--fake-user',
              metavar='GitHub user name',
              default='user',
              help='User name to use as part of the package name of the project as listed in the generated docs')
@click.option('--fake-project',
              metavar='GitHub repo name',
              default='project',
              help='Project name to use as part of the package name of the project as listed in the generated docs')
@click.option('--fake-version',
              metavar='Semver version string',
              default='1.0.0',
              help='Version of the project as listed in the generated docs')
@click.option('--fake-summary',
              metavar='Project summary',
              default='project summary',
              help='Summary of the project as listed in the generated docs')
@click.option('--fake-license',
              metavar='OSI-approved SPDX liense',
              required=True,
              help='License of the project to tell the Elm compiler  when generating docs')
@click.option('--force-exclusion/--no-force-exclusion',
              default=False,
              help=('force excluding modules specified by --exclude-modules and '
                    '--exclude-source-directories even if they are explicitly '
                    'specified in include_paths'))
@click.option('--validate/--no-validate',
              default=False,
              help='validate all doc comments are in place without generating docs')
@click.option('--doit-args',
              help='options to pass to doit.doit_cmd.DoitMain.run')
@click.argument('project_path')
@click.argument('include_paths', nargs=-1)
@_translate_click_exception_exit_code
def main(
        output,
        build_dir,
        elm_path,
        mount_at,
        exclude_modules,
        exclude_source_directories,
        force_exclusion,
        fake_user,
        fake_project,
        fake_version,
        fake_summary,
        fake_license,
        validate,
        doit_args,
        project_path,
        include_paths):
    """Generate static documentation for your Elm project"""

    if not shutil.which('rsync'):
        raise click.UsageError('this program requires rsync')

    if not check_rsync_version():
        raise click.UsageError('this program requires rsync version {} or greater'
                               .format('.'.join(REQUIRED_RSYNC_VERSION)))

    if not validate and output is None:
        raise click.BadParameter('please specify --output directory')

    resolved_include_paths = [_resolve_path(path) for path in include_paths]
    exclude_modules = exclude_modules.split(',') if exclude_modules else []
    exclude_source_directories = exclude_source_directories.split(',') if exclude_source_directories else []
    project_config = ProjectConfig(
        include_paths=resolved_include_paths,
        exclude_modules=exclude_modules,
        exclude_source_directories=exclude_source_directories,
        force_exclusion=force_exclusion,
        fake_user=fake_user,
        fake_project=fake_project,
        fake_version=fake_version,
        fake_summary=fake_summary,
        fake_license=fake_license,
    )

    task_creators = build_task_creators(
        _resolve_path(project_path),
        project_config,
        _resolve_path(output) if output is not None else None,
        build_path=_resolve_path(build_dir) if build_dir is not None else None,
        elm_path=_resolve_path(elm_path) if elm_path is not None else None,
        mount_point=mount_at,
        validate=validate)

    extra_config = {'GLOBAL': {'outfile': LazyOutfile()}}
    result = DoitMain(ModuleTaskLoader(task_creators), extra_config=extra_config).run(
        doit_args.split(' ') if doit_args else [])
    if result is not None and result > 0:
        raise DoitException('see output above', result)


if __name__ == '__main__':
    main()
