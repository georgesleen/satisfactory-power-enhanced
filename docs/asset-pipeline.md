# Asset pipeline

## Scope

`assets/` holds original equipment models and a standalone browser panel.
None is integrated with Satisfactory. A render is not a game screenshot, and a
browser interaction is not a gameplay feature.

Use the assets shell independently of the licensed mod toolchain:

```sh
nix develop path:.#assets
```

The shell supplies Blender, its built-in Python API, and ffmpeg, without the
engine, MSVC, Wwise, or Wine. Licensed setup belongs in
[Development](development.md).

## Models

| Model | Guide | Role |
| --- | --- | --- |
| EP-24 grid transformer | [assets/transformer](../assets/transformer/README.md) | HV-to-MV transformer concept |
| EP-C4 capacitor bank | [assets/capacitor-bank](../assets/capacitor-bank/README.md) | MW/MWh fast energy buffer |
| EP-M6 distribution pole | [assets/mv-pole](../assets/mv-pole/README.md) | Regional MV pole |
| EP-H16 transmission portal | [assets/hv-tower](../assets/hv-tower/README.md) | HV transmission tower |
| EP-C8 link cooler | [assets/cryo-station](../assets/cryo-station/README.md) | Superconducting link cooling station |

Each model directory holds a deterministic `generate.py`, the editable `.blend`
it writes, a `metrics.json` of evaluated bounds, counts, and sockets, and review
renders. Series identifiers such as `24` or `C4` are names, not ratings. Each
guide states its exact command, outputs, dimensions, sockets, and limits.

All generators import `assets/common/epkit.py`, the shared kit for primitives,
materials, labels, state keys, metrics, and the studio rig. Model geometry,
camera poses, and state timing stay in each `generate.py`.

## Regenerate a model

Run the generator in background Blender from the repository root:

```sh
nix develop path:.#assets --command blender --background --factory-startup --threads 3 --python assets/<model>/generate.py -- --animate
```

The generator clears the scene and replaces its named outputs. Do not use it to
overwrite unpreserved manual model edits. Stills use Cycles CPU with denoising.

`--animate` keys a short non-looping state sequence in the saved scene, such as
an operating, warning, trip, and isolated sequence. `--render-animation` also
writes low-sample frames to `renders/animation/`. Each guide then encodes them
with ffmpeg into a silent MP4 and a four-state contact sheet. The frames are
disposable and ignored by Git. The MP4 and contact sheet are presentation
previews: Blender object actions, visibility keys, and material emission, not
game physics, simulation output, or an Unreal animation.

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

Each guide documents its collections and socket markers. Socket markers are
named by tier, such as `CableSocket_HV` or `CableSocket_LV`. `metrics.json`
records evaluated bounds, counts, and socket positions when generated.

Each scene has editable procedural materials and unapplied detail modifiers.
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
  and interaction behavior in the real mod target. The core energy accounting is
  implemented and host-tested; its coupling to the game's power solver is
  unverified. See [Development](development.md#open-engine-questions).

The browser panel is an interface study, not a UMG widget or game client. Sample
ratings, losses, overload timing, and traces are illustrative. Optional power
quality concepts do not commit the design to reactive power or frequency
simulation. Keep an MW/MWh fast energy buffer distinct from an Mvar/MVA reactive
power-factor correction bank. Correction is not free energy and does not remove
all harmonic distortion.

## Source, previews, and generated output

Track original editable art, generator scripts, and browser source. PNG stills,
MP4 previews, and contact sheets are derived presentation deliverables; retain
their source and reproduction command alongside them. They are not Unreal cooked
assets or evidence that the design works in game. Animation frames under
`renders/animation/` are not tracked.

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
