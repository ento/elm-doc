# How to deploy changes to the internal elm docs site

After making and committing changes to [brilliantorg/package.elm-lang.org](https://github.com/brilliantorg/package.elm-lang.org/tree/master):

```bash
# Update the git submodule in this directory
cd vendor/package.elm-lang.org
git pull
cd ../..

# bump the version
vi pyproject.toml

# rebuild the wheel
poetry build

# copy
cp ./dist/elm_doc-[version-number]-py3-none-any.whl /path/to/brilliant/local_wheels/

# update line in requirements.txt
vi /path/to/brilliant/requirements.txt
# search for elm_doc and update the version number

# reinstall python packages
cd /path/to/brilliant/
/path/to/virtualenv/python brilliant/utils/shellscripts/pip_install.py
```
