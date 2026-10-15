{ pkgs }:
let
  metadataFile = ./wwise-source.json;
  metadata = if builtins.pathExists metadataFile then builtins.fromJSON (builtins.readFile metadataFile) else
    throw ''
      Wwise SDK 2025.1.6.9117 + UE integration 2025.1.6.4248 require an Audiokinetic account.
      Run make bootstrap-wwise interactively, then make import-wwise.
      The bootstrap uses upstream wwise-cli and prompts locally; never put credentials in Nix.
      The import records the licensed payload hash in nix/wwise-source.json.
    '';
  source = pkgs.requireFile {
    name = "enhancedpower-wwise-2025.1.6.9117-2025.1.6.4248.tar.zst";
    sha256 = metadata.sha256;
    message = "Run make import-wwise to import the locally downloaded licensed Wwise payload.";
  };
in
pkgs.stdenvNoCC.mkDerivation {
  pname = "enhancedpower-wwise";
  version = "2025.1.6.9117-2025.1.6.4248";
  src = source;
  nativeBuildInputs = [ pkgs.zstd ];
  dontUnpack = true;
  installPhase = ''
    mkdir -p "$out"
    tar --zstd -xf "$src" -C "$out"
  '';
  dontFixup = true;
  preferLocalBuild = true;
  allowSubstitutes = false;
  meta.license = pkgs.lib.licenses.unfree;
  meta.platforms = [ "x86_64-linux" ];
}
