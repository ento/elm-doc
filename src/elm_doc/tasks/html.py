import json
import html
from pathlib import Path

from elm_doc.utils import Namespace


# Note: title tag is omitted, as the Elm app sets the title after
# it's initialized.
PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <link rel="shortcut icon" size="16x16, 32x32, 48x48, 64x64, 128x128, 256x256" href="{mount_point}/assets/favicon.ico">
    <link rel="stylesheet" href="{mount_point}/assets/style.css">
    <script src="{mount_point}/artifacts/elm.js"></script>
    <script src="{mount_point}/assets/highlight/highlight.pack.js"></script>
    <link rel="stylesheet" href="{mount_point}/assets/highlight/styles/default.css">
  </head>
  <body>
  <script>
    try {{
      const fontsLink = document.createElement("link");
      fontsLink.href = "{mount_point}/assets/fonts/" + ((navigator.userAgent.indexOf("Macintosh") > -1) ? "_hints_off.css" : "_hints_on.css");
      fontsLink.rel = "stylesheet";
      document.head.appendChild(fontsLink);
    }} catch(e) {{
      // loading the font is not essential; log the error and move on
      console.log(e);
    }}

    Elm.Main.init({init});
  </script>
  </body>
</html>
'''  # noqa: E501


def _render(mount_point: str = ''):
    if mount_point and mount_point[-1] == '/':
        mount_point = mount_point[:-1]
    init = {
        'flags': {
            'mountedAt': mount_point,
        },
    }
    return PAGE_TEMPLATE.format(
        mount_point=html.escape(mount_point),
        init=json.dumps(init))


class actions(Namespace):
    def write(output_path: Path, mount_point: str = ''):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(output_path), 'w') as f:
            f.write(_render(mount_point=mount_point))
