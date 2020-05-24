import os
from collections import namedtuple
from subprocess import run
from pathlib import Path
import shlex
import tempfile


Tarball = namedtuple('Tarball', ('path', 'basename'))


def tarball_from_path(path: str) -> Tarball:
    basename = '-'.join(path.split(os.sep))
    return Tarball(Path(path).resolve(), basename)


TARBALLS = list(map(tarball_from_path, [
    'src/elm_doc/assets/assets.tar.gz',
    'tests/fixtures/0.19.0-elm-core.tar.gz',
    'tests/fixtures/0.19.1-elm-core.tar.gz',
]))


def main():
    repo = Path('.').resolve()
    with tempfile.TemporaryDirectory() as d:
        os.chdir(d)
        dump_tarballs(suffix='old')
        run(['git', '-C', repo, 'checkout', '.', '--quiet'])
        dump_tarballs(suffix='new')
        diff_dumps('old', 'new')


def dump_tarballs(suffix: str):
    for tarball in TARBALLS:
        output = format_output_filename(tarball, suffix)
        dump_tarball(tarball.path, output)


def format_output_filename(tarball: Tarball, suffix: str) -> str:
    return '{}-{}.txt'.format(tarball.basename, suffix)


def dump_tarball(tarball: Path, output: Path):
    with tempfile.TemporaryDirectory() as d:
        run(['tar', 'xf', tarball, '--directory', d], check=True)
        with open(output, 'w') as f:
            run(' '.join(map(shlex.quote, ('find', '.', '-type', 'f', '-exec', 'md5sum', '{}', ';'))) + '| sort',
                cwd=d,
                shell=True,
                stdout=f)


def diff_dumps(suffix_a: str, suffix_b: str):
    for tarball in TARBALLS:
        a = format_output_filename(tarball, suffix_a)
        b = format_output_filename(tarball, suffix_b)
        print(tarball.path)
        run(['diff', '-u', a, b])


if __name__ == '__main__':
    main()
