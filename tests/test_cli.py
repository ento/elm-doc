import pytest
from click.testing import CliRunner
from elm_doc import cli
import elm_doc


@pytest.fixture
def runner():
    return CliRunner()


def test_cli(runner, tmpdir):
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main)
        assert result.exception
        assert result.exit_code == 2


def test_cli_in_empty_project(tmpdir, runner):
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main, ['--output', 'docs', '.'])
        assert result.exception
        assert result.exit_code != 0


def test_cli_in_real_project(tmpdir, runner, overlayer, make_elm_project):
    elm_version = '0.18.0'
    make_elm_project(elm_version, tmpdir, copy_elm_stuff=True)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main, ['--output', output_dir, '.'])
        assert not result.exception
        assert result.exit_code == 0
