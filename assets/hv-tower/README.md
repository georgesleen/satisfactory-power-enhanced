# EP-H16 transmission portal

Original Enhanced Power transmission structure. A broad double-chord portal head,
three outsized hanging ceramic strings and four splayed legs give HV a fundamentally
different silhouette from the compact MV mast. Orange shields protect the leg bases
and crown nodes; dark steel members and bolted gussets expose the load paths. H16
is a series identifier, not a power rating. No game capacity or phase model is implied.

## Reproduction

From the repository root:

```sh
nix develop .#assets --command blender --background --factory-startup --threads 3 --python assets/hv-tower/generate.py -- --animate --render-animation --samples 24 --width 1280 --animation-width 640 --animation-samples 8
nix develop .#assets --command ffmpeg -y -framerate 12 -i assets/hv-tower/renders/animation/frame_%04d.png -c:v libx264 -crf 19 -pix_fmt yuv420p -movflags +faststart assets/hv-tower/renders/hv-tower-operating.mp4
nix develop .#assets --command ffmpeg -y -framerate 12 -i assets/hv-tower/renders/animation/frame_%04d.png -vf "select='eq(n,0)+eq(n,20)+eq(n,33)+eq(n,47)',tile=2x2" -frames:v 1 -update 1 assets/hv-tower/renders/animation-states.png
```

The deterministic baseline produces editable `hv-tower.blend`, `metrics.json`,
`renders/hero.png`, `service.png`, `orthographic.png`, a five-second silent MP4 and
an operating-state contact sheet. It clears the scene and replaces those outputs;
preserve deliberate manual edits before regeneration. Shared primitives, surfaces,
rendering and animation helpers are imported from `../common/epkit.py`.
Stills use CPU Cycles, denoising, 1280 x 960, 24 samples. Animation uses 640 x 480,
12 fps and 8 samples. `--views hero service`, `--width` and `--samples` customize
stills. `--animate` keys the timeline; without it the scene is static and the
cabinet shows ENERGIZED. The service still is a close view of the relay cabinet.

## Placement, dimensions and sockets

Meters, Z up, origin at the center of the structural base on the placement plane.
The four 1.3 m shoes have outer bounds 6.9 x 5.1 m, inside an 8 x 8 m foundation
placement square. The 8 m studio foundation is presentation-only. The head
overhangs to approximately 11.3 m overall width, above 12 m. Reserve a separate
12 x 8 m overhead clearance envelope to accommodate the crosshead and future
cable routing. Highest crown armor reaches approximately 15.34 m. Metrics record
the exact evaluated asset envelope, separate from the placement square.

`EPH16_TransmissionTower` holds authored equipment. `Studio_non_export` holds
lights, camera, ground and foundation. There are no demo cable segments, ladders,
mandatory wheels or fans. Ground service remains accessible from the front.

Cable markers are at the center of the lower suspension eyes, all Y=0:

| Name | X | Z | Suspension |
|---|---:|---:|---|
| `CableSocket_HV_A` | -4.8 | 9.95 | Left hanging string |
| `CableSocket_HV_B` | 0 | 12.15 | Raised center hanging string |
| `CableSocket_HV_C` | 4.8 | 9.95 | Right hanging string |

The eyes are mechanical metal attachment rings, below ceramic electrical isolation.
These named empty markers are not verified engine sockets. Three visual conductors
do not prescribe the eventual player connection count or a three-phase solver.
The meshes are a stylized engineering study, not a certified load/safety calculation.

## Operating sequence

The tower never moves. Only `HV_BaseIsolation_HandlePivot` and its orange relay
control handle rotate during frames 30-37. Timeline markers label ENERGIZED
(1-16), WARNING (17-29), ISOLATING (30-36), ISOLATED (37-60). The cabinet displays
ENERGIZED, WARNING and ISOLATED; WARNING persists during the short opening motion.
Linked cabinet and head beacon lenses change green, amber, then unlit. The overhead
beacon keeps state visible with the whole silhouette in view; the service panel
contains the detailed legend. There are no random effects, arcs or lightning.
This is relay/control equipment animation, not exposed HV blade switching at ground
level. State timing is illustrative, not a gameplay trip threshold or simulation.

## References, provenance and production boundary

Visual reference links:

- [Satisfactory Power Tower](https://satisfactory.wiki.gg/wiki/Power_Tower): orange protective ends, legible long-distance transmission role and dark open load paths.
- [Power Tower reference image](https://satisfactory.wiki.gg/images/Power_Tower.png): broad material hierarchy, not copied geometry.
- [Transmission tower](https://en.wikipedia.org/wiki/Transmission_tower): general bracing and suspended insulator concepts, not a reproduced real tower design.
- [Power Switch](https://satisfactory.wiki.gg/wiki/Power_Switch): compact service feedback.

All model geometry, EP lettering and procedural surfaces are original. No game
meshes, proprietary textures, external models or downloaded fonts are bundled.
The shared EP palette supplies orange paint, graphite/tank structure, steel,
ceramic, rubber and relay emission. Blender's built-in font supplies original text.
References establish broad proportions and function; no traced logos or artwork.
Satisfactory belongs to Coffee Stain Studios; this is an independent mod concept.

This is a detailed offline visualization source, not game-ready UE content.
Editable curves, text, separate parts and bevels remain. No deliberate production
UV layout, texture baking, collision, LOD chain, mesh export, Unreal import,
snapping validation or working game wiring is claimed. Production requires mesh
consolidation/optimization, text and curve conversion, materials, meter-to-centimeter
conversion, sockets and cable-clearance tests, animation/state implementation and
licensed Unreal integration.
