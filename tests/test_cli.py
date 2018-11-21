import pytest
import json
import os.path
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


def test_cli_non_binary_elm_make(tmpdir, runner):
    with tmpdir.as_cwd():
        tmpdir.join('elm-make').write('binwrapped elm!')
        result = runner.invoke(cli.main, ['--output', 'docs', '.', '--elm-make', 'elm-make'])
        assert result.exception
        assert result.exit_code == 2, result.output
        assert 'elm-make' in result.output


def test_cli_non_existent_elm_make(tmpdir, runner):
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main, ['--output', 'docs', '.', '--elm-make', 'elm-make'])
        assert result.exception
        assert result.exit_code == 2, result.output
        assert 'elm-make' in result.output


def test_cli_in_empty_project(tmpdir, runner):
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main, ['--output', 'docs', '.'])
        assert result.exception
        assert result.exit_code != 0


def test_cli_doit_only_arg_in_real_project(tmpdir, runner, elm_version, make_elm_project):
    project_dir = make_elm_project(elm_version, tmpdir, copy_elm_stuff=True)

    with tmpdir.as_cwd():
        tmpdir.mkdir('docs')
        result = runner.invoke(cli.main, ['--output', 'docs', project_dir.basename, '--doit-args', 'clean', '--dry-run'])
        assert not result.exception, result.output
        assert result.exit_code == 0

        assert tmpdir.join('docs').check(exists=True)


def test_cli_in_real_project(tmpdir, runner, elm_version, make_elm_project):
    modules = ['Main.elm']
    project_dir = make_elm_project(elm_version, tmpdir, copy_elm_stuff=True, modules=modules)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        project_dir.join('README.md').write('hello')
        result = runner.invoke(cli.main, ['--output', 'docs', project_dir.basename])
        assert not result.exception, result.output
        assert result.exit_code == 0

        assert output_dir.join('assets').check(dir=True)
        assert output_dir.join('artifacts').check(dir=True)

        elm_lang_html_docs_path = output_dir.join(
            'packages', 'elm', 'html', '1.0.0', 'documentation.json')
        assert elm_lang_html_docs_path.check()

        package_dir = output_dir.join('packages', 'user', 'project', '1.0.0')
        package_latest_link = package_dir.dirpath('latest')
        assert package_latest_link.check(dir=True, link=True)
        assert not os.path.isabs(package_latest_link.readlink())
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


def test_cli_validate_real_project(
        tmpdir, runner, elm_version, make_elm_project):
    modules = ['Main.elm']
    project_dir = make_elm_project(elm_version, tmpdir, copy_elm_stuff=True, modules=modules)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        project_dir.join('README.md').write('hello')
        result = runner.invoke(cli.main, ['--validate', project_dir.basename])
        assert not result.exception, result.output
        assert result.exit_code == 0

        assert output_dir.check(exists=False)


def test_cli_validate_subset_of_real_project_with_forced_exclusion(
        tmpdir, runner, elm_version, make_elm_project):
    modules = ['Main.elm', 'MissingModuleComment.elm']
    project_dir = make_elm_project(elm_version, tmpdir, copy_elm_stuff=True, modules=modules)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        project_dir.join('README.md').write('hello')
        result = runner.invoke(cli.main, [
            project_dir.basename,
            os.path.join(project_dir.basename, 'Main.elm'),
            os.path.join(project_dir.basename, 'MissingModuleComment.elm'),
            '--validate',
            '--exclude',
            'MissingModuleComment',
            '--force-exclusion',
        ])
        assert not result.exception, result.output
        assert result.exit_code == 0

        # validation should not output anything
        assert output_dir.check(exists=False)


def test_cli_validate_invalid_project_with_masked_exclude(
        tmpdir, runner, elm_version, make_elm_project, request):
    modules = ['MissingModuleComment.elm', 'PublicFunctionNotInAtDocs.elm']
    project_dir = make_elm_project(elm_version, tmpdir, copy_elm_stuff=True, modules=modules)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main, ['--output', 'docs', '--validate', project_dir.basename])
        problem_lines = [line for line in result.output.splitlines()
                         if 'NO DOCS' in line or 'DOCS MISTAKE' in line]
        assert len(problem_lines) == 2

        # traceback should be suppressed
        assert 'CalledProcessError' not in result.output

        assert result.exception, result.output
        assert result.exit_code == 1

        assert output_dir.check(exists=False)
