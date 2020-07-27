import os
import os.path
import json
from pathlib import Path

import pytest
from click.testing import CliRunner
import parsy
from doit.runner import SUCCESS, FAILURE, ERROR

from elm_doc import cli
from elm_doc import elm_project
from elm_doc.tasks import catalog as catalog_tasks


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_missing_arg(tmpdir, runner):
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main)
        assert result.exception
        assert result.exit_code == ERROR


def test_cli_invalid_mount_at(tmpdir, runner):
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main, ['--output', 'docs', '.', '--mount-at', 'elm'])
        assert result.exception
        assert result.exit_code == ERROR
        assert 'mount-at' in result.output


def test_cli_non_existent_elm_path(tmpdir, runner):
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main, ['--output', 'docs', '.', '--elm-path', 'elm-path'])
        assert result.exception
        assert result.exit_code == ERROR, result.output
        assert 'elm-path' in result.output


def test_cli_in_empty_project(tmpdir, runner):
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main, ['--output', 'docs', '.', '--fake-license', 'BSD-3-Clause'])
        assert result.exception
        assert result.exit_code == ERROR
        assert 'does not look like an Elm project' in str(result.output)


def test_cli_doit_only_arg_in_real_project(tmpdir, runner, elm_version, elm, make_elm_project):
    project_dir = make_elm_project(elm_version, tmpdir, copy_elm_stuff=True)

    with tmpdir.as_cwd():
        tmpdir.mkdir('docs')
        result = runner.invoke(cli.main, [
            '--output', 'docs',
            project_dir.basename,
            '--fake-license', 'BSD-3-Clause',
            '--elm-path', elm,
            '--doit-args', 'clean', '--dry-run'])
        assert not result.exception, result.output
        assert result.exit_code == SUCCESS

        assert tmpdir.join('docs').check(exists=True)


def test_cli_in_real_project(tmpdir, runner, elm_version, elm, make_elm_project):
    sources = {'.': ['Main.elm', 'PortModuleA.elm']}
    project_dir = make_elm_project(elm_version, tmpdir, sources=sources, copy_elm_stuff=False)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        project_dir.join('README.md').write('hello')
        result = runner.invoke(cli.main, [
            '--output', 'docs', project_dir.basename, '--fake-license', 'CATOSL-1.1',
        ], env={'PATH': '{}:{}'.format(str(Path(elm).parent), os.environ['PATH'])})
        assert not result.exception, result.output
        assert result.exit_code == SUCCESS

        assert output_dir.join('assets').check(dir=True)
        assert output_dir.join('artifacts').check(dir=True)

        elm_lang_html_path = output_dir.join(
            'packages', 'elm', 'html', '1.0.0')
        assert elm_lang_html_path.join('docs.json').check()
        assert elm_lang_html_path.join('..', 'releases.json').check()
        assert elm_lang_html_path.join('Html-Keyed').check()

        package_dir = output_dir.join('packages', 'user', 'project', '1.0.0')
        package_latest_link = package_dir.dirpath('latest')
        assert package_latest_link.check(dir=True, link=True)
        assert not os.path.isabs(package_latest_link.readlink())
        assert package_dir.join('README.md').check()
        assert package_dir.join('..', 'releases.json').check()

        package_index = package_dir.join('index.html')
        assert package_index.check()

        package_main = package_dir.join('Main')
        assert package_main.check()

        package_about = package_dir.join('about')
        assert package_about.check()

        package_docs = package_dir.join('docs.json')
        assert package_docs.check()
        assert json.loads(package_docs.read())[0]['name'] == 'Main'

        for popular_package in catalog_tasks.popular_packages:
            assert output_dir.join('packages', popular_package).check(dir=True)

        search_json = output_dir.join('search.json').read()
        assert 'CATOSL-1.1' not in search_json, 'Fake license should not be exposed in search.json'
        assert len(json.loads(search_json)) > 0

        help_doc_format = output_dir.join('help/documentation-format')
        assert help_doc_format.check()


def test_cli_build_docs_multiple_source_dirs(
        mock_popular_packages, tmpdir, mocker, runner, elm, elm_version, make_elm_project):
    sources = {'src': ['Main.elm'], 'srcB': ['PortModuleA.elm']}
    project_dir = make_elm_project(elm_version, tmpdir, sources=sources, copy_elm_stuff=False)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        project_dir.join('README.md').write('hello')
        result = runner.invoke(cli.main, [
            '--output', 'docs',
            project_dir.basename,
            '--fake-license', 'CATOSL-1.1',
            '--elm-path', elm,
        ])
        assert not result.exception, result.output
        assert result.exit_code == SUCCESS

        package_dir = output_dir.join('packages', 'user', 'project', '1.0.0')

        package_main = package_dir.join('Main')
        assert package_main.check()

        package_docs = package_dir.join('docs.json')
        assert package_docs.check()
        actual_docs = json.loads(package_docs.read())
        assert actual_docs[0]['name'] == 'Main'
        assert actual_docs[1]['name'] == 'PortModuleA'


