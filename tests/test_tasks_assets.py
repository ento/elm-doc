from pathlib import Path

from elm_doc.tasks import assets as assets_tasks


def test_extract_assets(tmpdir):
    tmp_path = Path(str(tmpdir))
    assets_tasks.actions.extract_assets(tmp_path)
    generated_files = [str(path.relative_to(tmp_path))
                       for path in tmp_path.glob('**/*') if path.is_file()]
    assert set(generated_files) == set(assets_tasks.bundled_assets)
