```bash
version=1.0.0
git checkout -b release-$version
nix-shell

# bump the version
vi pyproject.toml

# configure poetry
poetry config repositories.test https://test.pypi.org/legacy/
poetry config repositories.local http://127.0.0.1:8080/

# in a different shell; if testing the package locally
mkdir -p packages
pypi-server -p 8080 -i 127.0.0.1 -P . -a . --overwrite ./packages

# publish to local / test pypi
poetry build -v
poetry publish -r local # user/pass can be anything
# or
poetry publish -r test

# make a virtualenv and install prereqs
rm -rf env
python -m venv env
. env/bin/activate
npm install elm

# final check
pip install -i http://localhost:8080/ --extra-index-url https://pypi.org/simple elm-doc
# or
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple elm-doc
rm -rf workspace/0.19.1/build/docs
elm-doc workspace/0.19.1 -o workspace/0.19.1/build/docs --mount-at /docs --elm-path ./node_modules/.bin/elm
spark workspace/0.19.1/build
# open http://localhost:8080/docs and click around
git push # make sure CI is green

# publish to the real pypi
poetry build -v
poetry publish
git tag $version

# merge the branch to master and push the tag
```
