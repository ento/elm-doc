from pathlib import Path
import tarfile


tarball = Path(__file__).parent / 'assets' / 'assets.tar.gz'


def extract_assets(output_path: Path):
    with tarfile.open(tarball) as f:
        f.extractall(output_path)
