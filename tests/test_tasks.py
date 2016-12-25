from collections import defaultdict
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
    with tmpdir.as_cwd():
        package_dir = output_dir.join('packages', 'user', 'project', '1.0.0')
        result = by_basename(tasks.create_tasks(output_dir, ['elm-package.json']))

        # link from /latest
        assert len(result['package_latest_link']) == 1
        action, args = result['package_latest_link'][0]['actions'][0]
        action(*args)
        assert package_dir.dirpath('latest').check(dir=True, link=True)

        # package doc
        assert len(result['package_doc']) == 1
        output_index = package_dir.join('index.html')
        assert result['package_doc'][0]['targets'] == [output_index]

        action, args = result['package_doc'][0]['actions'][0]
        action(*args)
        assert output_index.check()

        # module doc
        assert len(result['module_doc']) == 1
        output_main = package_dir.join('Main')
        assert result['module_doc'][0]['targets'] == [output_main]

        action, args = result['module_doc'][0]['actions'][0]
        action(*args)
        assert output_main.check()


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