def test_cli_changes_in_port_module_gets_picked_up(
        mock_popular_packages, tmpdir, mocker, runner, elm, elm_version, make_elm_project):
    sources = {'.': ['PortModuleA.elm', 'PortModuleB.elm']}
    project_dir = make_elm_project(elm_version, tmpdir, sources=sources, copy_elm_stuff=False)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main, [
            '--output', 'docs',
            project_dir.basename,
            '--fake-license', 'BSD-3-Clause',
            '--elm-path', elm,
        ])
        assert not result.exception, result.output
        assert result.exit_code == SUCCESS

        package_dir = output_dir.join('packages', 'user', 'project', '1.0.0')
        assert package_dir.join('docs.json').check()

        port_module_a = project_dir / 'PortModuleA.elm'
        source = port_module_a.read_text('utf8')
        port_module_a.write_text(source.replace('portA', 'portC'), 'utf8')

        result = runner.invoke(cli.main, [
            '--output', 'docs',
            project_dir.basename,
            '--fake-license', 'BSD-3-Clause',
            '--elm-path', elm,
        ])
        assert not result.exception, result.output
        assert result.exit_code == SUCCESS

        package_dir = output_dir.join('packages', 'user', 'project', '1.0.0')
        docs = package_dir.join('docs.json').read_text('utf8')
        assert 'portC' in docs


def test_cli_mount_point_change_gets_picked_up(
        mock_popular_packages, tmpdir, mocker, runner, elm, elm_version, make_elm_project):
    sources = {'.': ['Main.elm']}
    project_dir = make_elm_project(elm_version, tmpdir, sources=sources, copy_elm_stuff=True)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main, [
            '--output', 'docs',
            project_dir.basename,
            '--fake-license', 'BSD-3-Clause',
            '--elm-path', elm,
        ])
        assert not result.exception, result.output
        assert result.exit_code == SUCCESS

        package_dir = output_dir.join('packages', 'user', 'project', '1.0.0')
        assert package_dir.join('docs.json').check()

        result = runner.invoke(cli.main, [
            '--output', 'docs',
            project_dir.basename,
            '--fake-license', 'BSD-3-Clause',
            '--elm-path', elm,
            '--mount-at', '/newmountpoint',
        ])
        assert not result.exception, result.output
        assert result.exit_code == SUCCESS

        # index
        assert 'newmountpoint' in output_dir.join('index.html').read()
        # help
        assert 'newmountpoint' in output_dir.join('help', 'documentation-format').read()

        package_dir = output_dir.join('packages', 'user', 'project', '1.0.0')

        # package page
        assert 'newmountpoint' in package_dir.join('index.html').read()
        # module page
        assert 'newmountpoint' in package_dir.join('Main').read()


def test_cli_project_version_change_gets_picked_up(
        mock_popular_packages, tmpdir, runner, elm, elm_version, make_elm_project):
    sources = {'.': ['Main.elm']}
    project_dir = make_elm_project(elm_version, tmpdir, sources=sources, copy_elm_stuff=True)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main, [
            '--output', 'docs',
            project_dir.basename,
            '--fake-license', 'BSD-3-Clause',
            '--elm-path', elm,
        ])
        assert not result.exception, result.output
        assert result.exit_code == SUCCESS

        package_dir = output_dir.join('packages', 'user', 'project', '1.0.0')
        assert package_dir.join('docs.json').check()

        result = runner.invoke(cli.main, [
            '--output', 'docs',
            project_dir.basename,
            '--fake-license', 'BSD-3-Clause',
            '--elm-path', elm,
            '--fake-version', '2.0.0'])
        assert not result.exception, result.output
        assert result.exit_code == SUCCESS

        package_dir = output_dir.join('packages', 'user', 'project', '2.0.0')
        assert package_dir.join('docs.json').check()

        package_latest_link = package_dir.dirpath('latest')
        package_latest_link_target = package_latest_link.realpath()
        assert package_latest_link_target.check(dir=True)
        assert package_latest_link_target.basename == '2.0.0'

        releases = json.loads(package_dir.join('..', 'releases.json').read())
        assert list(releases.keys()) == ['2.0.0']

        search_json = json.loads(output_dir.join('search.json').read())
        project_entry = next(entry for entry in search_json if entry['name'] == 'user/project')
        assert project_entry['version'] == '2.0.0'


