BUILD_DIR := build
MSVC_BUILD_DIR := $(BUILD_DIR)/msvc
JOBS := 4
CORE_SOURCES := $(filter-out %Module.cpp,$(wildcard Source/EnhancedPowerCore/Private/*.cpp))
FORMAT_SOURCES = $(shell find Source Tests tools -type f \( -name '*.h' -o -name '*.cpp' \) 2>/dev/null)
NIX_SOURCES = $(shell find . -name '*.nix' -not -path './.git/*' -not -path './.direnv/*' -not -path './$(BUILD_DIR)/*')
# Mirrors the Unreal Build Tool defaults for MSVC: C++20, conformance mode, exceptions disabled.
MSVC_FLAGS := /nologo /std:c++20 /permissive- /Zc:__cplusplus /Zc:preprocessor /W4 /WX /D_HAS_EXCEPTIONS=0 /c

.PHONY: help configure build test check fmt fmt-check balance core-msvc bootstrap-starter bootstrap-engine bootstrap-msvc bootstrap-wwise import-wwise toolchain shell wine-prefix smoke editor project-files compile-db integrate-wwise
.PHONY: bootstrap-server server-smoke mod-build mod-package mod-deploy
.PHONY: ui ui-preview

help:
	@printf '%s\n' \
	  'test              Build the core and run its host tests' \
	  'check             Run nix flake check: formatting, GCC and Clang core builds, tests' \
	  'fmt               Format C++ and Nix sources in place' \
	  'fmt-check         Check C++ and Nix formatting and lint shell scripts' \
	  'balance           Build ep-balance and print the balance report' \
	  'ui                Build C++ WASM and stage the browser UI (use .#ui shell)' \
	  'ui-preview        Build and serve the UI on 127.0.0.1:8080' \
	  'core-msvc         Compile the core with the packaged MSVC under Wine' \
	  'bootstrap-server  Download and import the dedicated server anonymously' \
	  'server-smoke      Run the dedicated-server integration smoke check' \
	  'mod-build         Build upstream FactoryEditor with the mod' \
	  'mod-package       Package Windows client and Linux server plugin' \
	  'mod-deploy        Package and deploy the Linux server plugin' \
	  'bootstrap-starter Clone pinned official starter and link this mod' \
	  'bootstrap-engine  Download/import authorized CSS engine parts' \
	  'bootstrap-msvc    Download/import approved MSVC and SDK sources' \
	  'bootstrap-wwise   Download Wwise with local account prompts' \
	  'import-wwise      Import licensed Wwise payload and record its hash' \
	  'toolchain         Realize immutable vendor outputs' \
	  'shell             Enter FHS runtime' \
	  'smoke             Inspect tool versions without compiling a game target' \
	  'integrate-wwise   Copy writable plugin source, link immutable SDK data' \
	  'editor            Build upstream FactoryEditor Linux Development' \
	  'project-files     Generate upstream project files' \
	  'compile-db        Generate upstream clang compilation database'

configure:
	cmake -S . -B $(BUILD_DIR) -G Ninja

build: configure
	cmake --build $(BUILD_DIR) -j$(JOBS)

test: build
	ctest --test-dir $(BUILD_DIR) --output-on-failure

check:
	nix flake check -L

fmt:
	$(if $(FORMAT_SOURCES),clang-format -i $(FORMAT_SOURCES))
	nixfmt $(NIX_SOURCES)

fmt-check:
	$(if $(FORMAT_SOURCES),clang-format --dry-run --Werror $(FORMAT_SOURCES))
	nixfmt --check $(NIX_SOURCES)
	shellcheck nix/*.sh hooks/*

balance: configure
	cmake --build $(BUILD_DIR) --target ep-balance -j$(JOBS)
	./$(BUILD_DIR)/tools/balance/ep-balance --tuning tools/balance/tuning.json tools/balance/scenarios

core-msvc: wine-prefix
	nix run . -- -c 'set -e; mkdir -p $(MSVC_BUILD_DIR); "$$UE_WINE_MSVC/bin/x64/cl" $(MSVC_FLAGS) /ISource/EnhancedPowerCore/Public /Fo$(MSVC_BUILD_DIR)/ $(CORE_SOURCES); wineserver -w'

bootstrap-starter:
	nix develop .\#bootstrap -c bash nix/bootstrap-starter.sh

bootstrap-engine:
	nix develop .\#bootstrap -c bash nix/bootstrap-engine.sh

bootstrap-msvc:
	nix develop .\#bootstrap -c bash nix/bootstrap-msvc.sh

bootstrap-wwise:
	nix develop .\#bootstrap -c bash nix/bootstrap-wwise.sh

import-wwise:
	nix develop .\#bootstrap -c bash nix/import-wwise.sh

toolchain:
	mkdir -p .direnv
	nix build .\#default --out-link .direnv/toolchain-runtime
	$(if $(wildcard nix/wwise-source.json),nix build .\#wwise --out-link .direnv/toolchain-wwise)

shell: toolchain
	nix run .

wine-prefix: toolchain
	nix run . -- -c 'env -u DISPLAY -u WAYLAND_DISPLAY WINEDLLOVERRIDES="mscoree,mshtml=" wineboot -u && wineserver -w'

smoke: wine-prefix
	nix run . -- -c 'set -e; wine --version; wwise-cli --help; "$$UE_ROOT/Engine/Binaries/ThirdParty/DotNet/8.0.300/linux-x64/dotnet" --info; "$$UE_WINE_MSVC/bin/x64/cl" /?; wineserver -w; test -f "$$UE_ROOT/Engine/Build/InstalledBuild.txt"; test -L "$$SML_DIR/Mods/EnhancedPower"'

editor: toolchain
	nix run . -- -c '"$$UE_ROOT/Engine/Build/BatchFiles/Linux/Build.sh" FactoryEditor Linux Development -project="$$SML_DIR/FactoryGame.uproject" -MaxParallelActions=4'

project-files: toolchain
	nix run . -- -c '"$$UE_ROOT/Engine/Build/BatchFiles/Linux/Build.sh" -projectfiles -project="$$SML_DIR/FactoryGame.uproject" -game -Makefile'

compile-db: toolchain
	nix run . -- -c '"$$UE_ROOT/Engine/Build/BatchFiles/RunUBT.sh" FactoryEditor Linux Development "$$SML_DIR/FactoryGame.uproject" -Compiler=Clang -mode=GenerateClangDataBase -OutputDir="$$SML_DIR"'

integrate-wwise:
	nix develop .\#mod -c bash nix/integrate-wwise.sh

bootstrap-server:
	nix develop .\#bootstrap -c bash nix/bootstrap-server.sh

server-smoke:
	nix run .\#server-smoke

mod-build: editor

mod-package: toolchain
	nix run . -- -c '"$$UE_ROOT/Engine/Build/BatchFiles/RunUAT.sh" -ScriptsForProject="$$SML_DIR/FactoryGame.uproject" PackagePlugin -Project="$$SML_DIR/FactoryGame.uproject" -dlcname=EnhancedPower -merge -build -server -clientconfig=Shipping -serverconfig=Shipping -platform=Win64 -serverplatform=Linux -nocompileeditor -installed -UbtArgs=-MaxParallelActions=4'

mod-deploy: toolchain
	nix run . -- -c '"$$UE_ROOT/Engine/Build/BatchFiles/RunUAT.sh" -ScriptsForProject="$$SML_DIR/FactoryGame.uproject" PackagePlugin -Project="$$SML_DIR/FactoryGame.uproject" -dlcname=EnhancedPower -merge -build -server -noclient -serverconfig=Shipping -serverplatform=Linux -nocompileeditor -installed -UbtArgs=-MaxParallelActions=4 -CopyToGameDirectory_LinuxServer="$$SF_ROOT/server-instance"'

# Blender game asset delivery
ASSET ?= all
.PHONY: asset-export
asset-export:
	@set -eu; \
	if [ "$(ASSET)" = all ]; then \
	  assets="transformer capacitor-bank mv-pole hv-tower cryo-station"; \
	else assets="$(ASSET)"; fi; \
	for asset in $$assets; do \
	  nix develop .#assets --command flock /tmp/enhancedpower-blender.lock \
	    blender --background --factory-startup --threads 3 --python-exit-code 1 \
	    --python assets/common/export_asset.py -- "assets/$$asset"; \
	done

# Engine-free browser UI
UI_DIR := $(BUILD_DIR)/ui
UI_PORT ?= 8080
ui:
	$(MAKE) -f assets/ui/wasm/Makefile -j4 UI_DIR=$(UI_DIR) UI_OBJECT_DIR=$(BUILD_DIR)/ui-wasm
	python3 -B assets/ui/wasm/stage.py $(UI_DIR)

ui-preview: ui
	python3 -B assets/ui/wasm/preview.py $(UI_DIR) --port $(UI_PORT)
