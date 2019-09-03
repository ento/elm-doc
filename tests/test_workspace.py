from pathlib import Path

from elm_doc import elm_project
from elm_doc import catalog_tasks


def test_fixture_includes_popular_packages():
    # this is so that tests can be run without network access, I think..
    workspace_path = Path(__file__).parent.parent / 'workspace'
    project = elm_project.from_path(workspace_path)
    assert set(project.direct_dependency_names()) >= set(catalog_tasks.popular_packages)
