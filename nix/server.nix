{ pkgs }:
let
  appId = "1690800";
  metadataFile = ./server-source.json;
  # Placeholder metadata keeps evaluation working until make bootstrap-server records the archive.
  metadata =
    if builtins.pathExists metadataFile then
      builtins.fromJSON (builtins.readFile metadataFile)
    else
      {
        buildId = "unbootstrapped";
        name = "satisfactory-server-unbootstrapped.tar.zst";
        sha256 = pkgs.lib.fakeSha256;
      };
  source = pkgs.requireFile {
    inherit (metadata) name sha256;
    message = ''
      The Satisfactory dedicated server (Steam app ${appId}) is free but not redistributable.
      Run make bootstrap-server from this checkout. It downloads the server with anonymous
      SteamCMD, imports the archive, and records its hash in nix/server-source.json.
    '';
  };
  smlVersion = "3.12.0";
in
rec {
  # Unmodified dedicated server tree for one Steam build.
  server = pkgs.stdenvNoCC.mkDerivation {
    pname = "satisfactory-server";
    version = metadata.buildId;
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
    meta = {
      description = "Satisfactory dedicated server, Steam build ${metadata.buildId}";
      license = pkgs.lib.licenses.unfree;
      platforms = [ "x86_64-linux" ];
    };
  };

  # Published Satisfactory Mod Loader for Linux dedicated servers.
  sml = pkgs.stdenvNoCC.mkDerivation {
    pname = "sml-linux-server";
    version = smlVersion;
    src = pkgs.fetchurl {
      url = "https://github.com/satisfactorymodding/SatisfactoryModLoader/releases/download/v${smlVersion}/SML-LinuxServer.zip";
      sha256 = "cb2904f76100477bb031a7322dc990de34cc62dd28f9506728b7d1ce310570d1";
    };
    nativeBuildInputs = [ pkgs.unzip ];
    dontUnpack = true;
    installPhase = ''
      mkdir -p "$out"
      unzip -q "$src" -d "$out"
    '';
    dontFixup = true;
    meta = {
      description = "Satisfactory Mod Loader ${smlVersion}, LinuxServer target";
      license = pkgs.lib.licenses.gpl3Only;
      platforms = [ "x86_64-linux" ];
    };
  };

  # Starts a disposable loopback-only server instance with SML under SF_ROOT.
  run = pkgs.writeShellApplication {
    name = "sf-server";
    runtimeInputs = [
      pkgs.coreutils
      pkgs.findutils
      pkgs.steam-run
      pkgs.bubblewrap
    ];
    runtimeEnv = {
      SF_SERVER = server;
      SF_SML = sml;
    };
    text = builtins.readFile ./run-server.sh;
  };

  # Starts the server, drives the HTTPS API through one world, and stops the server.
  smoke = pkgs.writeShellApplication {
    name = "sf-server-smoke";
    runtimeInputs = [
      run
      pkgs.coreutils
      pkgs.curl
      pkgs.jq
      pkgs.gnugrep
      pkgs.iproute2
      pkgs.bubblewrap
    ];
    text = builtins.readFile ./smoke-server.sh;
  };
}
