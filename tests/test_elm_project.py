from pathlib import Path

from elm_doc import elm_project


def test_glob_project_modules_includes_take_precedence_over_excludes(
        tmpdir, elm_version, make_elm_project):
    make_elm_project(
        elm_version,
        tmpdir,
        copy_elm_stuff=False,
        modules=[
            'Main.elm',
            'MissingModuleComment.elm',
            'PublicFunctionNotInAtDocs.elm',
        ])
    project = elm_project.from_path(Path(str(tmpdir)))
    config = elm_project.ProjectConfig(
        include_paths=_resolve_paths(tmpdir, 'Main.elm', 'MissingModuleComment.elm'),
        exclude_modules=['MissingModuleComment'],
        force_exclusion=False,
    )
    modules = list(elm_project.glob_project_modules(project, config))
    assert set(modules) == set(['Main', 'MissingModuleComment'])


def test_glob_project_modules_excludes_take_precedence_over_includes_if_forced(
        tmpdir, elm_version, make_elm_project):
    make_elm_project(
        elm_version,
        tmpdir,
        copy_elm_stuff=False,
        modules=[
            'Main.elm',
            'MissingModuleComment.elm',
            'PublicFunctionNotInAtDocs.elm',
        ])
    project = elm_project.from_path(Path(str(tmpdir)))
    config = elm_project.ProjectConfig(
        include_paths=_resolve_paths(tmpdir, 'Main.elm', 'MissingModuleComment.elm'),
        exclude_modules=['MissingModuleComment'],
        force_exclusion=True,
    )
    modules = list(elm_project.glob_project_modules(project, config))
    assert set(modules) == set(['Main'])


def test_glob_project_modules_includes_all_by_default(
        tmpdir, elm_version, make_elm_project):
    make_elm_project(
        elm_version,
        tmpdir,
        copy_elm_stuff=False,
        modules=[
            'Main.elm',
            'MissingModuleComment.elm',
        ])
    project = elm_project.from_path(Path(str(tmpdir)))
    config = elm_project.ProjectConfig(
        include_paths=[],
        exclude_modules=[],
        force_exclusion=False,
    )
    modules = list(elm_project.glob_project_modules(project, config))
    assert set(modules) == set(['Main', 'MissingModuleComment'])


def test_glob_project_modules_can_include_path_in_non_dot_source_dir(
        tmpdir, elm_version, make_elm_project):
    make_elm_project(
        elm_version,
        tmpdir,
        src_dir='src',
        copy_elm_stuff=False,
        modules=[
            'Main.elm',
            'MissingModuleComment.elm',
        ])
    project = elm_project.from_path(Path(str(tmpdir)))
    config = elm_project.ProjectConfig(
        include_paths=_resolve_paths(tmpdir, 'src/Main.elm'),
        exclude_modules=[],
        force_exclusion=False,
    )
    modules = list(elm_project.glob_project_modules(project, config))
    assert set(modules) == set(['Main'])


def _resolve_paths(tmpdir, *paths):
    return [str(tmpdir.join(path)) for path in paths]
