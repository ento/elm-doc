{ pythonVersion ? "38" }:
let
  pkgs = import <nixpkgs> {};
  python = pkgs."python${pythonVersion}".override {
    packageOverrides = self: super: {
      clikit = super.clikit.overridePythonAttrs (old: rec {
        # mark crashtest as python = ^3.6
        propagatedBuildInputs = with self; [
          pylev pastel
        ] ++ pkgs.lib.optionals (self.pythonAtLeast "3.6") [ crashtest ]
        ++ pkgs.lib.optionals self.isPy27 [ typing enum34 ];
      });
      distlib = super.distlib.overridePythonAttrs (old: rec {
        version = "0.3.1";
        src = self.fetchPypi {
          inherit (old) pname;
          inherit version;
          extension = "zip";
          sha256 = "1wdzv7fsjhrkhh1wfkarlhcwa8m00mgcpdsvknmf2qy8f9l13xpd";
        };
      });
      keyring =
        if self.pythonAtLeast "3.6"
        then super.keyring
        else super.keyring.overridePythonAttrs (old: rec {
          version = "20.0.1";
          src = self.fetchPypi {
            inherit (old) pname;
            inherit version;
            sha256 = "963bfa7f090269d30bdc5e25589e5fd9dad2cf2a7c6f176a7f2386910e5d0d8d";
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
        # checks depend on httpretty, which doesn't support 3.5
        doCheck = false;
        propagatedBuildInputs =
          old.propagatedBuildInputs
          ++ (with self; [ poetry-core virtualenv ]
                         ++ pkgs.lib.optionals (pythonAtLeast "3.6") [ crashtest ] );
        postPatch = ''
          substituteInPlace pyproject.toml \
           --replace "requests-toolbelt = \"^0.8.0\"" "requests-toolbelt = \"^0.9.1\"" \
           --replace 'importlib-metadata = {version = "^1.6.0", python = "<3.8"}' \
             'importlib-metadata = {version = ">=1.3,<2", python = "<3.8"}' \
           --replace "tomlkit = \"^0.5.11\"" "tomlkit = \"^0.6.0\"" \
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
  spark = pkgs.buildGoPackage rec {
    pname = "spark";
    version = "1.7.3";
    src = pkgs.fetchFromGitHub {
      owner = "rif";
      repo = pname;
      rev = "v${version}";
      sha256 = "0w3gcn4z8ayln08scwx449hv18ll5bmpk3m8kzn24nmm4crn6ymk";
    };
    goPackagePath = "github.com/rif/spark";
  };
in
pkgs.mkShell {
  buildInputs = with pkgs; [
    libffi
    nodejs
    python.pkgs.poetry
    rsync
    spark
  ];
  shellHook = ''
    export SOURCE_DATE_EPOCH=315532800
  '';
}
