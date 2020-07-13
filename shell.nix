let
  pkgs = import <nixpkgs> {};
  poetry-core = pkgs.python3Packages.buildPythonPackage rec {
    pname = "poetry-core";
    version = "1.0.0a8";
    src = pkgs.python3Packages.fetchPypi {
      inherit pname version;
      sha256 = "15advjnc719zx7ak16qlzff9k9zqlc8r3i2whvps9zd4p9d7w8q2";
    };
    nativeBuildInputs = with pkgs.python3Packages; [ intreehooks ];
    dontUseSetuptoolsCheck = true;
  };
  poetry = pkgs.python3Packages.poetry.overridePythonAttrs(old: rec {
    version = "1.1.0a3";
    src = pkgs.fetchFromGitHub {
      owner = "python-poetry";
      repo = "poetry";
      rev = version;
      sha256 = "1n30q95ipa6jac503ba6ispbf9vf8w7pzma21yfvip6ccd892dxm";
    };
    # appears to be broken as of 1.1.0a3
    disabledTests = old.disabledTests ++ [ "test_execute_executes_a_batch_of_operations" ];
    propagatedBuildInputs = old.propagatedBuildInputs ++ [ poetry-core ];
    postPatch = ''
      substituteInPlace pyproject.toml \
       --replace "requests-toolbelt = \"^0.8.0\"" "requests-toolbelt = \"^0.9.1\"" \
       --replace 'importlib-metadata = {version = "^1.6.0", python = "<3.8"}' \
         'importlib-metadata = {version = ">=1.3,<2", python = "<3.8"}' \
       --replace "tomlkit = \"^0.5.11\"" "tomlkit = \"^0.6.0\"" \
       --replace "version = \"^20.0.1\", python = \"~3.5\"" "version = \"^21.0.0\", python = \"^3.5\""
    '';
  });
in
pkgs.mkShell {
  buildInputs = with pkgs; [
    libffi
    nodejs
    poetry
    rsync
  ];
  shellHook = ''
    export SOURCE_DATE_EPOCH=315532800
  '';
}
