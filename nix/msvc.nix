{ pkgs }:
let
  payload = {
    name = "msvc-17.8.23-sdk-10.0.22621-payload.tar.gz";
    sha256 = "30c9c589f52f431e926ce9db1775657f07c22b7898d900b2814958c48024b463";
    upstreamRevision = "61b7cbc8cb9413fec8f0016ef433a90e06c37f54";
    channel = "release.ltsc.17.8";
    msvcVersion = "17.8";
    sdkVersion = "10.0.22621";
    manifestUrl = "https://download.visualstudio.microsoft.com/download/pr/bd2300cc-5700-4b59-955d-4e5ef66b964a/8f12f164877bbb7606c2ccbbd100db632013966c4a27cbb16ecace9c156d3e74/VisualStudio.vsman";
  };
  source = pkgs.requireFile {
    inherit (payload) name sha256;
    message = ''
      Microsoft licenses prohibit public redistribution of this toolchain.
      Run bash nix/bootstrap-msvc.sh after accepting the Microsoft license.
      The bootstrap downloads the pinned payload and imports it into the local store.
    '';
  };
  installationEnvironment = pkgs.buildFHSEnv {
    name = "msvc-install-env";
    targetPkgs = p: with p; [
      bash coreutils findutils gawk gnugrep gnused git python3 perl
      msitools unzip wineWow64Packages.stable samba
    ];
    runScript = "bash";
  };
in
pkgs.stdenvNoCC.mkDerivation {
  pname = "msvc-wine";
  version = "17.8.23";
  src = source;
  nativeBuildInputs = [ pkgs.gnutar pkgs.gzip ];
  dontUnpack = true;
  dontConfigure = true;
  dontBuild = true;
  dontFixup = true;
  preferLocalBuild = true;
  allowSubstitutes = false;

  installPhase = ''
    runHook preInstall
    mkdir payload
    tar -xzf "$src" -C payload
    substituteInPlace payload/upstream/wrappers/msvcenv.sh \
      --replace-fail 'export WINEDLLOVERRIDES="vcruntime140=n;vcruntime140_1=n"' \
        'export WINEDLLOVERRIDES="vcruntime140=n;vcruntime140_1=n''${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"'
    export HOME="$TMPDIR/msvc-home"
    export WINEPREFIX="$TMPDIR/msvc-wine-prefix"
    export WINEDEBUG=-all
    export WINEDLLOVERRIDES="mscoree,mshtml="
    mkdir -p "$HOME"
    cat > install-msvc.sh <<'INSTALL'
    set -euo pipefail
    unset DISPLAY WAYLAND_DISPLAY
    export PATH=/usr/bin:/bin:$PATH
    python3 payload/upstream/vsdownload.py \
      --accept-license --manifest "$PWD/payload/manifest.json" \
      --msvc-version ${payload.msvcVersion} --sdk-version ${payload.sdkVersion} \
      --host-arch x64 --cache "$PWD/payload/cache" --dest "$PWD/installed" \
      Microsoft.Net.4.8.SDK Microsoft.VisualStudio.MinShell
    bash payload/upstream/install.sh "$PWD/installed"
    test -f installed/bin/msvctricks.exe
    test -f installed/bin/process_sourcedependencies.exe
    wineserver -w
    INSTALL
    ${installationEnvironment}/bin/msvc-install-env install-msvc.sh
    mkdir -p "$out"
    cp -a installed/. "$out/"
    runHook postInstall
  '';

  passthru = { inherit payload installationEnvironment; };
  meta = {
    description = "Microsoft Visual C++ 17.8 toolchain and Windows SDK for Wine";
    license = pkgs.lib.licenses.unfree;
    platforms = [ "x86_64-linux" ];
  };
}
