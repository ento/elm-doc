import os
from tempfile import TemporaryDirectory
from pathlib import Path
import urllib.request
import tarfile
import subprocess
import shutil

from elm_docs import elm_platform
from elm_docs import elm_package


def build_assets(output_path: Path):
    tarball = 'https://api.github.com/repos/elm-lang/package.elm-lang.org/tarball'
    with TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)

        # download package.elm-lang.org repo
        subprocess.check_call(
            'curl -L -s {tarball} | tar xz --strip-components 1'.format(tarball=tarball),
            shell=True,
            cwd=root_path)
        package = elm_package.from_path(root_path)

        # install elm
        elm_platform.install(root_path, package.elm_version)
        subprocess.check_call(
            ['./node_modules/.bin/elm-package', 'install', '--yes'],
            cwd=root_path)

        # make artifacts
        artifacts_path = root_path / 'artifacts'
        os.makedirs(artifacts_path)

        # I know there's only one source directory!
        frontend_pages = Path(package.source_directories[0]) / 'Page'
        for main_elm in root_path.glob(str(frontend_pages / '*.elm')):
            basename = main_elm.stem
            subprocess.check_call(
                ['./node_modules/.bin/elm-make',
                 main_elm,
                 '--output',
                 'artifacts/Page-{0}.js'.format(basename)],
                cwd=root_path)

        # copy artifacts and assets
        shutil.copytree(artifacts_path, output_path / 'artifacts')
        shutil.copytree(root_path / 'assets', output_path / 'assets')
