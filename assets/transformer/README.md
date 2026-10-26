# EP-24 grid transformer

Original Enhanced Power industrial transformer study, authored procedurally in Blender.
Amber folded sheet armor wraps a charcoal oil vessel. The open-section skid,
pressed radiator bank, service controls and asymmetric terminals explain its function.
This is an HV-to-MV visual concept, not a shipped gameplay capacity or voltage rating.
`24` is an equipment series identifier, not a power rating.

## Files and reproduction

From the repository root, with Nix flakes enabled:

```sh
nix develop .#assets --command flock /tmp/enhancedpower-blender.lock blender --background --factory-startup --threads 3 --python assets/transformer/generate.py -- --animate
```

Blender reads model scripts from the working directory; they do not need a Nix source snapshot.
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
The tracked `transformer.blend`, `metrics.json` and renders are the first draft
from commit `692f293cea1ad8da9ae2be6e460f61dadb40f6c2`. Run the commands in this
guide to regenerate them as the industrial pilot that this guide describes.

Render only selected views or change image quality with script arguments:

```sh
nix develop .#assets --command flock /tmp/enhancedpower-blender.lock blender --background --factory-startup --threads 3 --python assets/transformer/generate.py -- --animate --views hero service --width 1280 --samples 40
```

Rendering uses Cycles CPU with denoising, 40 samples, 1280 x 960 and AgX Medium
High Contrast at +0.15 exposure. The foundation has 8 m tiles and faint 1 m lines.
The 40 mm hero camera is 3.5 m high. A side sun at 44 degrees elevation and a
pale-to-blue sky gradient give distinct face values and a visible ground shadow.
The hero includes an original tapered 1.8 m blue mannequin outside the footprint.
It is not part of the exported asset. No interactive graphics context is needed.

The generator imports `../common/epkit.py`. The kit supplies the industrial palette,
size-based bevels, plate/channel/angle/I-section helpers, real-size fasteners,
grating, louvres, the daylight site and scale figure. Existing kit APIs remain
available to generators that have not adopted this pilot.
See [Art direction](../../docs/art-direction.md) for measured rules and references.
Transformer geometry, camera poses and state timing live in `generate.py`.

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
nix develop .#assets --command flock /tmp/enhancedpower-blender.lock blender --background --factory-startup --threads 3 --python assets/transformer/generate.py -- --animate --render-animation --animation-samples 8
nix develop .#assets --command flock /tmp/enhancedpower-blender.lock ffmpeg -y -threads 3 -framerate 12 -i assets/transformer/renders/animation/frame_%04d.png -c:v libx264 -threads 3 -crf 19 -pix_fmt yuv420p -movflags +faststart assets/transformer/renders/transformer-operating.mp4
nix develop .#assets --command flock /tmp/enhancedpower-blender.lock ffmpeg -y -threads 3 -filter_threads 3 -framerate 12 -i assets/transformer/renders/animation/frame_%04d.png -vf "select='eq(n,0)+eq(n,28)+eq(n,44)+eq(n,59)',tile=2x2" -frames:v 1 -update 1 assets/transformer/renders/animation-states.png
```

`renders/transformer-operating.mp4` shows actual moving machine parts, not an orbit.
`renders/animation-states.png` shows operating, warning, tripped/coasting and isolated
states in reading order. The intermediate `renders/animation/frame_*.png` files may
be removed after encoding. The MP4 has no audio.

This is an illustrative non-looping state sequence, not a simulation or physics model.
The overload/trip timing and 108% load are presentation choices, not balanced gameplay
thresholds. Object actions, visibility keys, material emission and display text are
Blender source animation; they still need an Unreal rig/state/material implementation.

## Pilot comparison

`renders/before-after.png` is not tracked. After regenerating `renders/hero.png`,
these commands place the first-draft hero from commit
`692f293cea1ad8da9ae2be6e460f61dadb40f6c2` on the left and the pilot hero on the
right. Each panel is 1280 x 960.

```sh
git show 692f293cea1ad8da9ae2be6e460f61dadb40f6c2:assets/transformer/renders/hero.png > /tmp/ep-transformer-before.png
nix develop .#assets --command flock /tmp/enhancedpower-blender.lock ffmpeg -y -threads 3 -filter_complex_threads 3 -i /tmp/ep-transformer-before.png -i assets/transformer/renders/hero.png -filter_complex hstack=inputs=2 -frames:v 1 -threads 3 -update 1 assets/transformer/renders/before-after.png
```

The 4 m envelope, HV/MV socket coordinates and state sequence are unchanged.
The pilot uses 12 mm tank edges, 2 mm sheet edges, M16 service bolts, M24 anchors,
8 mm radiator panels at 64 mm pitch, a 200 mm stair rise and 1.1 m landing rails.
Folded panels have visible seams and bonding straps. The lid has a bolted manhole,
stiffening channels and mounted lifting eyes. The bare tank side has a weld band,
specification plate, thermometer and sampling valve. The cabinet has a silver
frame, louvres and a bracketed drip hood. Radiator guards have visible standoffs.
Grated stairs have silver stringers and ground feet. Cable eyes are 45% of the
cap diameter. Wear is narrow and grime is limited to the lowest meter.
The other four equipment generators and their renders are not part of this pilot.


## Asset contract and limits

- Meters, Z-up, origin at base center. All asset geometry stays inside the centered
  4 m square placement envelope (|x| and |y| at most 2 m); `metrics.json` records the bounds.
- `EP24_Transformer` contains the asset. `Studio_non_export` contains the camera,
  sunlight, ground grid and scale mannequin. There is no small display plinth.
- `CableSocket_HV` and `CableSocket_MV` are named empty attachment markers at the
  two terminal eyes, on opposite X sides. Taller, wider ceramic sheds identify HV.
- The cabinet load readout is a keyed state illustration, not connected to simulation.
- Painted amber, graphite and grey are dielectric finishes with roughness breakup,
  narrow edge wear and restrained ground grime. Galvanized steel, glazed ceramic,
  copper and rubber have separate finishes. All materials are editable procedural
  Blender shaders, not baked or game-integrated textures.
- Geometry is a detailed visualization source with unapplied bevel/normal modifiers,
  separate parts, curves and text. Evaluated counts include those parts and modifiers;
  they exclude all presentation geometry. Exact dimensions and counts are in `metrics.json`.
- After pilot scene regeneration, `make asset-export ASSET=transformer` derives
  an untracked delivery under `build/assets/transformer/` with baked UVs/textures,
  FBX meshes, LODs and collision. A sealed delivery from the pilot scene passed generic UE 5.6.1
  import and saved-hierarchy checks with all 35 listed hashes unchanged. The run
  retained editor compression-configuration warnings; it was not warning-free.
- Generic import does not establish rendered shading, FactoryGame paint/finish
  compatibility, runtime animation, LOD transitions, collision traversal,
  snapping/build clearance or gameplay wiring. The editable source materials
  above remain procedural. See the [delivery contract](../../docs/asset-pipeline.md#game-asset-delivery).

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
