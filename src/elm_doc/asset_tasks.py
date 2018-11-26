from pathlib import Path
import tarfile


tarball = Path(__file__).parent / 'assets' / 'assets.tar.gz'
bundled_helps = [
    'assets/help/documentation-format.md',
    'assets/help/design-guidelines.md',
]
bundled_assets = bundled_helps + [
    'artifacts/elm.js',
    'artifacts/LICENSE',
    'assets/favicon.ico',
    'assets/highlight/highlight.pack.js',
    'assets/highlight/LICENSE',
    'assets/highlight/styles/default.css',
    'assets/LICENSE',
    'assets/style.css',
]


def extract_assets(output_path: Path):
    with tarfile.open(str(tarball)) as f:
        f.extractall(str(output_path))
