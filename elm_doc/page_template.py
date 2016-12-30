import json


PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <link rel="shortcut icon" size="16x16, 32x32, 48x48, 64x64, 128x128, 256x256" href="{mount_point}/assets/favicon.ico">
    <link rel="stylesheet" href="{mount_point}/assets/highlight/styles/default.css">
    <link rel="stylesheet" href="{mount_point}/assets/style.css">
    <script src="{mount_point}/assets/highlight/highlight.pack.js"></script>
    <script src="{mount_point}/artifacts/Page-{page_module}.js"></script>
  </head>
  <body>
  <script>
    var page = Elm.Page.{page_module}.fullscreen({flags_json});
  </script>
  </body>
</html>
'''  # noqa: E501


def render(page_module: str, flags: dict = None, mount_point: str = ''):
    flags_json = json.dumps(flags) if flags else ''
    return PAGE_TEMPLATE.format(
        mount_point=mount_point, page_module=page_module, flags_json=flags_json)
