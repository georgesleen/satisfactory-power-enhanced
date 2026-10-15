# Development

## Transformer experiment: implementation blocked

There is no transformer actor, plugin module, spawn command, or buildable target
in this repository. Runtime verification is pending. A producer driven by the
previous frame's `HasPower()` cannot satisfy the required no-energy-creation
contract, so the experiment is not represented by a nonconserving prototype.
No editor or binary asset is required to investigate the C++ API.

## Available source evidence

The official SML starter project inspected is
[`satisfactorymodding/SatisfactoryModLoader` at `8eebc9e6`](https://github.com/satisfactorymodding/SatisfactoryModLoader/tree/8eebc9e6).
Paths below are relative to that project, not this repository.

- `Mods/Alpakit/Templates/CPPAndBlueprintBlank/Source/PLUGIN_NAME/` is the
  upstream C++ plugin template, using C++20 and the FactoryGame/SML modules.
- `Source/FactoryGame/Public/FGPowerConnectionComponent.h` exposes
  `SetPowerInfo()`. Each connection must have its own info; sharing one can
  race when assigning its circuit ID.
- `Source/FactoryGame/Public/FGCircuitConnectionComponent.h` exposes
  `AddHiddenConnection()` and `RemoveHiddenConnection()`, which connect and
  disconnect both ends and their circuits. One endpoint must be hidden.
  There must be no such connection between transformer primary and secondary.
- `Source/FactoryGame/Public/FGCircuitSubsystem.h` exposes connection/removal
  APIs and circuit/group rebuild delegates. Circuit pointers can be invalidated
  by a connection change and must not be cached across rebuilds.
- `Source/FactoryGame/Public/FGPowerInfoComponent.h` exposes asynchronous
  consumption and production requests, actual consumption, regulated production,
  and the protected virtual `UpdateSimulationData()` callback. It explicitly
  permits dynamic demand factors above one. Maximum target consumption is
  informational, not a power reservation.
- `Source/FactoryGame/Public/FGPowerCircuit.h` states that circuit groups exist
  only on the server. The group balance and battery tick are private. It does
  not specify the ordering of separate group solves or a cross-group transfer
  transaction.
- Power infos implement `IFGSaveInterface`; target consumption and dynamic
  capacity have `SaveGame` metadata. That does not establish how an independently
  spawned actor and its connections should be restored safely before the next
  solve. No saved nonzero offer may be trusted as evidence of primary supply.

The corresponding `Private/FGPowerInfoComponent.cpp` and
`Private/FGPowerCircuit.cpp` identify themselves as automatically generated
header implementations and contain empty methods/default returns. They are not
the shipped game's solver. The CSS Unreal Engine distribution supplies engine
source, not the missing FactoryGame power implementation.

## Exact missing contract

Implementation requires the real bodies, or an authoritative equivalent
contract, for:

1. `AFGCircuitSubsystem::Tick()`, `UFGPowerCircuitGroup::PreTickCircuitGroup()`
   and `TickPowerCircuitGroup()`: when requests are sampled, how separate groups
   are ordered, and when output is committed relative to primary consumption.
2. `UFGPowerInfoComponent::UpdateSimulationData()` and
   `GetRegulatedDynamicProduction()`: whether the reported production is the
   delivered amount or requested amount during overload, whether it is clamped
   to capacity, and whether a callback can change another group's still-pending
   solve without changing an already-committed result.
3. Fuse, disconnect, and battery behavior during that transaction: output must
   not be committed if the corresponding primary debit is rejected. A stale
   `HasPower()` flag is insufficient.
4. Zero-demand startup: `HasPower()` on the info describes fulfillment of its
   request, whereas the connection's `HasPower()` describes circuit production.
   Neither header specifies a funded bootstrap transaction. An arbitrary probe
   load would change idle consumption, and a free initial offer would create
   energy. Startup must be established without either shortcut.

Tick prerequisites alone cannot resolve independent circuit-group accounting.
Reading secondary output and requesting the matching primary consumption next
frame does not prove conservation: the later request can fail. A stored-energy
model would need explicit accounting and would change the immediate-unpowered
output requirement; it is not silently substituted for a transformer.

## Runtime acceptance checks

These are requirements, not observed results. There are no truthful
`EnhancedPower` spawn/wire/use commands or build command until the contract above
is resolved and an actual target exists. Do not use an invented `summon` class
name. The eventual command must be registered through upstream engine/SML
facilities and operate on the authority, without an editor-created asset.

Use a disposable save with one source island and one load island:

- Verify two distinct connection/info pairs, circuit IDs, and group IDs; neither
  hidden connections nor active circuit bridges may join the two islands.
- Start with an unloaded secondary and a powered primary, then add secondary
  load. Startup must succeed without free output or a permanent probe load.
- For a declared rating R MW, serve loads below R, exactly R, and above R.
  Delivered secondary power must never exceed R; above-R demand must trigger
  vanilla secondary overload behavior, not increase the offer.
- Measure primary actual consumption and secondary actual delivered production
  per solver interval, not just graph averages. For lossless operation their
  energies must match; an idle secondary must not impose the rating as primary
  consumption.
- Remove primary generation, disconnect the input, and trip the primary fuse
  while the secondary is loaded. There must be no unfunded secondary delivery.
- Trip the secondary while keeping the primary island below its capacity. The
  primary fuse must remain intact. Test both actor creation orders and variable
  frame times to expose order-dependent behavior.
- Supply the secondary locally and leave the primary dead. No reverse transfer
  or self-starting energy loop is allowed.
- Repeat on a host and client; only the server may update power requests.
  If persistence is supported, repeat across save/load with a dead primary.

Builds, tests, packaging, and in-game checks have not been run for this experiment.
Vanilla railway regeneration must be preserved, not implemented a second time:
`FGLocomotive::SetPowerRegeneration()` and the locomotive movement component's
regenerative power factor/curve already expose it.

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
`nix develop path:.#bootstrap`. The default devshell requires all licensed
sources. Missing Wwise input produces an actionable error until an
Audiokinetic account is used locally with `make bootstrap-wwise`. This command
prompts without echoing the password and does not persist it. Review applicable
vendor terms before downloading; bootstrap is not permission to accept
unrelated licenses.

The MSVC bootstrap uses the Microsoft license acceptance explicitly approved
for this setup. It does not authorize acceptance of unrelated licenses.
`nix/wwise-source.json` records the authenticated payload's content hash after
import and is part of the reproducible source lock, not a credential file.

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
they are not replacement build systems. No transformer target exists yet.

`nix run path:.` or `make shell` enters the FHS runtime. The outer direnv
devshell supplies its launcher and command tools; Unreal and Wine commands
run inside FHS. Runtime home, config, cache, temporary files, and Wine prefix
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
nix path-info -Sh path:.#engine path:.#msvc path:.#wwise
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
