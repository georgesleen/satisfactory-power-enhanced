{
  description = "FHS environment for Satisfactory modding (UE 5.6.1-CSS, msvc-wine, Wwise)";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; config.allowUnfree = true; };
      engine = import ./nix/engine.nix { inherit pkgs; };
      msvc = import ./nix/msvc.nix { inherit pkgs; };
      wwiseCli = import ./nix/wwise-cli.nix { inherit pkgs; };
      wwise = import ./nix/wwise.nix { inherit pkgs; };

      sfEnv = pkgs.buildFHSEnv {
        name = "sf-env";

        targetPkgs =
          p: with p; [
            # Shell tools that UE scripts, msvc-wine, and the Wwise patches call.
            bash
            coreutils
            findutils
            gnugrep
            gnused
            gawk
            gnupatch
            gnutar
            gzip
            zstd
            dos2unix
            which
            file
            git
            gh
            curl
            unzip
            gnumake
            wwiseCli
            python3
            perl
            msitools
            pciutils
            xdg-utils

            # MSVC under Wine; ntlm_auth supports mspdbsrv.
            wineWow64Packages.stable
            samba

            # Bundled dotnet 8 (UBT, UAT).
            icu
            krb5
            openssl
            zlib
            lttng-ust

            # Prebuilt clang toolchain and editor runtime.
            stdenv.cc.cc.lib
            glibc
            libuuid
            libxcrypt-legacy
            libunwind
            ncurses
            systemd
            expat
            dbus

            # Graphics: Vulkan loader; the Mesa ICDs come from /run/opengl-driver.
            vulkan-loader
            vulkan-tools
            libGL
            libglvnd
            libdrm
            libgbm

            # Windowing: SDL with X11 (XWayland) and Wayland libraries.
            sdl3
            SDL2
            wayland
            libdecor
            libxkbcommon
            libx11
            libxcb
            libxcursor
            libxi
            libxrandr
            libxext
            libxrender
            libxfixes
            libxcomposite
            libxdamage
            libxscrnsaver
            libxtst
            libxshmfence
            libxxf86vm

            # Fonts, CEF web browser widget, dialogs.
            fontconfig
            freetype
            nss
            nspr
            atk
            at-spi2-atk
            at-spi2-core
            cups
            gtk3
            pango
            cairo
            glib
            libsecret

            # Audio.
            alsa-lib
            libpulseaudio

            # IDE support outside the editor.
            clang-tools
          ];


        profile = ''
          export SF_ROOT="''${SF_ROOT:-''${XDG_DATA_HOME:-$HOME/.local/share}/sf}"
          export UE_ROOT="''${UE_ROOT:-${engine}}"
          export UE_WINE_MSVC="''${UE_WINE_MSVC:-${msvc}}"
          export WINEPREFIX="''${WINEPREFIX:-$SF_ROOT/wine}"
          export WINEDEBUG="''${WINEDEBUG:--all}"
          export SML_DIR="''${SML_DIR:-$SF_ROOT/s}"
          export MOD_REPO="''${MOD_REPO:-$HOME/Documents/projects/satisfactory-power-enhanced}"
          export SF_GAME_DIR="''${SF_GAME_DIR:-$HOME/.local/share/Steam/steamapps/common/Satisfactory}"
          export SF_PREFIX="''${SF_PREFIX:-$HOME/.local/share/Steam/steamapps/compatdata/526870/pfx}"
          export XDG_CACHE_HOME="$SF_ROOT/cache"
          export TMPDIR="$SF_ROOT/tmp"
          export HOME="$SF_ROOT/home"
          export XDG_CONFIG_HOME="$SF_ROOT/config"
          mkdir -p "$HOME" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$TMPDIR"

          # Mesa Vulkan ICDs from the host driver.
          if [ -d /run/opengl-driver/share/vulkan/icd.d ]; then
            export VK_DRIVER_FILES="$(find /run/opengl-driver/share/vulkan/icd.d -name '*.json' | tr '\n' ':' | sed 's/:$//')"
          fi
          export LD_LIBRARY_PATH="/run/opengl-driver/lib''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

          # The editor runs through XWayland under sway.
          export SDL_VIDEODRIVER=x11

          # The bundled dotnet 8 may not find ICU 78 by version probe.
          export DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1

          # Zen fails when it raises the open file limit past the hard limit.
          ulimit -n "$(ulimit -Hn)"
        '';

        runScript = "bash";
      };
    in
    {
      packages.${system} = {
        default = sfEnv;
        inherit engine msvc wwise;
        wwise-cli = wwiseCli;
      };

      devShells.${system} = {
        bootstrap = pkgs.mkShell {
          packages = with pkgs; [
            gh git gnumake coreutils nix zstd gnutar python3 msitools
          ];
        };

        # Standalone asset authoring without the vendor toolchain.
        assets = pkgs.mkShellNoCC {
          packages = [ pkgs.blender pkgs.ffmpeg ];
        };

        default = pkgs.mkShell {
          packages = [ sfEnv pkgs.gh pkgs.git pkgs.gnumake pkgs.nixfmt ];
          shellHook = ''
            export SF_ROOT="''${SF_ROOT:-''${XDG_DATA_HOME:-$HOME/.local/share}/sf}"
            export UE_ROOT="${engine}"
            export SML_DIR="$SF_ROOT/s"
            export UE_WINE_MSVC="${msvc}"
            export WINEPREFIX="$SF_ROOT/wine"
            export MOD_REPO="$PWD"
            export PATH="${wwiseCli}/bin:$PATH"
            export WWISE_ROOT="${wwise}"
          '';
        };
      };

      apps.${system}.default = {
        type = "app";
        program = "${sfEnv}/bin/sf-env";
      };
    };
}
