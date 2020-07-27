from pathlib import Path

from elm_doc import loader
from elm_doc import elm_project
from elm_doc.elm_project import ProjectConfig
from elm_doc.run_config import Build, Validate


def test_dependencies_task_loader_creates_matches_actual_basenames(
        mock_popular_packages, tmpdir, elm_version, make_elm_project):
    project_dir = make_elm_project(elm_version, tmpdir, copy_elm_stuff=True)
    output_dir = tmpdir.join('docs')
    with project_dir.as_cwd():
        project = elm_project.from_path(Path('.'))
        config = ProjectConfig()
        output_path = Path(str(output_dir))

        # expected
        result = _create_tasks(project, config, Build(None, None, output_path, ''))
        result_basenames = _basenames_in_first_seen_order(result)

        # actual
        deps_creator = loader.make_dependencies_task_loader(
            None, project, ProjectConfig(), output_path)
        # note: relies on doit internals
        delayed_task_creates = set(deps_creator.doit_create_after.creates)
        assert delayed_task_creates == set(result_basenames['task_dependencies'])


def test_create_tasks_only_dependencies(
        mock_popular_packages, tmpdir, elm_version, make_elm_project):
    project_dir = make_elm_project(elm_version, tmpdir, copy_elm_stuff=True)
    output_dir = tmpdir.join('docs')
    with project_dir.as_cwd():
        result = _create_tasks(elm_project.from_path(Path('.')), ProjectConfig(),
                               Build(None, None, Path(str(output_dir)), ''))
        expected_task_names = {
            'task_main_project': [
                'build_docs_json',
                'project_top_page',
                'project_versions_page',
                'project_elm_json',
                'project_releases',
                'project_latest_link',
                'project_about',
                ],
            'task_dependencies': [
                'dep_copy_docs_json',
                'dep_top_page',
                'dep_versions_page',
                'dep_elm_json',
                'dep_readme',
                'dep_releases',
                'dep_latest_link',
                'dep_about',
                'dep_module_page',
                'index',
                'search_json',
                'help',
                ],
            'task_assets': ['assets'],
        }
        assert _basenames_in_first_seen_order(result) == expected_task_names


def test_create_tasks_project_modules_and_dependencies(
        mock_popular_packages, tmpdir, elm_version, make_elm_project):
    sources = {'.': ['Main.elm']}
    project_dir = make_elm_project(elm_version, tmpdir, sources=sources, copy_elm_stuff=True)
    output_dir = tmpdir.join('docs')
    with project_dir.as_cwd():
        project_dir.join('README.md').write('hello')
        result = _create_tasks(elm_project.from_path(Path('.')), ProjectConfig(),
                               Build(None, None, Path(str(output_dir)), ''))

        expected_task_names = {
            'task_main_project': [
                'build_docs_json',
                'project_top_page',
                'project_versions_page',
                'project_elm_json',
                'project_readme',
                'project_releases',
                'project_latest_link',
                'project_about',
                'project_module_page',
                ],
            'task_dependencies': [
                'dep_copy_docs_json',
                'dep_top_page',
                'dep_versions_page',
                'dep_elm_json',
                'dep_readme',
                'dep_releases',
                'dep_latest_link',
                'dep_about',
                'dep_module_page',
                'index',
                'search_json',
                'help',
                ],
            'task_assets': ['assets'],
        }
        assert _basenames_in_first_seen_order(result) == expected_task_names


def test_create_tasks_for_validation(tmpdir, elm_version, make_elm_project):
    project_dir = make_elm_project(elm_version, tmpdir)
    with project_dir.as_cwd():
        result = _create_tasks(
            elm_project.from_path(Path('.')), ProjectConfig(), Validate(None, None))

        expected_task_names = {
            'task_main_project': [
                'validate_docs_json',
            ],
        }
        assert _basenames_in_first_seen_order(result) == expected_task_names


def _create_tasks(*args, **kwargs):
    task_loader = loader.make_task_loader(*args, **kwargs)
    return {name: creator() for name, creator in task_loader.items()}


def _basenames_in_first_seen_order(create_tasks_result):
    rv = {}
    for creator_name, created_tasks in create_tasks_result.items():
        rv[creator_name] = []
        seen = set()
        for task in created_tasks:
            basename = task['basename']
            if basename not in seen:
                seen.add(basename)
                rv[creator_name].append(basename)
    return rv
