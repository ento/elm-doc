from pathlib import Path

from elm_doc import elm_project


def test_sorted_exposed_modules_of_flat_exposed_modules():
    package = elm_project.ElmPackage(
        path=Path(),
        user='',
        project='',
        version='',
        summary='',
        license='',
        elm_version='',
        exposed_modules=['Module.C', 'Module.B'],
        dependencies={},
        test_dependencies={},
    )
    assert list(package.sorted_exposed_modules()) == ['Module.B', 'Module.C']


def test_sorted_exposed_modules_flattens_groups():
    package = elm_project.ElmPackage(
        path=Path(),
        user='',
        project='',
        version='',
        summary='',
        license='',
        elm_version='',
        exposed_modules={
            'Group A': ['Module.A'],
            'Group B': ['Module.C', 'Module.B'],
        },
        dependencies={},
        test_dependencies={},
    )
    assert list(package.sorted_exposed_modules()) == ['Module.A', 'Module.B', 'Module.C']


def test_glob_project_modules_includes_take_precedence_over_excludes(
        tmpdir, elm_version, make_elm_project):
    project_dir = make_elm_project(
        elm_version,
        tmpdir,
        copy_elm_stuff=False,
        modules=[
            'Main.elm',
            'MissingModuleComment.elm',
            'PublicFunctionNotInAtDocs.elm',
        ])
    project = elm_project.from_path(Path(str(project_dir)))
    config = elm_project.ProjectConfig(
        include_paths=_resolve_paths(project_dir, 'Main.elm', 'MissingModuleComment.elm'),
        exclude_modules=['MissingModuleComment'],
        force_exclusion=False,
    )
    modules = list(_glob_project_modules(project, config))
    assert set(modules) == set(['Main', 'MissingModuleComment'])


def test_glob_project_modules_excludes_take_precedence_over_includes_if_forced(
        tmpdir, elm_version, make_elm_project):
    project_dir = make_elm_project(
        elm_version,
        tmpdir,
        copy_elm_stuff=False,
        modules=[
            'Main.elm',
            'MissingModuleComment.elm',
            'PublicFunctionNotInAtDocs.elm',
        ])
    project = elm_project.from_path(Path(str(project_dir)))
    config = elm_project.ProjectConfig(
        include_paths=_resolve_paths(project_dir, 'Main.elm', 'MissingModuleComment.elm'),
        exclude_modules=['MissingModuleComment'],
        force_exclusion=True,
    )
    modules = list(_glob_project_modules(project, config))
    assert set(modules) == set(['Main'])


def test_glob_project_modules_includes_all_by_default(
        tmpdir, elm_version, make_elm_project):
    project_dir = make_elm_project(
        elm_version,
        tmpdir,
        copy_elm_stuff=False,
        modules=[
            'Main.elm',
            'MissingModuleComment.elm',
        ])
    project = elm_project.from_path(Path(str(project_dir)))
    config = elm_project.ProjectConfig(
        include_paths=[],
        exclude_modules=[],
        force_exclusion=False,
    )
    modules = list(_glob_project_modules(project, config))
    assert set(modules) == set(['Main', 'MissingModuleComment'])


def test_glob_project_modules_can_include_path_in_non_dot_source_dir(
        tmpdir, elm_version, make_elm_project):
    project_dir = make_elm_project(
        elm_version,
        tmpdir,
        src_dir='src',
        copy_elm_stuff=False,
        modules=[
            'Main.elm',
            'MissingModuleComment.elm',
        ])
    project = elm_project.from_path(Path(str(project_dir)))
    config = elm_project.ProjectConfig(
        include_paths=_resolve_paths(project_dir, 'src/Main.elm'),
        exclude_modules=[],
        force_exclusion=False,
    )
    modules = list(_glob_project_modules(project, config))
    assert set(modules) == set(['Main'])


def test_glob_project_modules_ignores_dot_directories(
        tmpdir, elm_version, make_elm_project):
    project_dir = make_elm_project(
        elm_version,
        tmpdir,
        src_dir='.',
        copy_elm_stuff=False,
        modules=[
            'Main.elm',
        ])
    dot_dir_file = Path(str(project_dir / '.elm-doc' / 'Extra.elm'))
    dot_dir_file.parent.mkdir()
    dot_dir_file.touch()
    project = elm_project.from_path(Path(str(project_dir)))
    config = elm_project.ProjectConfig(
        include_paths=[],
        exclude_modules=[],
        force_exclusion=False,
    )
    modules = list(_glob_project_modules(project, config))
    assert set(modules) == set(['Main'])


def _glob_project_modules(*args, **kwargs):
    '''Return only the module names from the result of elm_project.glob_project_modules'''
    return [module.name for module in elm_project.glob_project_modules(*args, **kwargs)]


def _resolve_paths(tmpdir, *paths):
    return [str(tmpdir.join(path)) for path in paths]
