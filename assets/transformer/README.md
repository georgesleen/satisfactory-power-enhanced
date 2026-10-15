# EP-24 grid transformer

Original Enhanced Power industrial transformer study, authored procedurally in Blender.
The orange folded shoulder armor wraps a dark oil vessel; the exposed radiator bank,
rear oil circuit, instrument cabinet and asymmetric terminal heights explain its function.
This is an HV-to-MV visual concept, not a shipped gameplay capacity or voltage rating.
`24` is an equipment series identifier, not a power rating.

## Files and reproduction

From the repository root, with Nix flakes enabled:

```sh
nix develop path:.#assets --command blender --background --factory-startup --threads 6 --python assets/transformer/generate.py -- --animate
```

The explicit `path:.` flake includes new local source files before they are tracked by Git.
The command generates:

- `transformer.blend`: editable scene, materials, studio and hero camera.
- `renders/hero.png`: front/radiator three-quarter view.
- `renders/service.png`: opposite rear/service view.
- `renders/orthographic.png`: parallel-projection silhouette/scale inspection.
- `metrics.json`: evaluated asset bounds, renderable object and triangle counts,
  socket coordinates, render engine, resolution and samples.

All paths above are relative to this directory. No downloaded textures, fonts or
models are required. The Blender built-in font is used for original equipment labels.
The script clears the scene, so run it in background mode rather than inside an
unsaved working scene. Repeated generation replaces the named outputs.

Render only selected views or change image quality with script arguments:

```sh
nix develop path:.#assets --command blender --background --factory-startup --threads 6 --python assets/transformer/generate.py -- --animate --views hero service --width 1280 --samples 40
```

Rendering uses Cycles CPU with denoising, 40 samples, 1280 x 960, AgX and large area
lights. No interactive graphics context, Unreal, Wine or Windows compiler is needed.

## Operating animation

`--animate` keys a five-second, 60-frame demonstration at 12 fps in the saved scene.
Timeline markers distinguish operating (frames 1-24), warning (25-40), breaker trip
(41-45), fan coast-down (46-59) and isolated (60). `CoolingFan_Rotor_A` and
`CoolingFan_Rotor_B` parent the separate pitched blades and hubs. Each rotor turns inside
a fixed graphite duct with a motor and a three-strut spider tied to the duct wall,
behind a finger guard. `Breaker_Handle` pivots into its tripped position. Named actions
also switch the cabinet readout/load bars and pulse the status lamp before the trip.
The readout shows `TRIPPED` and the lamp stays red through the coast-down. At frame 60
the readout shows `ISOLATED` and the lamp is unlit. The fan ducts and oil vessel do not rotate.

Generate the stills, keyed scene and low-sample 640 x 480 animation frames, then encode:

```sh
nix develop path:.#assets --command blender --background --factory-startup --threads 6 --python assets/transformer/generate.py -- --animate --render-animation --animation-samples 8
nix develop path:.#assets --command ffmpeg -y -framerate 12 -i assets/transformer/renders/animation/frame_%04d.png -c:v libx264 -crf 19 -pix_fmt yuv420p -movflags +faststart assets/transformer/renders/transformer-operating.mp4
nix develop path:.#assets --command ffmpeg -y -framerate 12 -i assets/transformer/renders/animation/frame_%04d.png -vf "select='eq(n,0)+eq(n,28)+eq(n,44)+eq(n,59)',tile=2x2" -frames:v 1 -update 1 assets/transformer/renders/animation-states.png
```

`renders/transformer-operating.mp4` shows actual moving machine parts, not an orbit.
`renders/animation-states.png` shows operating, warning, tripped/coasting and isolated
states in reading order. The intermediate `renders/animation/frame_*.png` files may
be removed after encoding. The MP4 has no audio.

This is an illustrative non-looping state sequence, not a simulation or physics model.
The overload/trip timing and 108% load are presentation choices, not balanced gameplay
thresholds. Object actions, visibility keys, material emission and display text are
Blender source animation; they still need an Unreal rig/state/material implementation.


## Asset contract and limits

- Meters, Z-up, origin at base center. All asset geometry stays inside the centered
  4 m square placement envelope (|x| and |y| at most 2 m); `metrics.json` records the bounds.
- `EP24_Transformer` contains the asset. `Studio_non_export` contains cameras,
  lights, floor and the 4.6 m display foundation, which is not part of the building.
- `CableSocket_HV` and `CableSocket_MV` are named empty attachment markers at the
  two terminal eyes, on opposite X sides. Taller, wider ceramic sheds identify HV.
- The cabinet load readout is a keyed state illustration, not connected to simulation.
- Named procedural paint, metal, rubber, ceramic and emission materials are editable.
  Fine painted-surface bump is render shading, not baked texture detail.
- Geometry is a detailed visualization source with unapplied bevel/normal modifiers,
  separate parts, curves and text. Evaluated counts include those parts and modifiers;
  they exclude all presentation geometry. Exact dimensions and counts are in `metrics.json`.
- No game UV layout, texture baking, LOD chain, collision mesh, Unreal import,
  snapping/build clearance integration or gameplay wiring has been completed.
  Primitive UVs are not a production UV layout. There is no GLB/FBX export here.
- Engine delivery requires conversion of text/curves, material/texture baking,
  deliberate mesh consolidation and optimization, UVs, collision, LODs and an Unreal
  import/material/socket validation pass. This is not a production-ready Unreal asset.

## Visual references and provenance

Official wiki building images and descriptions used as style references:

- [Power Storage](https://satisfactory.wiki.gg/wiki/Power_Storage),
  [building image](https://satisfactory.wiki.gg/images/Power_Storage.png): strong
  orange-over-graphite material hierarchy, protective structure and visible energy state.
- [Power Switch](https://satisfactory.wiki.gg/wiki/Power_Switch),
  [building image](https://satisfactory.wiki.gg/images/Power_Switch.png): two clearly
  differentiated grid connections, framed service controls and small status feedback.
- [Power Tower](https://satisfactory.wiki.gg/wiki/Power_Tower),
  [building image](https://satisfactory.wiki.gg/images/Power_Tower.png): exposed dark
  load paths, orange protective ends and prominent electrical connection hardware.

These anchor broad industrial proportions and readability, not traced geometry.
The transformer silhouette, folded shells, cooling layout, labels and mesh generation
are original. No Coffee Stain mesh, texture, logo or proprietary game file is included.
Satisfactory is Coffee Stain Studios' game; this is an independent mod concept.
Repository licensing applies to the authored source and generated original work.
