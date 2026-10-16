# EP-M6 regional distribution pole

Original Enhanced Power Blender study for regional MV aggregation. The compact armored
service base, replaceable orange protection, braced crossarm and three raised pale
ceramic terminals distinguish it from a taller vanilla pole. M6 is a series identifier,
not a gameplay rating. This is not a working Satisfactory buildable.

## Reproduction

From the repository root:

```sh
nix develop .#assets --command blender --background --factory-startup --threads 3 --python assets/mv-pole/generate.py -- --animate --render-animation --samples 24 --width 1280 --animation-width 640 --animation-samples 8
nix develop .#assets --command ffmpeg -y -framerate 12 -i assets/mv-pole/renders/animation/frame_%04d.png -c:v libx264 -crf 19 -pix_fmt yuv420p -movflags +faststart assets/mv-pole/renders/mv-pole-operating.mp4
nix develop .#assets --command ffmpeg -y -framerate 12 -i assets/mv-pole/renders/animation/frame_%04d.png -vf "select='eq(n,0)+eq(n,20)+eq(n,33)+eq(n,47)',tile=2x2" -frames:v 1 -update 1 assets/mv-pole/renders/animation-states.png
```

Outputs: editable `mv-pole.blend`, evaluated `metrics.json`, `renders/hero.png`,
`service.png`, `orthographic.png`, five-second silent MP4 and state contact sheet.
The generator replaces its outputs and clears the scene. Preserve manual edits first.
Shared geometry/material/render helpers come from `../common/epkit.py`.
Stills use denoised CPU Cycles, 1280 x 960 and 24 samples; animation is 640 x 480,
12 fps and 8 samples. `--views hero service` selects stills; `--samples` and `--width`
control still quality. `--animate` keys the timeline; without it the scene is static
and the cabinet shows ENERGIZED.

## Coordinates and connections

Meters, Z up, origin at base center on the placement plane. Structural base is
1.8 x 1.8 m, inside a 2 x 2 m placement tile. Ceramic/crossarm envelope extends
about 3.0 m in X, with the highest terminal eye near 7.26 m. Treat overhead
clearance as a separate 3.2 x 2 m corridor, not as the base footprint; eventual
engine cable routing still needs clearance tests. Exact evaluated bounds are in metrics.

`EPM6_DistributionPole` contains the authored equipment. `Studio_non_export`
contains the display foundation, floor, lights and camera. The foundation is not
part of the base footprint. There are no demonstration cable meshes.

Attachment empties are centered in the raised metal eyes, all at Y=0:

| Name | X | Z | Role |
|---|---:|---:|---|
| `CableSocket_MV_A` | -1.28 | 6.31 | Left crossarm terminal |
| `CableSocket_MV_B` | 1.28 | 6.31 | Right crossarm terminal |
| `CableSocket_MV_C` | 0 | 7.11 | Raised center terminal |

These are authoring markers, not verified Unreal sockets. Three visual conductors
do not imply a three-phase solver or three separate player wiring interactions.

## Useful restrained animation

The whole silhouette stays still. `BaseIsolation_HandlePivot` rotates only the
orange service handle during frames 30-37. Timeline markers identify ENERGIZED
(1-16), WARNING (17-29), ISOLATING (30-36) and ISOLATED (37-60). Cabinet text
uses ENERGIZED, WARNING and ISOLATED; the warning persists through handle motion.
Linked cabinet and upper relay lamps change green to amber to unlit. There is
no lightning, random event, tower motion, fan or wheel. The cabinet is a relay
control illustration, not exposed live MV switching at hand height. There is no
simulation hookup or physical electrical safety certification.

## Materials, source and limits

All geometry, EP labels and procedural surfaces are original. Orange paint,
graphite structure, pale ceramic, steel fasteners, copper contact necks and sealed
rubber conduit use the shared EP palette. No external meshes, fonts, textures or
Coffee Stain game files are included. Blender's built-in font supplies original text.

Style references, not traced geometry:

- [Power Poles](https://satisfactory.wiki.gg/wiki/Power_Poles): compact regional placement and readable connection hardware.
- [Power Tower](https://satisfactory.wiki.gg/wiki/Power_Tower): strong dark load paths with orange protective sections.
- [Power Switch](https://satisfactory.wiki.gg/wiki/Power_Switch): framed service controls and legible local state.

This is an authored visualization source, not a game-ready asset. Bevels, curves,
text, procedural materials and separate parts remain editable. No reviewed game
UV layout, baked texture set, collision, LODs, export or verified Unreal import is
provided. Engine delivery requires mesh optimization, text/curve conversion,
materials, explicit meter-to-centimeter conversion, socket validation, placement
clearance, animation/state implementation and licensed-toolchain integration.
