from pathlib import Path

from elm_doc import tasks
from elm_doc.elm_project import ProjectConfig


def test_create_tasks_only_dependencies(tmpdir, elm_version, make_elm_project):
    project_dir = make_elm_project(elm_version, tmpdir, copy_elm_stuff=True)
    output_dir = tmpdir.join('docs')
    with project_dir.as_cwd():
        result = _create_tasks(Path('.'), ProjectConfig(), Path(str(output_dir)))
        expected_task_names = {
            'task_main_project': [
                'build_project_docs_json',
                'package_page',
                'package_releases',
                'package_latest_link',
                ],
            'task_dependencies': [
                'copy_package_docs_json',
                'package_page',
                'package_readme',
                'package_releases',
                'package_latest_link',
                'module_page',
                'index',
                'search_json',
                'new_packages',
                ],
            'task_assets': ['assets'],
        }
        assert _basenames_in_first_seen_order(result) == expected_task_names


def test_create_tasks_project_modules_and_dependencies(
        tmpdir, elm_version, make_elm_project):
    modules = ['Main.elm']
    project_dir = make_elm_project(elm_version, tmpdir, modules=modules, copy_elm_stuff=True)
    output_dir = tmpdir.join('docs')
    with project_dir.as_cwd():
        project_dir.join('README.md').write('hello')
        result = _create_tasks(Path('.'), ProjectConfig(), Path(str(output_dir)))

        expected_task_names = {
            'task_main_project': [
                'build_project_docs_json',
                'package_page',
                'package_readme',
                'package_releases',
                'package_latest_link',
                'module_page',
                ],
            'task_dependencies': [
                'copy_package_docs_json',
                'package_page',
                'package_readme',
                'package_releases',
                'package_latest_link',
                'module_page',
                'index',
                'search_json',
                'new_packages',
                ],
            'task_assets': ['assets'],
        }
        assert _basenames_in_first_seen_order(result) == expected_task_names


def test_create_tasks_for_validation(tmpdir, elm_version, make_elm_project):
    project_dir = make_elm_project(elm_version, tmpdir)
    output_dir = tmpdir.join('docs')
    with project_dir.as_cwd():
        result = _create_tasks(Path('.'), ProjectConfig(), Path(str(output_dir)), validate=True)

        expected_task_names = {
            'task_main_project': [
                'validate_project_docs_json',
            ],
        }
        assert _basenames_in_first_seen_order(result) == expected_task_names


def _create_tasks(*args, **kwargs):
    task_creators = tasks.build_task_creators(*args, **kwargs)
    return {name: creator() for name, creator in task_creators.items()}


def _basenames_in_first_seen_order(create_tasks_result):
    rv = {}
    for creator_name, tasks in create_tasks_result.items():
        rv[creator_name] = []
        seen = set()
        for task in tasks:
            basename = task['basename'].split(':')[0]
            if basename not in seen:
                seen.add(basename)
                rv[creator_name].append(basename)
    return rv