def test_cli_validate_real_project(
        tmpdir, runner, elm, elm_version, make_elm_project):
    sources = {'.': ['Main.elm']}
    project_dir = make_elm_project(elm_version, tmpdir, sources=sources, copy_elm_stuff=True)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        project_dir.join('README.md').write('hello')
        result = runner.invoke(cli.main, [
            '--validate', project_dir.basename,
            '--fake-license', 'BSD-3-Clause',
            '--elm-path', elm,
        ])
        assert not result.exception, result.output
        assert result.exit_code == SUCCESS

        assert output_dir.check(exists=False)


def test_cli_validate_subset_of_real_project_with_forced_exclusion(
        tmpdir, runner, elm, elm_version, make_elm_project):
    sources = {
        'ok': ['Main.elm'],
        'err1': ['MissingModuleComment.elm'],
        'err2': ['PublicFunctionNotInAtDocs.elm'],
    }
    project_dir = make_elm_project(elm_version, tmpdir, sources=sources, copy_elm_stuff=True)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        project_dir.join('README.md').write('hello')
        result = runner.invoke(cli.main, [
            project_dir.basename,
            os.path.join(project_dir.basename, 'ok', 'Main.elm'),
            os.path.join(project_dir.basename, 'err1', 'MissingModuleComment.elm'),
            os.path.join(project_dir.basename, 'err2', 'PublicFunctionNotInAtDocs.elm'),
            '--fake-license', 'BSD-3-Clause',
            '--elm-path', elm,
            '--validate',
            '--exclude-modules',
            'MissingModuleComment',
            '--exclude-source-directories',
            'err2',
            '--force-exclusion',
        ])
        assert not result.exception, result.output
        assert result.exit_code == SUCCESS

        # validation should not output anything
        assert output_dir.check(exists=False)


def test_cli_validate_invalid_project_with_masked_exclude(
        tmpdir, runner, elm, elm_version, make_elm_project, request):
    sources = {'.': ['MissingModuleComment.elm', 'PublicFunctionNotInAtDocs.elm']}
    project_dir = make_elm_project(elm_version, tmpdir, sources=sources, copy_elm_stuff=True)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main, [
            '--output', 'docs',
            '--fake-license', 'BSD-3-Clause',
            '--elm-path', elm,
            '--validate',
            project_dir.basename])
        assert result.exception, result.output
        assert result.exit_code == FAILURE

        problem_lines = [line for line in result.output.splitlines()
                         if 'NO DOCS' in line or 'DOCS MISTAKE' in line]
        assert len(problem_lines) == 2, result.output

        # traceback should be suppressed
        assert 'CalledProcessError' not in result.output

        assert output_dir.check(exists=False)


def test_cli_parsy_error_is_reported_as_error(
        tmpdir, runner, elm, elm_version, make_elm_project, mocker, request):
    sources = {'.': ['MissingModuleComment.elm', 'PortModuleA.elm']}
    project_dir = make_elm_project(elm_version, tmpdir, sources=sources, copy_elm_stuff=True)
    mocker.patch('elm_doc.elm_parser.parse_port_declaration',
                 side_effect=parsy.ParseError(None, None, None))
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main, [
            '--output', 'docs',
            '--fake-license', 'BSD-3-Clause',
            '--elm-path', elm,
            '--validate',
            project_dir.basename])
        assert result.exception, result.output
        assert result.exit_code == ERROR


def test_cli_line_parser_error_is_reported_as_error(
        tmpdir, runner, elm, elm_version, make_elm_project, mocker, request):
    sources = {'.': ['MissingModuleComment.elm', 'PortModuleA.elm']}
    project_dir = make_elm_project(elm_version, tmpdir, sources=sources, copy_elm_stuff=True)
    mocker.patch('elm_doc.elm_parser.iter_line_chunks', side_effect=Exception(''))
    with tmpdir.as_cwd():
        result = runner.invoke(cli.main, [
            '--output', 'docs',
            '--fake-license', 'BSD-3-Clause',
            '--elm-path', elm,
            '--validate',
            project_dir.basename])
        assert result.exception, result.output
        assert result.exit_code == ERROR


def test_issue_55(tmpdir, runner, elm, elm_version, fixture_path):
    project_dir = fixture_path.join('issue-55')
    project_elm_version = elm_project.from_path(Path(str(project_dir))).elm_version
    if project_elm_version != elm_version:
        pytest.skip('This test is intended for elm version {v}'.format(v=project_elm_version))
    with tmpdir.as_cwd():
        project_dir.copy(tmpdir)
        result = runner.invoke(cli.main, [
            '--output', 'docs',
            '--fake-license', 'BSD-3-Clause',
            '--elm-path', elm,
            '--validate',
            '.'])
        assert not result.exception, result.output
        assert result.exit_code == SUCCESS
