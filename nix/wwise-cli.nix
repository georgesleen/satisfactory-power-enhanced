{ pkgs }:
pkgs.stdenvNoCC.mkDerivation {
  pname = "wwise-cli";
  version = "0.2.4";
  src = pkgs.fetchurl {
    url = "https://github.com/mircearoata/wwise-cli/releases/download/v0.2.4/wwise-cli_linux_amd64";
    sha256 = "23ff2858e275ed33c02fad7ab96b0bab12c8a0c2015a90c6df820a55dca6ea9f";
  };
  dontUnpack = true;
  installPhase = ''
    install -Dm755 "$src" "$out/bin/wwise-cli"
  '';
  meta.platforms = [ "x86_64-linux" ];
}
