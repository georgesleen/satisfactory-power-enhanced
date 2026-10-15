.PHONY: help bootstrap-starter bootstrap-engine bootstrap-msvc bootstrap-wwise import-wwise toolchain shell wine-prefix smoke editor project-files compile-db integrate-wwise

help:
	@printf '%s\n' 'bootstrap-starter Clone pinned official starter and link this mod' 'bootstrap-engine  Download/import authorized CSS engine parts' 'bootstrap-msvc    Download/import approved MSVC and SDK sources' 'bootstrap-wwise   Download Wwise with local account prompts' 'import-wwise      Import licensed Wwise payload and record its hash' 'toolchain         Realize immutable vendor outputs' 'shell             Enter FHS runtime' 'smoke             Inspect tool versions without compiling a game target' 'integrate-wwise   Copy writable plugin source, link immutable SDK data' 'editor            Build upstream FactoryEditor Linux Development' 'project-files     Generate upstream project files' 'compile-db        Generate upstream clang compilation database'

bootstrap-starter:
	nix develop path:.\#bootstrap -c bash nix/bootstrap-starter.sh

bootstrap-engine:
	nix develop path:.\#bootstrap -c bash nix/bootstrap-engine.sh

bootstrap-msvc:
	nix develop path:.\#bootstrap -c bash nix/bootstrap-msvc.sh

bootstrap-wwise:
	nix develop path:.\#bootstrap -c bash nix/bootstrap-wwise.sh

import-wwise:
	nix develop path:.\#bootstrap -c bash nix/import-wwise.sh

toolchain:
	nix build path:.\#engine path:.\#msvc path:.\#wwise --no-link

shell:
	nix run path:.

wine-prefix:
	nix run path:. -- -c 'env -u DISPLAY -u WAYLAND_DISPLAY WINEDLLOVERRIDES="mscoree,mshtml=" wineboot -u && wineserver -w'

smoke: wine-prefix
	nix run path:. -- -c 'set -e; wine --version; wwise-cli --help; "$$UE_ROOT/Engine/Binaries/ThirdParty/DotNet/8.0.300/linux-x64/dotnet" --info; "$$UE_WINE_MSVC/bin/x64/cl" /?; wineserver -w; test -f "$$UE_ROOT/Engine/Build/InstalledBuild.txt"; test -L "$$SML_DIR/Mods/EnhancedPower"'

editor:
	nix run path:. -- -c '"$$UE_ROOT/Engine/Build/BatchFiles/Linux/Build.sh" FactoryEditor Linux Development -project="$$SML_DIR/FactoryGame.uproject"'

project-files:
	nix run path:. -- -c '"$$UE_ROOT/Engine/Build/BatchFiles/Linux/Build.sh" -projectfiles -project="$$SML_DIR/FactoryGame.uproject" -game -Makefile'

compile-db:
	nix run path:. -- -c '"$$UE_ROOT/Engine/Build/BatchFiles/RunUBT.sh" FactoryEditor Linux Development "$$SML_DIR/FactoryGame.uproject" -Compiler=Clang -mode=GenerateClangDataBase -OutputDir="$$SML_DIR"'

integrate-wwise:
	nix develop path:. -c bash nix/integrate-wwise.sh
