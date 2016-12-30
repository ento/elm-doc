from collections import defaultdict
import json

from elm_doc import tasks


# todo: this module should only test which tasks are generated,
# and test_cli and/or tests for each task should test the actual effects.


def test_create_tasks_only_elm_stuff(tmpdir, make_elm_project):
    elm_version = '0.18.0'
    make_elm_project(elm_version, tmpdir, copy_elm_stuff=True)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        result = list(tasks.create_tasks('.', str(output_dir)))
        expected_task_names = [
            'build_package_docs_json',
            'package_page',
            'package_latest_link',
            'download_package_docs_json',
            'package_readme',
            'module_page',
            'index',
            'all_packages',
            'new_packages',
            'assets']
        assert basenames_in_first_seen_order(result) == expected_task_names

        # artifacts and assets
        tasks_by_basename = by_basename(result)
        assert len(tasks_by_basename['download_package_docs_json']) > 0
        invoke_actions(tasks_by_basename['download_package_docs_json'][0]['actions'])

        _, args = tasks_by_basename['download_package_docs_json'][0]['actions'][1]
        package, output_path = args
        assert output_path.is_file()


def test_create_tasks_only_project_modules(tmpdir, overlayer, make_elm_project):
    elm_version = '0.18.0'
    modules = ['Main.elm']
    make_elm_project(elm_version, tmpdir, modules=modules)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        tmpdir.join('README.md').write('hello')

        package_dir = output_dir.join('packages', 'user', 'project', '1.0.0')
        result = by_basename(tasks.create_tasks('.', str(output_dir)))

        # artifacts and assets
        assert len(result['assets']) == 1
        invoke_actions(result['assets'][0]['actions'])
        assert output_dir.join('assets').check(dir=True)
        assert output_dir.join('artifacts').check(dir=True)

        # link from /latest
        assert len(result['package_latest_link']) == 1
        invoke_actions(result['package_latest_link'][0]['actions'])
        assert package_dir.dirpath('latest').check(dir=True, link=True)

        # readme
        assert len(result['package_readme']) == 1
        invoke_actions(result['package_readme'][0]['actions'])
        assert package_dir.join('README.md').check()

        # package page
        assert len(result['package_page']) == 1
        output_index = package_dir.join('index.html')
        assert result['package_page'][0]['targets'] == [output_index]

        invoke_actions(result['package_page'][0]['actions'])
        assert output_index.check()

        # module page
        assert len(result['module_page']) == 1
        output_main = package_dir.join('Main')
        assert result['module_page'][0]['targets'] == [output_main]

        invoke_actions(result['module_page'][0]['actions'])
        assert output_main.check()

        # package documentation.json
        assert len(result['build_package_docs_json']) == 1
        output_docs = package_dir.join('documentation.json')
        assert result['build_package_docs_json'][0]['targets'] == [output_docs]

        invoke_actions(result['build_package_docs_json'][0]['actions'])
        assert output_docs.check()
        assert json.loads(output_docs.read())[0]['name'] == 'Main'

        # all-packages
        assert len(result['all_packages']) == 1
        all_packages = output_dir.join('all-packages')
        assert result['all_packages'][0]['targets'] == [all_packages]

        invoke_actions(result['all_packages'][0]['actions'])
        assert all_packages.check()
        assert len(json.loads(all_packages.read())) > 0

        # new-packages
        assert len(result['new_packages']) == 1
        new_packages = output_dir.join('new-packages')
        assert result['new_packages'][0]['targets'] == [new_packages]

        invoke_actions(result['new_packages'][0]['actions'])
        assert new_packages.check()
        assert len(json.loads(new_packages.read())) > 0


def by_basename(tasks):
    rv = defaultdict(list)
    for task in tasks:
        basename = task['basename'].split(':')[0]
        rv[basename].append(task)
    return rv


def basenames_in_first_seen_order(tasks):
    rv = []
    seen = set()
    for task in tasks:
        basename = task['basename'].split(':')[0]
        if basename not in seen:
            seen.add(basename)
            rv.append(basename)
    return rv


def invoke_actions(action_specs):
    for action_spec in action_specs:
        if len(action_spec) == 3:
            action, args, kwargs = action_spec
            action(*args, **kwargs)
        else:
            action, args = action_spec
            action(*args)
