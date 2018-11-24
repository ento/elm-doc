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
                'build_docs_json',
                'project_top_page',
                'project_releases',
                'project_latest_link',
                ],
            'task_dependencies': [
                'dep_copy_docs_json',
                'dep_top_page',
                'dep_readme',
                'dep_releases',
                'dep_latest_link',
                'dep_module_page',
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
                'build_docs_json',
                'project_top_page',
                'project_readme',
                'project_releases',
                'project_latest_link',
                'project_module_page',
                ],
            'task_dependencies': [
                'dep_copy_docs_json',
                'dep_top_page',
                'dep_readme',
                'dep_releases',
                'dep_latest_link',
                'dep_module_page',
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
                'validate_docs_json',
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
            basename = task['basename']
            if basename not in seen:
                seen.add(basename)
                rv[creator_name].append(basename)
    return rv
