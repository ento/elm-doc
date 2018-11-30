from pathlib import Path

from elm_doc import asset_tasks


def test_asset_tasks_extract_assets(tmpdir):
    tmp_path = Path(str(tmpdir))
    asset_tasks.extract_assets(tmp_path)
    generated_files = [str(path.relative_to(tmp_path))
                       for path in tmp_path.glob('**/*') if path.is_file()]
    assert set(generated_files) == set(asset_tasks.bundled_assets)
