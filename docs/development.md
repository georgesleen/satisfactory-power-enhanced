# Development

## Source layout

| Path | Contents | Verification |
| --- | --- | --- |
| `Source/EnhancedPowerCore/` | Engine-free simulation core from [Core model](core-model.md) | Host builds and tests |
| `Tests/Core/` | doctest host tests for the core | `make test`, `make check` |
| `tools/balance/` | `ep-balance` CLI, scenarios, tuning, and report gates; see [Balance](balance.md) | `make balance`, `make test` |
| `EnhancedPower.uplugin`, `Source/EnhancedPower/` | SML plugin with a server-only transformer probe | Not compiled |
| `assets/` | Blender models and the browser UI study; see [Asset pipeline](asset-pipeline.md) | Assets shell |

The core is plain C++20 with no Unreal headers. Its Unreal module entry point,
`EnhancedPowerCoreModule.cpp`, is excluded from the host build. The runtime
module calls the core. No playable building, wire tier, or grid rule exists in
the game yet.

## Shells

| Shell | Command | Purpose |
| --- | --- | --- |
| Default | `nix develop` | Core code, tests, formatting, balance |
| Assets | `nix develop .#assets` | Blender and ffmpeg |
| Bootstrap | `nix develop .#bootstrap` | Authorized vendor and server acquisition |
| Mod | `nix develop .#mod` | Licensed engine, MSVC, and Wwise |

The default shell provides GCC, CMake, Ninja, doctest, nlohmann_json,
clang-tools, Python, nixfmt, and shellcheck. It needs no licensed vendor payload
or `nix/wwise-source.json`. The assets shell needs no vendor payload either.
Enter the default shell with `nix develop` or `direnv allow`.

Use `path:.` only when intentionally including untracked Nix inputs.
Git-backed references omit untracked files and avoid copying ignored build and
animation-frame trees. Blender reads its scripts from the working directory.

## Host development

```sh
nix develop
make test
make balance
make fmt
make fmt-check
make check
```

`make test` configures the root CMake project, builds with at most four jobs,
and runs CTest: the core tests, the balance scenarios, and the balance report
and extraction tests. CMake writes the compile command database in `build`.
`make balance` builds `ep-balance` and prints the report for
`tools/balance/scenarios`.

`make check` runs `nix flake check -L`. It checks formatting and shell lint,
builds the core and balance tool with GCC and Clang, and runs CTest for each
compiler. It never realizes licensed vendor payloads or the dedicated server.
CI runs the same command on pushes and pull requests. `.envrc` installs the
tracked `hooks/pre-push` automatically, and the hook runs this gate.

`make fmt` formats C++ and Nix source. `make fmt-check` checks C++ under
`Source`, `Tests`, and `tools`, checks Nix formatting, and runs shellcheck on
`nix/*.sh` and `hooks/*`. `.clang-format` uses tab indentation, Allman braces,
and a 110-column limit.

## Transformer probe

