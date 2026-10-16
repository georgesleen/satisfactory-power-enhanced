# EP-C8 superconducting link cooler

Original Enhanced Power late-game equipment study. A long stainless vacuum jacket
joins two armored SC cable couplings. Orange portals protect the cryostat, while
the right-side fin stack and twin guarded fans reject compressor heat. The left
service flank exposes insulated coolant loops, a quarter-turn isolation valve,
flow meter, generic coolant coupling and compressor. C8 is a series identifier,
not a power rating or a coolant specification.

This station illustrates cooling as the logistics cost of compact, high-capacity
transmission. It does not impose station spacing, per-machine placement rules,
or a committed nitrogen recipe. HV remains an alternative. The two connectors
are SC link endpoints, not a claim of implemented voltage conversion or gameplay.

## Reproduction

Run from the repository root:

```sh
nix develop .#assets --command blender --background --factory-startup --threads 3 --python assets/cryo-station/generate.py -- --animate --render-animation --samples 24 --animation-samples 8
nix develop .#assets --command ffmpeg -y -framerate 12 -i assets/cryo-station/renders/animation/frame_%04d.png -c:v libx264 -crf 19 -pix_fmt yuv420p -movflags +faststart assets/cryo-station/renders/cryo-station-operating.mp4
nix develop .#assets --command ffmpeg -y -framerate 12 -i assets/cryo-station/renders/animation/frame_%04d.png -vf "select='eq(n,0)+eq(n,27)+eq(n,40)+eq(n,59)',tile=2x2" -frames:v 1 -update 1 assets/cryo-station/renders/animation-states.png
```

The generator clears its scene and replaces these outputs:

- `cryo-station.blend`: editable geometry, materials, animation, studio and hero camera.
- `metrics.json`: evaluated visible asset bounds, counts, sockets and still settings.
- `renders/hero.png`: connector and heat exchanger three-quarter view.
- `renders/service.png`: coolant entry, compressor, valve and access controls.
- `renders/orthographic.png`: parallel-projection silhouette and proportions.
- `renders/animation/frame_0001.png` through `frame_0060.png`: disposable preview frames.

The encoding commands produce `renders/cryo-station-operating.mp4` (silent) and the
2x2 `renders/animation-states.png` sheet: STARTUP, READY, COOLANT LOST and SAFE
SHUTDOWN in reading order. Still images are Cycles CPU, denoised, 1280 x 960,
24 samples. Animation is 640 x 480, 8 samples, 12 fps.
Use `--views hero service` for selected stills, `--width` and `--samples` for
quality, and `--animation-width` and `--animation-samples` for animation quality.
No external textures, models, fonts or plugins are required. The shared
`../common/epkit.py` owns primitives, palette, studio, state helpers and metrics.

## Coordinates, attachment and materials

Meters, Z-up, origin at the center of the base on the placement plane. Nominal
placement footprint is 4 x 8 m, with X spanning -2 to 2 and Y spanning -4 to 4.
The full visual envelope is recorded in `metrics.json`; the display foundation,
lights, floor and camera belong to `Studio_non_export`, not the building.
`EPC8_CryoStation` holds authored asset parts.

| Marker | Location in meters | Outward side |
|---|---|---|
| `CableSocket_SC_In` | (-0.45, -3.63, 2.13) | -Y |
| `CableSocket_SC_Out` | (-0.45, 3.63, 2.13) | +Y |
| `CoolantSocket` | (-1.9, -1.45, 1.1) | -X |

Markers are Blender empties, not verified Unreal sockets. In/Out establishes
visual naming only, not a final simulation direction contract.

Original editable procedural surfaces include orange enamel, graphite structure,
satin stainless, pale ceramic insulation, rubber seals, warm-white markings,
and restrained cyan instrumentation. The narrow cyan flow meter and connector
identification bands are emissive surfaces, not magical plasma or particle effects.
The apparent insulation is opaque solid geometry rather than simulated heat flow.

## Operating sequence

The saved scene presents READY at frame 28 for still review. Timeline markers
and keyed text identify a five-second non-looping operating demonstration:

| Frames | State | Visible action |
|---|---|---|
| 1-10 | STARTUP | Valve opens a quarter turn; fan rotors begin accelerating |
| 11-22 | COOLING | Fans accelerate; segmented coolant meter begins cycling |
| 23-36 | READY | Fans maintain operation; flow segments cycle through the meter |
| 37-46 | COOLANT LOST | Warning readout appears, flow meter goes dark, valve begins isolating |
| 47-60 | SAFE SHUTDOWN | Valve closes, fans coast to a stop; safe state remains visible |

`HeatRejectionFan_A` and `_B` parent hubs and pitched blades. Ducts, finger guards
and the exchanger remain fixed. `CoolantIsolationValve` parents
the lever and position pointer. Readouts face both the front and service flank.
The camera remains fixed during animation. Warning does not explode, destroy
parts or pretend to model a real cryogenic accident. Timing is illustrative,
not a balance threshold or a physically calibrated cooling simulation.

## Production boundaries

This is an authored Blender visual study and review preview, not an integrated
Satisfactory building. Separate text, curves, cylinders, bevels and editable
material nodes prioritize inspection over runtime budget. Metrics include the
visible evaluated detail, not a proposed shipping triangle count.

There is no deliberate production UV unwrap, baked texture set, LOD chain,
collision mesh, FBX/GLB export, verified Unreal import, game snapping or traversal
validation. Primitive UVs do not establish a game-ready layout. Blender material
emission, object actions, visibility and text changes need an Unreal material,
rig/state and display implementation. Engine delivery also needs mesh
consolidation, curve/text conversion, UV and material work, collision, LODs,
meters-to-centimeters conversion and socket validation. The presentation
foundation is not buildable collision. No cooling or transmission gameplay is
implemented by the animation.

## References and provenance

Broad Satisfactory industrial style references, shared with the EP-24 study:

- [Power Tower](https://satisfactory.wiki.gg/wiki/Power_Tower): strong dark load paths,
  orange protection and legible electrical connections.
- [Power Storage](https://satisfactory.wiki.gg/wiki/Power_Storage): protected machinery,
  disciplined orange/graphite hierarchy and readable state.
- [Power Switch](https://satisfactory.wiki.gg/wiki/Power_Switch): accessible controls
  and two obvious circuit connection modules.
- [Blender manual: animation](https://docs.blender.org/manual/en/latest/animation/index.html):
  the source animation mechanism, not a claim of game integration.

The elongated cryostat, insulation loops, fan exchanger arrangement, compressor,
portal frame, labels and generator geometry are original. References are not
traced meshes. No Coffee Stain mesh, texture, logo, extracted game asset or
third-party model is included. EP is the only authored equipment mark.
Repository licensing applies to this original source and generated work;
Satisfactory belongs to Coffee Stain Studios and this concept is independent.
