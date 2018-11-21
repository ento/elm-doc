import os
import os.path
from collections import ChainMap
from tempfile import TemporaryDirectory
from pathlib import Path
import subprocess
import shutil

from retrying import retry

from elm_doc import elm_platform
from elm_doc import elm_project
from elm_doc import node_modules
from elm_doc.decorators import capture_subprocess_error


codeshifter = os.path.normpath(os.path.join(os.path.dirname(__file__), 'native', 'prepend_mountpoint.js'))


def _package_elm_lang_org_ref_to_download(elm_version):
    refs = {
        '0.19.0': 'a8b9f08c66ddc2a5f784bedbc943f48f6efa9be3'
    }
    return refs.get(elm_version, refs['0.19.0'])


@capture_subprocess_error
def build_assets(elm_version: elm_project.ExactVersion, output_path: Path, mount_point: str = ''):
    ref = _package_elm_lang_org_ref_to_download(elm_version)
    tarball = 'https://api.github.com/repos/elm/package.elm-lang.org/tarball/{}'.format(ref)
    with TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)

        # download package.elm-lang.org repo
        subprocess.run(
            'curl -L -s {tarball} | tar xz --strip-components 1'.format(tarball=tarball),
            shell=True,
            cwd=str(root_path),
            check=True,
            capture_output=True,
        )
        package = elm_project.from_path(root_path)

        # install elm
        elm_platform.install(root_path, package.elm_version)
        node_modules.add('jscodeshift', cwd=str(root_path))

        # make artifacts
        artifacts_path = root_path / 'artifacts'
        os.makedirs(str(artifacts_path))

        # see:
        # https://github.com/elm/package.elm-lang.org/blob/a8b9f08c66ddc2a5f784bedbc943f48f6efa9be3/src/backend/Artifacts.hs#L34
        subprocess.run(
            ['./node_modules/.bin/elm',
             'make',
             'src/frontend/Main.elm',
             '--optimize',
             '--output',
             'artifacts/elm.js',
             ],
            cwd=str(root_path),
            check=True,
            capture_output=True,
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
