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
        version = "1.1.4";
        src = pkgs.fetchFromGitHub {
          owner = "python-poetry";
          repo = "poetry";
          rev = version;
          sha256 = "0lx3qpz5dad0is7ki5a4vxphvc8cm8fnv4bmrx226a6nvvaj6ahs";
        };
        # checks depend on httpretty, which doesn't support 3.5
        doCheck = false;
        propagatedBuildInputs =
          old.propagatedBuildInputs
          ++ (with self; [ poetry-core virtualenv ]
                         ++ pkgs.lib.optionals (pythonAtLeast "3.6") [ crashtest ] );
      });
      poetry-core = self.buildPythonPackage rec {
        pname = "poetry-core";
        version = "1.0.0";
        format = "pyproject";
        src = pkgs.fetchFromGitHub {
          owner = "python-poetry";
          repo = pname;
          rev = version;
          sha256 = "02pqkwzbg43xz2zsw8q7m0sfkj8wbw07in83gy0bk0znhljhp0vw";
        };
        nativeBuildInputs = with self; [ intreehooks ];
        dontUseSetuptoolsCheck = true;
      };
      pypiserver = self.buildPythonPackage rec {
        pname = "pypiserver";
        version = "1.3.2";
        format = "pyproject";
        src = self.fetchPypi {
          inherit pname version;
          sha256 = "0qnf3qg0mx1whbysq072y0wpj0s3kkld96wzfmnqdi72mk8f3li1";
          extension = "zip";
        };
        propagatedBuildInputs = with self; [ setuptools setuptools-git wheel ];
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
    python.pkgs.pypiserver
    rsync
    spark
  ];
  shellHook = ''
    export SOURCE_DATE_EPOCH=315532800
  '';
}
