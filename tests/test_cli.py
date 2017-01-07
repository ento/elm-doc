import pytest
import json
from click.testing import CliRunner
from elm_doc import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_missing_arg(tmpdir, runner):
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main)
        assert result.exception
        assert result.exit_code == 2


def test_cli_invalid_mount_at(tmpdir, runner):
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main, ['--output', 'docs', '.', '--mount-at', 'elm'])
        assert result.exception
        assert result.exit_code == 2
        assert 'mount-at' in result.output


def test_cli_in_empty_project(tmpdir, runner):
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main, ['--output', 'docs', '.'])
        assert result.exception
        assert result.exit_code != 0


def test_cli_doit_only_arg_in_real_project(tmpdir, runner, make_elm_project):
    elm_version = '0.18.0'
    project_path = tmpdir.mkdir('frontend')
    make_elm_project(elm_version, project_path)

    with tmpdir.as_cwd():
        tmpdir.mkdir('docs')
        result = runner.invoke(cli.main, ['--output', 'docs', 'frontend', 'clean', '--dry-run'])
        assert not result.exception, result.output
        assert result.exit_code == 0

        assert tmpdir.join('docs').check(exists=True)


def test_cli_in_real_project(tmpdir, runner, overlayer, make_elm_project):
    elm_version = '0.18.0'
    project_path = tmpdir.mkdir('frontend')
    modules = ['Main.elm']
    make_elm_project(elm_version, project_path, copy_elm_stuff=True, modules=modules)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        tmpdir.join('frontend', 'README.md').write('hello')
        result = runner.invoke(cli.main, ['--output', 'docs', 'frontend'])
        assert not result.exception, result.output
        assert result.exit_code == 0

        assert output_dir.join('assets').check(dir=True)
        assert output_dir.join('artifacts').check(dir=True)

        elm_lang_html_docs_path = output_dir.join(
            'packages', 'elm-lang', 'html', '2.0.0', 'documentation.json')
        assert elm_lang_html_docs_path.check()

        package_dir = output_dir.join('packages', 'user', 'project', '1.0.0')
        assert package_dir.dirpath('latest').check(dir=True, link=True)
        assert package_dir.join('README.md').check()

        package_index = package_dir.join('index.html')
        assert package_index.check()

        package_main = package_dir.join('Main')
        assert package_main.check()

        package_docs = package_dir.join('documentation.json')
        assert package_docs.check()
        assert json.loads(package_docs.read())[0]['name'] == 'Main'

        all_packages = output_dir.join('all-packages')
        assert all_packages.check()
        assert len(json.loads(all_packages.read())) > 0

        new_packages = output_dir.join('new-packages')
        assert new_packages.check()
        assert len(json.loads(new_packages.read())) > 0


def test_cli_validate_real_project(tmpdir, runner, overlayer, make_elm_project):
    elm_version = '0.18.0'
    project_path = tmpdir.mkdir('frontend')
    modules = ['Main.elm']
    make_elm_project(elm_version, project_path, copy_elm_stuff=True, modules=modules)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        tmpdir.join('frontend', 'README.md').write('hello')
        result = runner.invoke(cli.main, ['--validate', 'frontend'])
        assert not result.exception, result.output
        assert result.exit_code == 0

        assert output_dir.check(exists=False)


def test_cli_validate_invalid_project(capfd, tmpdir, runner, overlayer, make_elm_project):
    elm_version = '0.18.0'
    project_path = tmpdir.mkdir('frontend')
    modules = ['MissingModuleComment.elm', 'PublicFunctionNotInAtDocs.elm']
    make_elm_project(elm_version, project_path, copy_elm_stuff=True, modules=modules)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main, ['--output', 'docs', '--validate', 'frontend'])
        out, err = capfd.readouterr()

        problem_lines = [line for line in err.splitlines()
                         if 'SYNTAX PROBLEM' in line or 'DOCUMENTATION ERROR' in line]
        assert len(problem_lines) == 2

        # traceback should be suppressed
        assert 'CalledProcessError' not in result.output
        assert 'CalledProcessError' not in out
        assert 'CalledProcessError' not in err

        assert result.exception, result.output
        assert result.exit_code == 1

        assert output_dir.check(exists=False)
