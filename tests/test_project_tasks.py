from pathlib import Path

from elm_doc import elm_project
from elm_doc import project_tasks


def test_sync_source_files_create_new_file(
        tmpdir, elm_version, make_elm_project):
    project_dir = make_elm_project(
        elm_version,
        tmpdir,
        sources={
            'src': [
                'Main.elm',
            ],
        },
        copy_elm_stuff=False,
    )
    project = elm_project.from_path(Path(str(project_dir)))
    target_dir = Path(project_dir / 'tmp')
    project_tasks._sync_source_files(project, target_dir)
    assert (target_dir / 'Main.elm').exists()


def test_sync_source_files_update_file(
        tmpdir, elm_version, make_elm_project):
    project_dir = make_elm_project(
        elm_version,
        tmpdir,
        sources={
            'src': [
                'Main.elm',
            ],
        },
        copy_elm_stuff=False,
    )
    project = elm_project.from_path(Path(str(project_dir)))
    target_dir = Path(project_dir / 'tmp')
    project_tasks._sync_source_files(project, target_dir)

    main_elm = project_dir.join('src', 'Main.elm')
    main_elm.write('updated for testing')

    project_tasks._sync_source_files(project, target_dir)
    assert (target_dir / 'Main.elm').read_text() == 'updated for testing'


def test_sync_source_files_delete_file(
        tmpdir, elm_version, make_elm_project):
    project_dir = make_elm_project(
        elm_version,
        tmpdir,
        sources={
            'src': [
                'Main.elm',
            ],
        },
        copy_elm_stuff=False,
    )
    project = elm_project.from_path(Path(str(project_dir)))
    target_dir = Path(project_dir / 'tmp')
    project_tasks._sync_source_files(project, target_dir)

    main_elm = project_dir.join('src', 'Main.elm')
    main_elm.remove()

    project_tasks._sync_source_files(project, target_dir)
    assert not (target_dir / 'Main.elm').exists()
