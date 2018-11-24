from pathlib import Path

from elm_doc import asset_tasks


def test_asset_tasks_extract_assets(tmpdir):
    asset_tasks.extract_assets(Path(str(tmpdir)))
    assert tmpdir.join('assets').check(dir=True)
    assert tmpdir.join('assets', 'highlight', 'highlight.pack.js').check()
    assert tmpdir.join('assets', 'help', 'design-guidelines.md').check()
    assert tmpdir.join('assets', 'LICENSE').check()
    assert tmpdir.join('artifacts', 'elm.js').check()
    assert tmpdir.join('artifacts', 'LICENSE').check()
