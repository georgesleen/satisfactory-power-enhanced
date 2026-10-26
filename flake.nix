{
  description = "EnhancedPower: core simulation, asset tools, and the Satisfactory modding toolchain";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };
      inherit (pkgs) lib;

      engine = import ./nix/engine.nix { inherit pkgs; };
      msvc = import ./nix/msvc.nix { inherit pkgs; };
      wwiseCli = import ./nix/wwise-cli.nix { inherit pkgs; };
      serverTools = import ./nix/server.nix { inherit pkgs; };

      uiSource = lib.fileset.toSource {
        root = ./.;
        fileset = lib.fileset.unions [
          ./Makefile
          ./assets/ui
          ./Source/EnhancedPowerCore
          ./tools/balance/tuning.json
        ];
      };
      uiPackage = pkgs.stdenvNoCC.mkDerivation {
        pname = "enhanced-power-ui";
        version = "0";
        src = uiSource;
        nativeBuildInputs = [
          pkgs.emscripten
          pkgs.gnumake
          pkgs.python3
        ];
        dontConfigure = true;
        buildPhase = ''
          runHook preBuild
          export EM_CACHE="$TMPDIR/emscripten-cache"
          cp -r ${pkgs.emscripten}/share/emscripten/cache "$EM_CACHE"
          chmod -R u+w "$EM_CACHE"
          make ui
          runHook postBuild
        '';
        installPhase = ''
          runHook preInstall
          mkdir -p "$out/share/enhanced-power-ui"
          cp -r build/ui/. "$out/share/enhanced-power-ui/"
          runHook postInstall
        '';
      };
      uiPreview = pkgs.writeShellApplication {
        name = "enhanced-power-ui";
        runtimeInputs = [ pkgs.python3 ];
        text = ''
          exec python3 -B ${./assets/ui/wasm/preview.py} ${uiPackage}/share/enhanced-power-ui "$@"
        '';
      };

      # The licensed Wwise payload exists only after a local import records its hash.
      wwiseLocked = builtins.pathExists ./nix/wwise-source.json;
      wwise = import ./nix/wwise.nix { inherit pkgs; };
      wwiseMissingMessage = ''
        Wwise is not locked: nix/wwise-source.json is missing, so WWISE_ROOT is unset.
        Run make bootstrap-wwise interactively, then make import-wwise.
      '';

      # Host toolchain for the core library, its tests, and the balance tool.
      coreInputs = [
        pkgs.doctest
        pkgs.nlohmann_json
      ];
      coreNativeInputs = [
        pkgs.cmake
        pkgs.ninja
        pkgs.python3
      ];

      # Formatter and linter inputs shared by the default shell and the formatting check.
      formatInputs = [
        pkgs.clang-tools
        pkgs.nixfmt
        pkgs.shellcheck
      ];

      coreSource = lib.fileset.toSource {
        root = ./.;
        fileset = lib.fileset.unions [
          ./CMakeLists.txt
          ./Source/EnhancedPowerCore
          ./Tests/Core
          ./Tests/Assets
          ./assets/common/unreal_import_smoke.py
          (lib.fileset.maybeMissing ./tools/balance)
        ];
      };

      # Builds the core with the given standard environment and runs its tests.
      coreCheck =
        name: stdenv:
        stdenv.mkDerivation {
          pname = "enhanced-power-${name}";
          version = "0";
          src = coreSource;
          preBuild = ''
            export NIX_BUILD_CORES=4
          '';
          nativeBuildInputs = coreNativeInputs;
          buildInputs = coreInputs;
          doCheck = true;
          checkPhase = ''
            runHook preCheck
            ctest --output-on-failure
            runHook postCheck
          '';
          installPhase = ''
            runHook preInstall
            install -Dm755 enhanced_power_core_tests "$out/bin/enhanced_power_core_tests"
            runHook postInstall
          '';
        };

      formatSource = lib.fileset.toSource {
        root = ./.;
        fileset = lib.fileset.unions [
          ./.clang-format
          ./flake.nix
          ./nix
          ./hooks
          (lib.fileset.maybeMissing ./Source)
          (lib.fileset.maybeMissing ./Tests)
          (lib.fileset.maybeMissing ./tools)
        ];
      };

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
        inherit engine msvc;
        wwise-cli = wwiseCli;
        server = serverTools.server;
        server-run = serverTools.run;
        server-smoke = serverTools.smoke;
        sml-server = serverTools.sml;
        ui = uiPackage;
        ui-preview = uiPreview;
      }
      // lib.optionalAttrs wwiseLocked { inherit wwise; };

      checks.${system} = {
        core-gcc = coreCheck "core-gcc" pkgs.stdenv;
        core-clang = coreCheck "core-clang" pkgs.clangStdenv;
        formatting = pkgs.runCommand "enhanced-power-formatting" { nativeBuildInputs = formatInputs; } ''
          cd ${formatSource}
          for directory in Source Tests tools; do
            if [ -d "$directory" ]; then
              find "$directory" -type f \( -name '*.h' -o -name '*.cpp' \) -print0 \
                | xargs -0 --no-run-if-empty clang-format --dry-run --Werror
            fi
          done
          find . -name '*.nix' -print0 | xargs -0 nixfmt --check
          shellcheck nix/*.sh hooks/*
          touch "$out"
        '';
      };

      devShells.${system} = {
        # Light shell: core build, tests, formatters, and the balance tool.
        default = pkgs.mkShell {
          packages =
            coreInputs
            ++ coreNativeInputs
            ++ formatInputs
            ++ [
              pkgs.gnumake
              pkgs.git
            ];
        };

        # Browser prototype with the engine-free C++ core compiled to WASM.
        ui = pkgs.mkShellNoCC {
          packages = [
            pkgs.emscripten
            pkgs.gnumake
            pkgs.python3
          ];
          shellHook = ''
            export EM_CACHE="$PWD/build/emscripten-cache"
            if [ ! -d "$EM_CACHE" ]; then
              mkdir -p "$(dirname "$EM_CACHE")"
              cp -r ${pkgs.emscripten}/share/emscripten/cache "$EM_CACHE"
              chmod -R u+w "$EM_CACHE"
            fi
          '';
        };

        # Vendor acquisition tools; needs no licensed payload.
        bootstrap = pkgs.mkShell {
          packages = with pkgs; [
            gh
            git
            gnumake
            coreutils
            nix
            zstd
            gnutar
            python3
            msitools
            steamcmd
          ];
        };

        # Standalone asset authoring without the vendor toolchain.
        assets = pkgs.mkShellNoCC {
          packages = [
            pkgs.blender
            pkgs.ffmpeg
          ];
        };

        # Licensed engine, MSVC, and Wwise toolchain around the FHS runtime.
        mod = pkgs.mkShell {
          packages = [
            sfEnv
            pkgs.gh
            pkgs.git
            pkgs.gnumake
            pkgs.nixfmt
          ];
          shellHook = ''
            export SF_ROOT="''${SF_ROOT:-''${XDG_DATA_HOME:-$HOME/.local/share}/sf}"
            export UE_ROOT="${engine}"
            export SML_DIR="$SF_ROOT/s"
            export UE_WINE_MSVC="${msvc}"
            export WINEPREFIX="$SF_ROOT/wine"
            export MOD_REPO="$PWD"
            export PATH="${wwiseCli}/bin:$PATH"
          ''
          + (
            if wwiseLocked then
              ''
                export WWISE_ROOT="${wwise}"
              ''
            else
              ''
                printf '%s' ${lib.escapeShellArg wwiseMissingMessage} >&2
              ''
          );
        };
      };

      apps.${system} = {
        default = {
          type = "app";
          program = "${sfEnv}/bin/sf-env";
          meta.description = "Satisfactory modding FHS runtime";
        };
        server-smoke = {
          type = "app";
          program = "${serverTools.smoke}/bin/sf-server-smoke";
          meta.description = "Dedicated-server integration smoke check";
        };
        ui = {
          type = "app";
          program = "${uiPreview}/bin/enhanced-power-ui";
          meta.description = "Loopback browser preview with the C++ core";
        };
      };
    };
}
