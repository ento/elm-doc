from pathlib import Path

from elm_doc.run_config import Build
from elm_doc.tasks import assets as assets_tasks


def test_extract_assets(tmpdir):
    tmp_path = Path(str(tmpdir))
    assets_tasks.actions.extract_assets(Build(None, None, tmp_path, '/docs'))
    generated_files = [str(path.relative_to(tmp_path))
                       for path in tmp_path.glob('**/*') if path.is_file()]
    expected_files = assets_tasks.bundled_assets + [
        str(f.parent / f.stem) for f in map(Path, assets_tasks.bundled_assets) if f.suffix == '.gz']
    assert set(generated_files) == set(expected_files)
