import os
import os.path
from collections import defaultdict
import json

import elm_docs
from elm_docs import tasks


def test_create_tasks_empty_input():
    result = list(tasks.create_tasks(None, []))
    assert len(result) == 0


def test_create_tasks_only_elm_stuff(tmpdir, make_elm_project):
    elm_version = '0.18.0'
    make_elm_project(elm_version, tmpdir, copy_elm_stuff=True)
    output_dir = tmpdir.join('docs')
    with tmpdir.as_cwd():
        result = list(tasks.create_tasks(output_dir, ['elm-package.json']))
        assert len(result) == 0


def test_create_tasks_only_project_modules(tmpdir, make_elm_project):
    elm_version = '0.18.0'
    modules = ['Main.elm']
    make_elm_project(elm_version, tmpdir, modules=modules)
    output_dir = tmpdir.join('docs')
    elm_docs.__path__.append(os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir)))
    with tmpdir.as_cwd():
        tmpdir.join('README.md').write('hello')

        package_dir = output_dir.join('packages', 'user', 'project', '1.0.0')
        result = by_basename(tasks.create_tasks(output_dir, ['elm-package.json']))

        # link from /latest
        assert len(result['package_latest_link']) == 1
        action, args = result['package_latest_link'][0]['actions'][0]
        action(*args)
        assert package_dir.dirpath('latest').check(dir=True, link=True)

        # readme
        assert len(result['package_readme']) == 1
        action, args = result['package_readme'][0]['actions'][0]
        action(*args)
        assert package_dir.join('README.md').check()

        # package page
        assert len(result['package_page']) == 1
        output_index = package_dir.join('index.html')
        assert result['package_page'][0]['targets'] == [output_index]

        action, args = result['package_page'][0]['actions'][0]
        action(*args)
        assert output_index.check()

        # module page
        assert len(result['module_page']) == 1
        output_main = package_dir.join('Main')
        assert result['module_page'][0]['targets'] == [output_main]

        action, args = result['module_page'][0]['actions'][0]
        action(*args)
        assert output_main.check()

        # package documentation.json
        assert len(result['package_docs_json']) == 1
        output_docs = package_dir.join('documentation.json')
        assert result['package_docs_json'][0]['targets'] == [output_docs]

        action, args = result['package_docs_json'][0]['actions'][0]
        action(*args)
        assert output_docs.check()
        assert json.loads(output_docs.read())[0]['name'] == 'Main'


def by_basename(tasks):
    rv = defaultdict(list)
    for task in tasks:
        basename = task['basename'].split(':')[0]
        rv[basename].append(task)
    return rv


# deprecated
def _get_npm_elm_version_range(elm_package):
    min_version, gt_op, _, lt_op, max_version = elm_package['elm-version'].split(' ')
    return '{gt_op}{min_version} {lt_op}{max_version}'.format(
        min_version=min_version,
        gt_op=flip_inequality_op(gt_op),
        lt_op=lt_op,
        max_version=max_version,
    )


# deprecated
def _flip_inequality_op(op):
    # assume there's only one < or >
    return op.replace('>', '<').replace('<', '>')