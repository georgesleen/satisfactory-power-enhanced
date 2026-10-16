{ pkgs }:
let
  version = "5.6.1-css-83";
  hashes = [
    "5847a80489d04e7ec231de01c154e1046174aa69f5d2c00023a62a67626001e7"
    "06e8177c34ac2cae5568a71dc92b735162ee29987e964ecf312620f0b11a8d9f"
    "b624c15b9becf336b6ed4e71b73498f208d3f6edaf857e0bcdcebce7540a9362"
    "565829545aff54f3771ac80d00e6edea38fd0a235c723c55be063f563aadb049"
  ];
  parts = pkgs.lib.imap0 (
    index: hash:
    pkgs.requireFile {
      name = "UnrealEngine-CSS-Editor-Linux.tar.zst.0${toString index}";
      sha256 = hash;
      message = ''
        CSS Unreal Engine ${version} requires authorized GitHub access.
        Run make bootstrap-engine from this checkout to download, verify and import
        the four licensed release parts. No credentials are passed to Nix builds.
      '';
    }
  ) hashes;
in
pkgs.stdenvNoCC.mkDerivation {
  pname = "unreal-engine-css";
  inherit version;
  dontUnpack = true;
  nativeBuildInputs = [
    pkgs.zstd
    pkgs.gnutar
  ];
  installPhase = ''
    set -o pipefail
    mkdir -p "$out"
    cat ${pkgs.lib.escapeShellArgs (map toString parts)} | zstd -d | tar -x -C "$out"
    chmod u+x "$out/Engine/Binaries/ThirdParty/DotNet/8.0.300/linux-x64/dotnet"
    substituteInPlace "$out/Engine/Build/BatchFiles/Linux/SetupDotnet.sh" \
      --replace-fail 'chmod u+x "$UE_DOTNET_DIR/dotnet"' ': # Dotnet permissions are fixed in the immutable package.'
  '';
  dontFixup = true;
  meta = {
    description = "Licensed CSS Unreal Engine installed Linux editor";
    license = pkgs.lib.licenses.unfree;
    platforms = [ "x86_64-linux" ];
  };
  preferLocalBuild = true;
  allowSubstitutes = false;
}
