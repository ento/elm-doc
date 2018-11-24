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
    <script src="{mount_point}/artifacts/elm.js"></script>
  </head>
  <body>
  <script>
    Elm.Main.init({init});
  </script>
  </body>
</html>
'''  # noqa: E501


def render(mount_point: str = ''):
    if mount_point and mount_point[-1] == '/':
        mount_point = mount_point[:-1]
    init = {
        'flags': {
            'mountedAt': mount_point,
        },
    }
    return PAGE_TEMPLATE.format(mount_point=mount_point, init=json.dumps(init))
