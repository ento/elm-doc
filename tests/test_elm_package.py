from pathlib import Path

from elm_doc import elm_package


def test_glob_package_modules_includes_then_excludes(tmpdir, make_elm_project):
    elm_version = '0.18.0'
    make_elm_project(
        elm_version,
        tmpdir,
        copy_elm_stuff=True,
        modules=[
            'Main.elm',
            'MissingModuleComment.elm',
            'PublicFunctionNotInAtDocs.elm',
        ])
    package = elm_package.from_path(Path(tmpdir))
    include_patterns = ['Main.elm', 'MissingModuleComment.elm']
    exclude_patterns = ['MissingModuleComment']
    modules = list(elm_package.glob_package_modules(package, include_patterns, exclude_patterns))
    assert modules == ['Main']


def test_glob_package_modules_includes_all_by_default(tmpdir, make_elm_project):
    elm_version = '0.18.0'
    make_elm_project(
        elm_version,
        tmpdir,
        copy_elm_stuff=False,
        modules=[
            'Main.elm',
            'MissingModuleComment.elm',
        ])
    package = elm_package.from_path(Path(tmpdir))
    include_patterns = []
    exclude_patterns = []
    modules = list(elm_package.glob_package_modules(package, include_patterns, exclude_patterns))
    assert modules == ['Main', 'MissingModuleComment']
