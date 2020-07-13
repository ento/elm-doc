let
  pkgs = import <nixpkgs> {};
in
pkgs.mkShell {
  buildInputs = with pkgs; [
    nodejs
    poetry
    rsync
  ];
  shellHook = ''
    export SOURCE_DATE_EPOCH=315532800
  '';
}
