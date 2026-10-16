# EnhancedPower

Satisfactory mod (mod reference `EnhancedPower`). Read `README.md`,
`docs/design.md`, and `docs/development.md` first.

## Layout

- `docs/`: design, roadmap, core model contract, player guide, toolchain.
- `Source/EnhancedPowerCore/`: engine-free simulation core, host-tested.
- `Tests/Core/`: host tests for the core, written from `docs/core-model.md`.
- `assets/`: Blender generators, renders, and the browser UI prototype.
- `nix/`: vendor toolchain packages (engine, MSVC, Wwise) and bootstrap scripts.

## Rules

- Rules live on wires and grid buildings, never on machines.
- The core never includes Unreal headers. Unreal glue lives in
  `Source/EnhancedPower/` and calls the core.
- Vendor payloads enter the Nix store only through `requireFile`; credentials
  never enter Nix expressions, the store, or logs.

## Workarounds

- `nix/msvc.nix:45`: upstream `msvcenv.sh` overwrites `WINEDLLOVERRIDES`, which
  drops `mscoree,mshtml=` and makes Wine offer to install Wine Mono; the patch
  keeps inherited overrides.
- `nix/engine.nix:30`: `SetupDotnet.sh` runs `chmod` on the bundled dotnet at
  every start, which fails on the read-only store; the package sets the mode at
  build time and removes the runtime `chmod`.
- `nix/bootstrap-engine.sh:16`: `gh` downloads of the multi-GB engine parts fail
  with HTTP/2 `PROTOCOL_ERROR`; `GODEBUG=http2client=0` forces HTTP/1.1.
