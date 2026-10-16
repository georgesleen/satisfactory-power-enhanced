# Enhanced Power

Mod reference: `EnhancedPower`.

A Satisfactory mod that makes the power grid a layout puzzle: voltage tiers on
wires, transformers, transmission loss, local overloads, and late-game
superconductors.

Status: the mechanics are planned gameplay, not a playable mod. The
engine-free simulation core and the balance tool build and pass host tests. A
server-only transformer probe is written against the SML headers but is not
compiled or run in the game. Blender models and a browser UI study run on their
own.

## Design rules

- Fun first, realism second.
- No busywork: rules apply to wires and grid buildings, never to individual
  machines.
- The vanilla power line is the LV tier. A factory floor plays like vanilla.

## Quick start

```sh
nix develop          # light shell: core, tests, formatters, balance
make test            # core and balance host tests
make balance         # balance report for the sample factories
make check           # the pre-push and CI gate
nix develop .#assets # Blender and ffmpeg
make server-smoke    # dedicated server smoke run; needs make bootstrap-server
```

None of these needs the licensed engine, MSVC, or Wwise. The mod build needs
all three; see [Development](docs/development.md).

## Documents

- [Design](docs/design.md): mechanics and the reasons for them.
- [Core model](docs/core-model.md): exact rules of the simulation core, tested
  in [`Tests/Core`](Tests/Core).
- [Balance](docs/balance.md): initial tuning and scenario results from
  `ep-balance`.
- [Roadmap](docs/roadmap.md): critical path and later phases.
- [Development](docs/development.md): shells, the transformer probe, toolchain,
  and the dedicated server.
- [Planned player guide](docs/player-guide.md): factory-scale LV wiring and grid choices.
- [Asset pipeline](docs/asset-pipeline.md): modeling, rendering, and game-import boundaries.
- [Prior art](docs/prior-art.md): existing Satisfactory and Minecraft mods.
- [Contributing](CONTRIBUTING.md): environments and contribution evidence.

## Visual prototypes

Blender studies with editable scenes, generators, and renders:
[transformer](assets/transformer/README.md),
[capacitor bank](assets/capacitor-bank/README.md),
[MV pole](assets/mv-pole/README.md),
[HV tower](assets/hv-tower/README.md), and
[cryo station](assets/cryo-station/README.md).
The [grid UI](assets/ui/README.md) is a browser study with simulated readings,
not a connection to a running game.

![Transformer concept render](assets/transformer/renders/hero.png)

## License

AGPL-3.0-or-later. See [LICENSE](LICENSE).
