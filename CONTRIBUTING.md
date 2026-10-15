# Contributing

Enhanced Power is a design and asset project, not a playable mod. The transformer
runtime is blocked on verified solver ordering and energy conservation. Blender
previews and the browser panel are prototypes, not evidence of in-game behavior.

## Start here

```sh
git clone https://github.com/georgesleen/satisfactory-power-enhanced.git
cd satisfactory-power-enhanced
```

For art, enter the separate assets shell:

```sh
nix develop path:.#assets
```

It supplies Blender without the licensed engine, MSVC, Wwise, or Wine. See the
[asset pipeline](docs/asset-pipeline.md) for source and preview commands.

For runtime work, follow [Development](docs/development.md) for official licensed
vendor acquisition, the mod shell, source evidence, and runtime acceptance checks.
The default shell is not the assets shell. Do not redistribute vendor downloads,
credentials, or proprietary engine content.

## Where work belongs

- `docs/design.md`: mechanics, decisions, and open design questions.
- `docs/roadmap.md`: implementation sequence.
- `docs/development.md`: toolchain setup and unresolved runtime contracts.
- `assets/transformer/`: authored Blender model, generator, and review renders.
- `assets/ui/`: standalone browser interface prototype with simulated data.
- `nix/`, `flake.nix`, and `Makefile`: toolchain definitions and commands.

There is no EnhancedPower gameplay module or buildable transformer target. Paths
in the development document that refer to the official starter are upstream
sources, not implementations in this repository.

## Submit a focused change

Explain the problem, the proposed result, and what you actually observed. Separate
accepted decisions from proposals and simulations from working gameplay.

- **Design:** identify the player decision and tradeoff. Vanilla LV should serve
  one reasonably sized factory; higher tiers address distance and multiple
  factories, not per-machine wiring chores. Numerical tuning remains a proposal
  unless accepted explicitly.
- **Art:** include editable source, provenance, reproduction commands, and useful
  previews. State which modeling, export, and integration steps were exercised.
- **Code:** use existing conventions, update affected callers and documentation,
  and add relevant acceptance coverage. Report exact commands and outcomes,
  including anything not run and why. A successful render or simulated panel
  does not verify power conservation, multiplayer, persistence, or game loading.

## Authorship and licensing

Submit only original work you can license under the repository's
[AGPL-3.0-or-later license](LICENSE), or identify compatible third-party material
and its source, author, license, and required attribution explicitly. Keep that
provenance beside the asset. Do not copy or extract Coffee Stain meshes, textures,
icons, audio, or other proprietary assets into submissions. References are not
permission to redistribute their content. This is an independent project, not a
Coffee Stain Studios release or endorsement.

Editable `.blend` files are intentional authored deliverables, not disposable
engine output. Requested PNG review previews may accompany their source. Do not
submit Unreal caches, cooked packages, build products, editor backups, secrets,
or licensed toolchain archives. See the asset pipeline for storage conventions.
