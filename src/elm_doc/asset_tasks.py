import os
import os.path
from collections import ChainMap
from tempfile import TemporaryDirectory
from pathlib import Path
import subprocess
import shutil

from retrying import retry

from elm_doc import elm_platform
from elm_doc import elm_package
from elm_doc import node_modules
from elm_doc.decorators import capture_subprocess_error


codeshifter = os.path.normpath(os.path.join(os.path.dirname(__file__), 'native', 'prepend_mountpoint.js'))


@capture_subprocess_error
def build_assets(output_path: Path, mount_point: str = ''):
    tarball = 'https://api.github.com/repos/elm-lang/package.elm-lang.org/tarball/0.18.0'
    with TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)

        # download package.elm-lang.org repo
        subprocess.check_call(
            'curl -L -s {tarball} | tar xz --strip-components 1'.format(tarball=tarball),
            shell=True,
            cwd=str(root_path),
        )
        package = elm_package.from_path(root_path)

        # install elm
        elm_platform.install(root_path, package.elm_version)
        node_modules.add('jscodeshift', cwd=str(root_path))
        _install_elm_packages(str(root_path))

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
                cwd=str(root_path),
            )

        env = dict(ChainMap(
            os.environ,
            {'ELM_DOC_MOUNT_POINT': mount_point},
        ))
        codeshift_command = [
            './node_modules/.bin/jscodeshift',
            '--transform',
            codeshifter,
            str(artifacts_path)]
        proc = subprocess.Popen(
            codeshift_command,
            env=env,
            cwd=str(root_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True)
        out, err = proc.communicate()
        # todo: jscodeshift doesn't exit with 1 when there's an error
        if ('ERROR' in out) or ('ERROR' in err) or (proc.returncode != 0):
            raise subprocess.CalledProcessError(
                proc.returncode, codeshift_command, out, err)

        # copy artifacts
        shutil.rmtree(str(output_path / 'artifacts'), ignore_errors=True)
        shutil.copytree(str(artifacts_path), str(output_path / 'artifacts'))

        # copy assets
        shutil.rmtree(str(output_path / 'assets'), ignore_errors=True)
        shutil.copytree(str(root_path / 'assets'), str(output_path / 'assets'))


@retry(
    retry_on_exception=lambda e: isinstance(e, subprocess.CalledProcessError),
    wait_exponential_multiplier=1000,  # Wait 2^x * 1000 milliseconds between each retry,
    wait_exponential_max=30 * 1000,  # up to 30 seconds, then 30 seconds afterwards
    stop_max_attempt_number=10)
def _install_elm_packages(root_path):
    subprocess.check_call(
        ['./node_modules/.bin/elm-package', 'install', '--yes'],
        cwd=root_path,
    )
