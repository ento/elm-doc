{ pythonVersion ? "38" }:
let
  pkgs = import <nixpkgs> {};
  python = pkgs."python${pythonVersion}".override {
    packageOverrides = self: super: {
      distlib = super.distlib.overridePythonAttrs (old: rec {
        version = "0.3.1";
        src = self.fetchPypi {
          inherit (old) pname;
          inherit version;
          extension = "zip";
          sha256 = "1wdzv7fsjhrkhh1wfkarlhcwa8m00mgcpdsvknmf2qy8f9l13xpd";
        };
      });
      poetry = super.poetry.overridePythonAttrs (old: rec {
        version = "1.1.0a4-c264bc0";
        src = pkgs.fetchFromGitHub {
          owner = "python-poetry";
          repo = "poetry";
          rev = "c264bc0"; # includes #2664
          sha256 = "008qx6c8qgwkn5j95vz5dwnk9926i2ia4irs3gn4kcwnl4m4crz4";
        };
        # appears to be broken as of 1.1.0a3
        disabledTests = old.disabledTests ++ [
          "test_execute_executes_a_batch_of_operations"
          "test_create_venv_tries_to_find_a_compatible_python_executable_using_specific_ones"
          "test_builder_installs_proper_files_for_standard_packages"
          "test_create_poetry"
        ];
        propagatedBuildInputs = old.propagatedBuildInputs ++ (with self; [ poetry-core virtualenv ]);
        postPatch = ''
          substituteInPlace pyproject.toml \
           --replace "requests-toolbelt = \"^0.8.0\"" "requests-toolbelt = \"^0.9.1\"" \
           --replace 'importlib-metadata = {version = "^1.6.0", python = "<3.8"}' \
             'importlib-metadata = {version = ">=1.3,<2", python = "<3.8"}' \
           --replace "tomlkit = \"^0.5.11\"" "tomlkit = \"^0.6.0\"" \
           --replace "version = \"^20.0.1\", python = \"~3.5\"" "version = \"^21.0.0\", python = \"^3.5\""
        '';
      });
      poetry-core = self.buildPythonPackage rec {
        pname = "poetry-core";
        version = "1.0.0a8-ada9bf8";
        format = "pyproject";
        src = pkgs.fetchFromGitHub {
          owner = "python-poetry";
          repo = pname;
          rev = "ada9bf8";
          sha256 = "17hzmh71wzr2ra3ql8i22lcx611nww6xk9j9vcpsv1g5z19w4pv2";
        };
        nativeBuildInputs = with self; [ intreehooks ];
        dontUseSetuptoolsCheck = true;
      };
      virtualenv = super.virtualenv.overridePythonAttrs (old: rec {
        version = "20.0.26";
        src = self.fetchPypi {
          inherit (old) pname;
          inherit version;
          sha256 = "0wm1jxm00wgi4j11028gv38as5fwqhsd7qfz42blbnnb81pwc371";
        };
      });
    };
  };
in
pkgs.mkShell {
  buildInputs = with pkgs; [
    libffi
    nodejs
    python.pkgs.poetry
    rsync
  ];
  shellHook = ''
    export SOURCE_DATE_EPOCH=315532800
  '';
}
