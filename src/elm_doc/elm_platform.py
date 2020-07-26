import os
from pathlib import Path


# See: https://github.com/elm/compiler/blob/0.19.0/builder/src/Elm/PerUserCache.hs#L44
# Note: this implementation is not exactly the same as the above, which uses
# getAppUserDataDirectory:
# http://hackage.haskell.org/package/directory-1.3.3.1/docs/System-Directory.html#v:getAppUserDataDirectory
# On Windows, this is something like 'C:/Users/<user>/AppData/Roaming/<app>'.
# elm-doc currently doesn't support Windows, so this is fine for now.
ELM_HOME = Path(os.environ['ELM_HOME']) if 'ELM_HOME' in os.environ else (Path.home() / '.elm')
