import click
import os
import os.path
from doit.doit_cmd import DoitMain
from doit.cmd_base import ModuleTaskLoader
from elm_doc.tasks import create_tasks


class DoitException(click.ClickException):
    def __init__(self, message, exit_code):
        click.ClickException.__init__(self, message)
        self.exit_code = exit_code


# todo:: validate mode
@click.command()
@click.option('--output', '-o', required=True)
@click.option('--elm-make', help=('specify which elm-make to use. if not specified, '
                                  'elm will be installed afresh in a temporary directory'))
@click.option('--mount-at', help='url path at which the docs will be served', default='')
@click.option('--exclude', '-x', help='comma-separated fnmatch pattern of modules to exclude')
@click.argument('project_path')
def main(output, elm_make, mount_at, exclude, project_path):
    """Generate your own Elm package documentation site"""
    def task_build():
        if 'ELM_DOC_EXTENSION_PATH' in os.environ:
            import elm_doc
            elm_doc.__path__.append(os.path.abspath(os.environ['ELM_DOC_EXTENSION_PATH']))
        exclude_modules = exclude.split(',') if exclude else []
        return create_tasks(
            os.path.abspath(project_path),
            os.path.abspath(output),
            elm_make=os.path.abspath(elm_make) if elm_make is not None else None,
            exclude_modules=exclude_modules,
            mount_point=mount_at)
    result = DoitMain(ModuleTaskLoader(locals())).run(['--verbosity', '0'])
    if result > 0:
        raise DoitException('', result)


if __name__ == '__main__':
    main()
