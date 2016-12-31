import pytest
from click.testing import CliRunner
from elm_doc import cli


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
    project_path = tmpdir.mkdir('frontend')
    make_elm_project(elm_version, project_path, copy_elm_stuff=True)
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main, ['--output', 'docs', 'frontend'])
        assert not result.exception, result.output
        assert result.exit_code == 0
