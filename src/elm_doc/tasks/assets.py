from pathlib import Path
import re
import gzip
import tarfile

from elm_doc.run_config import Build
from elm_doc.utils import Namespace


tarball = Path(__file__).parent.parent / 'assets' / 'assets.tar.gz'
bundled_helps = [
    'assets/help/documentation-format.md',
    'assets/help/design-guidelines.md',
]
bundled_assets = bundled_helps + [
    'artifacts/elm.js',
    'artifacts/LICENSE',
    'assets/favicon.ico',
    'assets/fonts/6xK1dSBYKcSV-LCoeQqfX1RYOo3qPZ7jsDJB9cme_xc.woff2',
    'assets/fonts/6xK1dSBYKcSV-LCoeQqfX1RYOo3qPZ7jsDJT9g.woff2',
    'assets/fonts/6xK1dSBYKcSV-LCoeQqfX1RYOo3qPZ7ksDJB9cme_xc.woff2',
    'assets/fonts/6xK1dSBYKcSV-LCoeQqfX1RYOo3qPZ7ksDJT9g.woff2',
    'assets/fonts/6xK1dSBYKcSV-LCoeQqfX1RYOo3qPZ7nsDI.woff2',
    'assets/fonts/6xK1dSBYKcSV-LCoeQqfX1RYOo3qPZ7nsDJB9cme.woff2',
    'assets/fonts/6xK1dSBYKcSV-LCoeQqfX1RYOo3qPZ7osDJB9cme_xc.woff2',
    'assets/fonts/6xK1dSBYKcSV-LCoeQqfX1RYOo3qPZ7osDJT9g.woff2',
    'assets/fonts/6xK1dSBYKcSV-LCoeQqfX1RYOo3qPZ7psDJB9cme_xc.woff2',
    'assets/fonts/6xK1dSBYKcSV-LCoeQqfX1RYOo3qPZ7psDJT9g.woff2',
    'assets/fonts/6xK1dSBYKcSV-LCoeQqfX1RYOo3qPZ7qsDJB9cme_xc.woff2',
    'assets/fonts/6xK1dSBYKcSV-LCoeQqfX1RYOo3qPZ7qsDJT9g.woff2',
    'assets/fonts/6xK1dSBYKcSV-LCoeQqfX1RYOo3qPZ7rsDJB9cme_xc.woff2',
    'assets/fonts/6xK1dSBYKcSV-LCoeQqfX1RYOo3qPZ7rsDJT9g.woff2',
    'assets/fonts/6xK3dSBYKcSV-LCoeQqfX1RYOo3qN67lqDY.woff2',
    'assets/fonts/6xK3dSBYKcSV-LCoeQqfX1RYOo3qN67lujVj9_mf.woff2',
    'assets/fonts/6xK3dSBYKcSV-LCoeQqfX1RYOo3qNK7lqDY.woff2',
    'assets/fonts/6xK3dSBYKcSV-LCoeQqfX1RYOo3qNK7lujVj9_mf.woff2',
    'assets/fonts/6xK3dSBYKcSV-LCoeQqfX1RYOo3qNa7lqDY.woff2',
    'assets/fonts/6xK3dSBYKcSV-LCoeQqfX1RYOo3qNa7lujVj9_mf.woff2',
    'assets/fonts/6xK3dSBYKcSV-LCoeQqfX1RYOo3qNq7lqDY.woff2',
    'assets/fonts/6xK3dSBYKcSV-LCoeQqfX1RYOo3qNq7lujVj9_mf.woff2',
    'assets/fonts/6xK3dSBYKcSV-LCoeQqfX1RYOo3qO67lqDY.woff2',
    'assets/fonts/6xK3dSBYKcSV-LCoeQqfX1RYOo3qO67lujVj9_mf.woff2',
    'assets/fonts/6xK3dSBYKcSV-LCoeQqfX1RYOo3qOK7l.woff2',
    'assets/fonts/6xK3dSBYKcSV-LCoeQqfX1RYOo3qOK7lujVj9w.woff2',
    'assets/fonts/6xK3dSBYKcSV-LCoeQqfX1RYOo3qPK7lqDY.woff2',
    'assets/fonts/6xK3dSBYKcSV-LCoeQqfX1RYOo3qPK7lujVj9_mf.woff2',
    'assets/fonts/6xKwdSBYKcSV-LCoeQqfX1RYOo3qPZZclSdg18S0xR41YDw.woff2',
    'assets/fonts/6xKwdSBYKcSV-LCoeQqfX1RYOo3qPZZclSdg18Smxg.woff2',
    'assets/fonts/6xKwdSBYKcSV-LCoeQqfX1RYOo3qPZZclSdh18S0xR41YDw.woff2',
    'assets/fonts/6xKwdSBYKcSV-LCoeQqfX1RYOo3qPZZclSdh18Smxg.woff2',
    'assets/fonts/6xKwdSBYKcSV-LCoeQqfX1RYOo3qPZZclSdi18S0xR41YDw.woff2',
    'assets/fonts/6xKwdSBYKcSV-LCoeQqfX1RYOo3qPZZclSdi18Smxg.woff2',
    'assets/fonts/6xKwdSBYKcSV-LCoeQqfX1RYOo3qPZZclSdj18S0xR41YDw.woff2',
    'assets/fonts/6xKwdSBYKcSV-LCoeQqfX1RYOo3qPZZclSdj18Smxg.woff2',
    'assets/fonts/6xKwdSBYKcSV-LCoeQqfX1RYOo3qPZZclSdo18S0xR41YDw.woff2',
    'assets/fonts/6xKwdSBYKcSV-LCoeQqfX1RYOo3qPZZclSdo18Smxg.woff2',
    'assets/fonts/6xKwdSBYKcSV-LCoeQqfX1RYOo3qPZZclSds18Q.woff2',
    'assets/fonts/6xKwdSBYKcSV-LCoeQqfX1RYOo3qPZZclSds18S0xR41.woff2',
    'assets/fonts/6xKwdSBYKcSV-LCoeQqfX1RYOo3qPZZclSdv18S0xR41YDw.woff2',
    'assets/fonts/6xKwdSBYKcSV-LCoeQqfX1RYOo3qPZZclSdv18Smxg.woff2',
    'assets/fonts/6xKydSBYKcSV-LCoeQqfX1RYOo3ig4vwkxdu3cOWxy40.woff2',
    'assets/fonts/6xKydSBYKcSV-LCoeQqfX1RYOo3ig4vwkxduz8A.woff2',
    'assets/fonts/6xKydSBYKcSV-LCoeQqfX1RYOo3ig4vwlBdu3cOWxy40.woff2',
    'assets/fonts/6xKydSBYKcSV-LCoeQqfX1RYOo3ig4vwlBduz8A.woff2',
    'assets/fonts/6xKydSBYKcSV-LCoeQqfX1RYOo3ig4vwlxdu.woff2',
    'assets/fonts/6xKydSBYKcSV-LCoeQqfX1RYOo3ig4vwlxdu3cOWxw.woff2',
    'assets/fonts/6xKydSBYKcSV-LCoeQqfX1RYOo3ig4vwmBdu3cOWxy40.woff2',
    'assets/fonts/6xKydSBYKcSV-LCoeQqfX1RYOo3ig4vwmBduz8A.woff2',
    'assets/fonts/6xKydSBYKcSV-LCoeQqfX1RYOo3ig4vwmRdu3cOWxy40.woff2',
    'assets/fonts/6xKydSBYKcSV-LCoeQqfX1RYOo3ig4vwmRduz8A.woff2',
    'assets/fonts/6xKydSBYKcSV-LCoeQqfX1RYOo3ig4vwmhdu3cOWxy40.woff2',
    'assets/fonts/6xKydSBYKcSV-LCoeQqfX1RYOo3ig4vwmhduz8A.woff2',
    'assets/fonts/6xKydSBYKcSV-LCoeQqfX1RYOo3ig4vwmxdu3cOWxy40.woff2',
    'assets/fonts/6xKydSBYKcSV-LCoeQqfX1RYOo3ig4vwmxduz8A.woff2',
    'assets/fonts/HI_SiYsKILxRpg3hIP6sJ7fM7PqlM-vWjMY.woff2',
    'assets/fonts/HI_SiYsKILxRpg3hIP6sJ7fM7PqlM-vWnsUnxlC9.woff2',
    'assets/fonts/HI_SiYsKILxRpg3hIP6sJ7fM7PqlMOvWjMY.woff2',
    'assets/fonts/HI_SiYsKILxRpg3hIP6sJ7fM7PqlMOvWnsUnxlC9.woff2',
    'assets/fonts/HI_SiYsKILxRpg3hIP6sJ7fM7PqlMuvWjMY.woff2',
    'assets/fonts/HI_SiYsKILxRpg3hIP6sJ7fM7PqlMuvWnsUnxlC9.woff2',
    'assets/fonts/HI_SiYsKILxRpg3hIP6sJ7fM7PqlOevWjMY.woff2',
    'assets/fonts/HI_SiYsKILxRpg3hIP6sJ7fM7PqlOevWnsUnxlC9.woff2',
    'assets/fonts/HI_SiYsKILxRpg3hIP6sJ7fM7PqlPevW.woff2',
    'assets/fonts/HI_SiYsKILxRpg3hIP6sJ7fM7PqlPevWnsUnxg.woff2',
    'assets/fonts/HI_SiYsKILxRpg3hIP6sJ7fM7PqlPuvWjMY.woff2',
    'assets/fonts/HI_SiYsKILxRpg3hIP6sJ7fM7PqlPuvWnsUnxlC9.woff2',
    'assets/fonts/_hints_off.css.gz',
    'assets/fonts/_hints_on.css.gz',
    'assets/highlight/LICENSE',
    'assets/highlight/highlight.pack.js',
    'assets/highlight/styles/default.css',
    'assets/style.css',
    'assets/LICENSE',
]


class actions(Namespace):
    def extract_assets(run_config: Build):
        with tarfile.open(str(tarball)) as f:
            f.extractall(str(run_config.output_path))
        # decompress .gz files
        for asset in bundled_assets:
            if Path(asset).suffix == '.gz':
                src_path = run_config.output_path / asset
                write_to = src_path.parent / src_path.stem
                decompress_and_rewrite(src_path, write_to, run_config.mount_point)


def decompress_and_rewrite(source: Path, target: Path, mount_point: str):
    assets_re = re.compile(re.escape(b'/assets/'))
    replace_with = mount_point.encode('utf8') + b'/assets/'
    rewrite = target.suffix == '.css'
    with gzip.open(str(source), 'rb') as f, target.open('wb') as g:
        while True:
            content = f.read(1024)
            if not content:
                break
            if rewrite:
                content = assets_re.sub(replace_with, content)
            g.write(content)
    # re-compress the rewritten content
    if rewrite:
        with target.open('rb') as f, gzip.open(str(source), 'wb') as g:
            while True:
                content = f.read(1024)
                if not content:
                    break
                g.write(content)
