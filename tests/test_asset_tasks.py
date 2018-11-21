from pathlib import Path

from elm_doc import asset_tasks


def test_asset_tasks_build_assets(
        tmpdir, elm_version, make_elm_project):
    asset_tasks.build_assets(elm_version, Path(str(tmpdir)), '/docs')
    assert tmpdir.join('assets').check(dir=True)
    assert tmpdir.join('assets', 'highlight', 'highlight.pack.js').check()
    assert tmpdir.join('assets', 'help', 'design-guidelines.md').check()
    assert tmpdir.join('artifacts', 'elm.js').check()
