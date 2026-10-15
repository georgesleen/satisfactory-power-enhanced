# Asset pipeline

## Scope

`assets/transformer/` holds an original transformer visual study.
`assets/ui/` holds a standalone browser panel with simulated telemetry. Neither
is integrated with Satisfactory. A render is not a game screenshot, and a working
browser interaction is not a working gameplay feature.

Use the lightweight art shell independently of the licensed mod toolchain:

```sh
nix develop path:.#assets
```

The shell supplies Blender and its built-in Python API, without the engine,
MSVC, Wwise, or Wine. Official licensed setup belongs in
[Development](development.md).

## Regenerate the transformer

From the repository root:

```sh
nix develop path:.#assets --command blender --background --factory-startup --threads 6 --python assets/transformer/generate.py -- --animate
```

The generator writes `assets/transformer/transformer.blend`,
`assets/transformer/metrics.json`, and `assets/transformer/renders/hero.png`,
`service.png`, and `orthographic.png`. It replaces those outputs. Do not use it
to overwrite unpreserved manual model edits. The default scene uses Cycles CPU,
40 samples, denoising, and 1280 x 960 review images.

The saved scene includes a five-second, 60-frame illustrative sequence with
moving fan rotors, breaker trip, and keyed cabinet indicators. This is Blender
animation, not game physics or a verified Unreal animation implementation.

See the [model source guide](../assets/transformer/README.md) for selected-view
rendering, animation-frame generation, FFmpeg encoding of
`renders/transformer-operating.mp4` and `renders/animation-states.png`, provenance,
and exact limitations. These requested previews are presentation derivatives,
not engine binaries. Intermediate animation frames are disposable after encoding.
Successful generation and visual inspection must still be reported as observed
results, not inferred from the script.

## Preview the browser panel

With Python 3 available, run from the repository root:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory assets/ui
```

Open <http://127.0.0.1:8765/>. Stop the local server with Ctrl+C. Python is needed
only for this static preview server; the assets shell supplies Blender, not a
Python web toolchain.

The source is `assets/ui/index.html`, `terminal.css`, and `terminal.js`, with
usage and limitations in [the UI guide](../assets/ui/README.md). There are no
third-party browser dependencies or network assets. All telemetry is simulated;
the panel has no Unreal, SML, or game connection.

## Editable source and coordinates

Keep the editable `.blend` model and the deterministic Blender Python generator
together. The `.blend` is an intentional authored deliverable: reviewers can
inspect and edit its objects, materials, cameras, and lights without rebuilding
the scene. The generator records the reproducible baseline. Preserve deliberate
manual edits in source rather than silently overwriting them with a regeneration.
Deterministic scene construction does not promise byte-identical Blender files
or renders across Blender versions and render backends.

Author dimensions in meters, with Z up and the building origin at the center of
the base on the placement plane. Document the footprint separately from the
full visual envelope. Keep placement guides, attachment markers, cameras, lights,
and render staging distinguishable from the meshes intended for eventual export.
Name attachments by voltage tier and document their side and position. A marker
does not prove a functioning Unreal socket or electrical connection.

The EP-24 study uses a nominal 4 m square footprint. Its `EP24_Transformer`
collection contains the asset; `Studio_non_export` holds presentation geometry,
including a separate 4.6 m display foundation, plus cameras and lights.
`CableSocket_HV` and `CableSocket_MV` are empty markers at opposite X-side
terminal eyes. This is an HV-to-MV visual concept, not an HV-to-LV model or a
committed gameplay rating. `metrics.json` records evaluated bounds, counts, and
socket positions when generated.

The scene has editable procedural materials and unapplied detail modifiers.
There is no deliberate game UV layout, texture bake, export, collision mesh, LOD
chain, or verified Unreal import. These are planned delivery steps, not hidden
capabilities of the `.blend`.

## Integration boundary

The Blender scene and review images establish a visual design, not a game-ready
asset. Treat the following as integration work unless accompanied by explicit
observed evidence:

- **Materials:** map Blender materials to supported Unreal materials and confirm
  appearance in the target renderer. A procedural shader is not an exported
  texture set.
- **UVs:** inspect UV coverage, texel density, seams, and any baked maps. Generated
  primitive coordinates do not establish a reviewed production unwrap.
- **Export:** choose the engine-supported mesh format and verify applied scale,
  transforms, normals, material slots, and attachment placement after import.
  Convert meters to Unreal centimeters through an explicit export/import setting.
- **Collision:** author simple collision and verify placement, traversal, cable
  clearance, and interaction in engine. A visible base is not collision evidence.
- **LODs:** author and inspect distance representations and performance before
  claiming runtime suitability. A detailed offline render is not an LOD budget.
- **Game integration:** register the actual mesh, materials, sockets, buildable,
  and interaction behavior in the real mod target. Transformer energy accounting
  remains blocked on the contracts in [Development](development.md).

The browser panel is an interface study, not a UMG widget or game client. Sample
ratings, losses, overload timing, and traces are illustrative. Optional power
quality concepts do not commit the design to reactive power or frequency
simulation. Keep an MW/MWh fast energy buffer distinct from an Mvar/MVA reactive
power-factor correction bank. Correction is not free energy and does not remove
all harmonic distortion.

## Source, previews, and generated output

Track original editable art, generator scripts, and browser source. The requested
PNG review previews are intentional derived presentation deliverables; retain
their source and reproduction command alongside them. They are not Unreal cooked
assets or evidence that the design works in game.

Keep engine-generated `Binaries`, `Intermediate`, `Saved`, `DerivedDataCache`,
cooked packages, transient export trials, Blender backups, and licensed vendor
payloads out of submissions. Exported runtime assets need an explicit integration
purpose and provenance, not automatic inclusion of every generated file.

Use ordinary Git for these sources and review images. Do not introduce Git LFS
without measured asset sizes that warrant it. Binary format alone does not make
an authored `.blend` disposable or require LFS.

All model geometry, surface treatments, UI artwork, and textures must be original
or carry explicit compatible source and license records. Record creator, source,
license, attribution, and modifications beside any third-party input. Do not
redistribute extracted game assets, vendor samples without permission, or copied
Coffee Stain artwork. The repository license does not grant rights to external
references or imply official affiliation.
