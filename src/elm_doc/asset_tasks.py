import os
import os.path
from collections import ChainMap
from tempfile import TemporaryDirectory
from pathlib import Path
import subprocess
import shutil

from elm_doc import elm_platform
from elm_doc import elm_package
from elm_doc import node_modules


codeshifter = os.path.normpath(os.path.join(os.path.dirname(__file__), 'native', 'prepend_mountpoint.js'))


def build_assets(output_path: Path, mount_point: str = ''):
    tarball = 'https://api.github.com/repos/elm-lang/package.elm-lang.org/tarball'
    with TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)

        # download package.elm-lang.org repo
        subprocess.check_call(
            'curl -L -s {tarball} | tar xz --strip-components 1'.format(tarball=tarball),
            shell=True,
            cwd=str(root_path))
        package = elm_package.from_path(root_path)

        # install elm
        elm_platform.install(root_path, package.elm_version)
        node_modules.add('jscodeshift', cwd=str(root_path))
        subprocess.check_call(
            ['./node_modules/.bin/elm-package', 'install', '--yes'],
            cwd=str(root_path))

        # make artifacts
        artifacts_path = root_path / 'artifacts'
        os.makedirs(str(artifacts_path))

        # I know there's only one source directory!
        frontend_pages = Path(package.source_directories[0]) / 'Page'
        for main_elm in root_path.glob(str(frontend_pages / '*.elm')):
            basename = main_elm.stem
            subprocess.check_call(
                ['./node_modules/.bin/elm-make',
                 str(main_elm),
                 '--output',
                 'artifacts/Page-{0}.js'.format(basename)],
                cwd=str(root_path))

        env = dict(ChainMap(
            os.environ,
            {'ELM_DOC_MOUNT_POINT': mount_point},
        ))
        output = subprocess.check_output(
            ['./node_modules/.bin/jscodeshift',
             '--transform',
             codeshifter,
             str(artifacts_path)],
            env=env,
            cwd=str(root_path),
            stderr=subprocess.STDOUT,
            universal_newlines=True)
        # todo: jscodeshift doesn't exit with 1 when there's an error
        assert 'ERROR' not in output, output

        # copy artifacts and assets
        shutil.copytree(str(artifacts_path), str(output_path / 'artifacts'))
        shutil.copytree(str(root_path / 'assets'), str(output_path / 'assets'))