The `EnhancedPower` runtime module is a transient server diagnostic, not a
playable transformer. It spawns a source actor, a load actor, and a transformer
actor in C++, with no assets, recipes, or save support. The transformer joins
two separate circuits through the core `PlanLink`, `SettleLink`, and
`StepThermal` functions. The probe source is complete, but it is not compiled or
run. The Unreal build waits on Wwise provisioning; see
[Toolchain setup](#toolchain-setup).

The plugin targets the starter headers at SML commit `8eebc9e6` (game CL
`513885`) and declares SML `>=3.12.0 <3.13.0`. `RequiredOnRemote` is false, so
clients do not need the plugin. The pinned dedicated server with published SML
`3.12.0` reports CL `513885`, which matches the starter headers.

Run these commands through the server console or the HTTPS API `RunCommand`,
in a disposable world with auto-pause disabled. Editor and client worlds reject
them. The probe actors are transient; never use a normal player save.

| Command | Arguments | Effect |
| --- | --- | --- |
| `EnhancedPower.Probe.Start` | `[ratingMW]`, default `50` | Creates one unloaded fixture. Source production is twice the rating. |
| `EnhancedPower.Probe.Set` | `sourceMW loadMW peakMW periodSeconds` | Sets production and demand. A nonzero period alternates `loadMW` and `peakMW` each half period. |
| `EnhancedPower.Probe.Report` | None | Writes cumulative energy accounting to `LogEnhancedPower`. |
| `EnhancedPower.Probe.Stop` | None | Reports, removes hidden connections, and destroys the fixture. |

SML hooks run before and after `AFGCircuitSubsystem::Tick(float)`. The before
hook applies the core plan as primary consumption and secondary dynamic
capacity. The after hook reads actual consumption and regulated production and
settles the core accounting. Each tick logs a `LogEnhancedPower: Probe tick=...`
line with the plan, the engine readbacks, fuse flags, heat, escrow, settlement
excess, and power-info callback counts. `conserved=1` in the report means the
accounting residual is within `1e-6` MJ and both excess counters are zero. It
does not prove that the callbacks fall inside the hook bracket.

## Open engine questions

Host tests establish the core accounting: a link never offers unfunded energy,
and settlement reports any engine excess explicitly. The coupling to the
game's power solver is unverified. The starter project's
`FGPowerCircuit.cpp` and `FGPowerInfoComponent.cpp` are generated stubs, so the
headers alone cannot answer these questions. The probe answers them on a real
server:

| Question | Probe evidence |
| --- | --- |
| Do the two circuits stay separate? | Distinct circuit and group IDs; no hidden connection joins primary and secondary. |
| Does the engine honor the secondary capacity? | `delivered <= planOffer` and `overDelivery=0` on every tick, including overload. |
| Does primary consumption follow demand, or lag one tick? | `preSolveRequest`, `planRequest`, `request`, and `consumed` under a pulsed load. |
| Is a secondary trip local? | Secondary fuse trips while the primary fuse holds. |
| Do upstream outages and fuses propagate? | Input stops, escrow drains, and the offer reaches zero. |
| Do callbacks fall inside the tick bracket? | One callback per info per tick and no callbacks outside the bracket. |

The upstream sources are relative to
[`satisfactorymodding/SatisfactoryModLoader` at `8eebc9e6`](https://github.com/satisfactorymodding/SatisfactoryModLoader/tree/8eebc9e6):

- `Source/FactoryGame/Public/FGPowerConnectionComponent.h`: `SetPowerInfo()`;
  each connection needs its own info.
- `Source/FactoryGame/Public/FGCircuitConnectionComponent.h`:
  `AddHiddenConnection()` and `RemoveHiddenConnection()`. No such connection may
  join transformer primary and secondary.
- `Source/FactoryGame/Public/FGCircuitSubsystem.h`: the virtual subsystem
  `Tick(float)` and rebuild delegates. Circuit pointers do not survive a rebuild.
- `Source/FactoryGame/Public/FGPowerInfoComponent.h`: asynchronous requests,
  actual consumption, regulated production, and the protected virtual
  `UpdateSimulationData()` callback. Demand factors above one are permitted.
- `Source/FactoryGame/Public/FGPowerCircuit.h`: circuit groups exist only on the
  server. The header does not specify group solve order.

Persistence, multiplayer clients, and railway regeneration are outside the
probe. Vanilla railway regeneration stays vanilla:
`AFGLocomotive::SetPowerRegeneration()` and the locomotive movement component's
regenerative factor already expose it.

## Toolchain setup

The root flake pins an x86_64-linux NixOS FHS runtime and licensed vendor
derivations. The CSS engine is `5.6.1-css-83`, MSVC is `17.8.23` from the
upstream `release.ltsc.17.8` selection with SDK `10.0.22621`, and Wwise uses
SDK `2025.1.6.9117` with integration `2025.1.6.4248`. The public Wwise CLI
is `0.2.4`; Wine is `11.0`. The engine, MSVC, and Wwise outputs are unfree local
packages and must not be published to a public binary cache.

Authenticated acquisition happens outside Nix builders. Bootstrap commands use
official `gh`, `msvc-wine/vsdownload.py`, and `wwise-cli`; verified payloads
enter the store through `requireFile`. Neither credentials nor credentialed
download URLs belong in Nix expressions, lock files, or build logs.

```sh
make bootstrap-starter
make bootstrap-engine
make bootstrap-msvc
make bootstrap-wwise
make import-wwise
make toolchain
direnv allow
make integrate-wwise
make wine-prefix
make smoke
```

The bootstrap shell does not require vendor payloads and is available as
`nix develop .#bootstrap`. The vendor shell is `nix develop .#mod`.
It prints an actionable message and leaves `WWISE_ROOT` unset when
`nix/wwise-source.json` is missing. The `wwise` package is exposed only after
this lock exists. Core checks and the default and assets shells do not import
the Wwise SDK. `make toolchain` realizes engine and MSVC, plus Wwise when locked.
Use `make bootstrap-wwise` with an Audiokinetic account, then `make import-wwise`.
Bootstrap prompts without echoing the password and does not persist it.
Review applicable vendor terms before downloading. Bootstrap is not permission
to accept unrelated licenses.

The Unreal build of the starter project needs the integrated Wwise plugin, so
`make mod-build` waits on an Audiokinetic account and the Wwise lock. Host
development, assets, the server bootstrap, and the server smoke do not need
Wwise.

The MSVC bootstrap uses the Microsoft license acceptance explicitly approved
for this setup. It does not authorize acceptance of unrelated licenses.
`nix/wwise-source.json` records the authenticated payload's content hash after
import and is part of the reproducible source lock, not a credential file.
`make import-wwise` stages it, so `use flake .` in direnv sees it; commit it.

`make wine-prefix` initializes the disposable Wine prefix with upstream's
`WINEDLLOVERRIDES=mscoree,mshtml=` and without a display. It does not download
Wine Mono or Gecko. MSVC's native compiler/helper path does not require them.
The packaged upstream wrapper preserves inherited DLL overrides while retaining
its required native vcruntime DLLs. Managed .NET tools have not been exercised;
do not accept an automatic installer prompt as a toolchain dependency.

The official starter checkout lives at
`${XDG_DATA_HOME:-$HOME/.local/share}/sf/s`, with
`Mods/EnhancedPower` linked to this repository. It remains writable for
upstream project files and generated build output. `make editor`,
`make project-files`, and `make compile-db` wrap upstream Unreal commands;
they are not replacement build systems. The linked plugin builds with
`FactoryEditor`.

`nix run .` or `make shell` enters the FHS runtime. The mod shell supplies
its launcher and vendor paths. Unreal and Wine commands run inside FHS.
`make core-msvc` compiles every core source with the packaged MSVC under Wine.
It uses C++20, `/W4 /WX`, conformance mode, and the Unreal exception-disabled
configuration. It creates object files under `build/msvc`; it does not link or
run the host tests. Runtime home, config, cache, temporary files, and Wine prefix
are isolated beneath `SF_ROOT`, which defaults to the `sf` directory above.
The immutable engine keeps its installed-build marker and precompiled
automation. Its bundled dotnet permissions are fixed during packaging rather
than mutated by `SetupDotnet.sh` at runtime. Installed UBT/UAT relocates rules
and logs to writable user/project paths. This is not a guarantee that every
editor feature avoids writing `Engine/Intermediate`; editor behavior must be
verified separately before claiming complete read-only compatibility.

Wwise integration copies writable plugin source/config into the starter
checkout because upstream WwisePatches modifies those files. Large `ThirdParty`
SDK data is linked to the immutable output. The integration command refuses
to overwrite an existing plugin directory.

## Mod packaging

After vendor import and Wwise integration:

```sh
make mod-build
make mod-deploy
```

`make mod-build` builds the upstream `FactoryEditor` target with the linked
plugin. `make mod-package` calls upstream `PackagePlugin` for the Windows client
and Linux dedicated server. `make mod-deploy` packages only the Linux server
plugin and copies it into `$SF_ROOT/server-instance`, the instance that
`packages.server-run` starts. It is a development deployment, not a release.
All three commands limit Unreal Build Tool to four actions and require the
licensed toolchain. A passing host check implies no build, package, or
deployment result.

## Dedicated server

The server bootstrap uses anonymous SteamCMD for app `1690800`:

```sh
make bootstrap-server
make server-smoke
```

Bootstrap records `nix/server-source.json` and imports its archive through
`requireFile`. The server package does not redistribute the Steam payload.
`packages.server` exposes the pinned server. `packages.sml-server` exposes the
published LinuxServer SML build. `packages.server-run` starts a disposable local
instance under `$SF_ROOT/server-instance` with SML and loopback-only networking.
`make server-smoke` starts that instance, disables auto-pause, creates a world
through the HTTPS API, checks that game time advances, saves through
`RunCommand`, checks the SML version in the log, and shuts the server down. It
does not need the EnhancedPower plugin. The server packages do not participate
in the core check gate.

The server is the runtime path for the probe: deploy the plugin with
`make mod-deploy`, start `packages.server-run`, and run the probe commands
through the console or `RunCommand`.

## Storage and reclamation

| Location | Contents |
| --- | --- |
| Nix store | Pinned runtime dependencies, imported licensed archives, immutable engine/MSVC/Wwise outputs |
| `$SF_ROOT/dl` | Original engine parts and licensed import archives |
| `$SF_ROOT/msvc-download` | Versioned Microsoft payload cache and imported archive originals |
| `$SF_ROOT/cache` | Explicit upstream download caches, including Wwise |
| `$SF_ROOT/bootstrap` | Temporary licensed acquisition/extraction workspaces |
| `$SF_ROOT/home`, `$SF_ROOT/config`, `$SF_ROOT/tmp`, `$SF_ROOT/wine` | Disposable runtime state and Wine prefix |
| `$SF_ROOT/s` | Writable official starter checkout, integrated plugins, build output |
| Repo `.direnv` | direnv environments and their Nix GC roots |
| Repo `Binaries`, `Intermediate`, `Saved`, `DerivedDataCache` | Ignored generated mod output |

Engine archive parts total 8,264,339,940 bytes before extraction. Importing
them temporarily keeps both the host originals and fixed-output store
sources, and packaging adds the unpacked output. MSVC and Wwise likewise
have temporary download/cache, archive, and unpacked copies. Budget peak
space rather than assuming zero duplication. `requireFile` sources can
remain reachable through derivations even after their original downloads
are removed.

Inspect storage without deleting anything:

```sh
du -h -d 2 "${SF_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/sf}"
nix path-info -Sh .#engine .#msvc .#wwise
nix-store --gc --print-roots
nix-store --gc --print-dead
```

After successful import and realization, the original files under
`$SF_ROOT/dl` and download-only bootstrap/cache directories can be removed
explicitly. Keep any user-created Wwise projects, saves, and changes to the
starter checkout. The Wine prefix and runtime cache are disposable; deleting
them costs initialization/download time. Leaving the devshell deletes nothing.

After those conditions are met, these commands remove only local acquisition
copies and disposable runtime state, not store packages or the starter project:

```sh
sf_root="${SF_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/sf}"
printf 'Review toolchain root before removing anything: %s\n' "$sf_root"
# Run only after confirming the printed path and successful store imports:
rm -rf -- "$sf_root/dl" "$sf_root/bootstrap" "$sf_root/cache" "$sf_root/tmp" \
  "$sf_root/msvc-download"
# Optional: discard the initialized Wine prefix and isolated runtime settings:
rm -rf -- "$sf_root/wine" "$sf_root/home" "$sf_root/config"
```

To retire the entire project toolchain, leave all shells, stop Unreal/Wine,
remove this checkout's `.direnv` and any `result` symlinks, and explicitly remove
the chosen `SF_ROOT` only after preserving wanted data. The default path is
`~/.local/share/sf`; confirm it before any recursive removal. Removing that
directory does not remove the immutable store packages.

`nix store gc --dry-run` previews reclaimable Nix paths;
`nix store gc` explicitly collects unreferenced paths across the user's shared
store, not just this project. Active shells, direnv roots, profiles, result
links, and other projects can retain dependencies. Remove only roots you
understand; do not delete store paths manually. GC is never run automatically
by this setup, and vendor output deletion is not implied by devshell exit.
