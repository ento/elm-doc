from pathlib import Path

from elm_doc import tasks
from elm_doc.elm_project import ProjectConfig


def test_create_tasks_only_dependencies(tmpdir, elm_version, make_elm_project):
    project_dir = make_elm_project(elm_version, tmpdir, copy_elm_stuff=True)
    output_dir = tmpdir.join('docs')
    with project_dir.as_cwd():
        result = list(tasks.create_tasks(Path('.'), ProjectConfig(), Path(str(output_dir))))
        expected_task_names = [
            'build_project_docs_json',
            'package_page',
            'package_releases',
            'package_latest_link',
            'copy_package_docs_json',
            'package_readme',
            'module_page',
            'index',
            'search_json',
            'new_packages',
            'assets']
        assert basenames_in_first_seen_order(result) == expected_task_names


def test_create_tasks_project_modules_and_dependencies(
        tmpdir, elm_version, make_elm_project):
    modules = ['Main.elm']
    project_dir = make_elm_project(elm_version, tmpdir, modules=modules, copy_elm_stuff=True)
    output_dir = tmpdir.join('docs')
    with project_dir.as_cwd():
        project_dir.join('README.md').write('hello')
        result = list(tasks.create_tasks(Path('.'), ProjectConfig(), Path(str(output_dir))))

        expected_task_names = [
            'build_project_docs_json',
            'package_page',
            'package_readme',
            'package_releases',
            'package_latest_link',
            'module_page',
            'copy_package_docs_json',
            'index',
            'search_json',
            'new_packages',
            'assets',
        ]
        assert basenames_in_first_seen_order(result) == expected_task_names


def test_create_tasks_for_validation(tmpdir, elm_version, make_elm_project):
    project_dir = make_elm_project(elm_version, tmpdir)
    output_dir = tmpdir.join('docs')
    with project_dir.as_cwd():
        result = list(tasks.create_tasks(Path('.'), ProjectConfig(), Path(str(output_dir)), validate=True))

        expected_task_names = [
            'validate_project_docs_json',
            ]
        assert basenames_in_first_seen_order(result) == expected_task_names


def basenames_in_first_seen_order(tasks):
    rv = []
    seen = set()
    for task in tasks:
        basename = task['basename'].split(':')[0]
        if basename not in seen:
            seen.add(basename)
            rv.append(basename)
    return rv
