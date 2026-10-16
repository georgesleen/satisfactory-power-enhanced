# EP-C4 fast-buffer capacitor bank

EP-C4 is an original Enhanced Power building study. Four removable twin-can
cassettes sit on an open industrial skid. Orange clamp bands and folded posts
frame charcoal capacitor cans. Porcelain bushings carry exposed copper bus bars.
A separate rear LV converter carries the cable terminal and a finned service
bleed resistor. Each cassette has its own five-segment charge column.

This is a short-peak real-energy buffer, not a reactive power-factor correction
bank. The labels use MW and MWh, not Mvar. It charges from spare grid headroom
and returns stored energy during a peak. It does not cover a sustained deficit
or create energy. The open low rack, repeated cans and bus bars distinguish it
from a battery or the game's tall single-vessel Power Storage building.
`C4` identifies the four-module equipment series. It does not specify capacity.

## Regenerate

Run these commands from the repository root:

```sh
nix develop .#assets --command blender --background --factory-startup --threads 3 --python assets/capacitor-bank/generate.py -- --animate
```

The generator imports the shared `../common/epkit.py` material, geometry,
studio, state-keying and metrics helpers. It needs no downloaded textures,
fonts or meshes. It clears the Blender scene and replaces named output files.
Do not run it inside an unsaved working scene.

Outputs in this directory:

- `capacitor-bank.blend`: editable scene with named objects, materials and actions.
- `metrics.json`: evaluated frame-one bounds, triangle counts and socket position.
- `renders/hero.png`: front three-quarter view with charge columns and service display.
- `renders/service.png`: rear three-quarter view with converter and bleed resistor.
- `renders/orthographic.png`: parallel-projection silhouette and scale view.
- `renders/capacitor-bank-operating.mp4`: five-second state demonstration without audio.
- `renders/animation-states.png`: 2x2 state contact sheet.

Stills use Cycles CPU, denoising, AgX, 40 samples and 1280 x 960 pixels.
Select views or quality through the shared command options:

```sh
nix develop .#assets --command blender --background --factory-startup --threads 3 --python assets/capacitor-bank/generate.py -- --animate --views hero service --width 1280 --samples 40
```

## State animation

Generate all stills, the keyed scene and the 640 x 480 preview frames, then encode:

```sh
nix develop .#assets --command blender --background --factory-startup --threads 3 --python assets/capacitor-bank/generate.py -- --animate --render-animation --animation-samples 8
nix develop .#assets --command ffmpeg -y -framerate 12 -i assets/capacitor-bank/renders/animation/frame_%04d.png -c:v libx264 -crf 19 -pix_fmt yuv420p -movflags +faststart assets/capacitor-bank/renders/capacitor-bank-operating.mp4
nix develop .#assets --command ffmpeg -y -framerate 12 -i assets/capacitor-bank/renders/animation/frame_%04d.png -vf "select='eq(n,0)+eq(n,21)+eq(n,36)+eq(n,52)',tile=2x2" -frames:v 1 -update 1 assets/capacitor-bank/renders/animation-states.png
```

The timeline uses 60 frames at 12 fps. Named markers identify these states:

| Marker | Frames | Visible state |
| --- | --- | --- |
| `IDLE_FULL` | 1-12 | All charge segments glow cyan. The readout shows `READY 100%`. |
| `DISCHARGE_PULSE` | 13-32 | Segments drop from top to bottom, module by module. Each module starts a quick warm bus flash. The contactor closes and the readout shows `PEAK ASSIST`. |
| `EMPTY` | 33-42 | All charge segments are dark. The separate status lamp glows amber. The contactor opens and the readout shows `EMPTY`. |
| `RECHARGE` | 43-60 | Segments refill from bottom to top, module by module. The readout shows `CHARGING`, then `READY 100%` at frame 60. |

The contact sheet follows timeline order: full, discharge, empty, recharge.
Named material actions key each charge segment, the copper bus and the state
lamp. `Contactor_PulseRecharge` keys the contactor pivot. Named visibility
actions switch the display text. The camera stays fixed during the MP4.
Intermediate `renders/animation/frame_*.png` files are disposable after encoding.

This sequence illustrates states, not an energy simulation or a balanced rating.
The bus flash is a state cue, not an arc, fault or claim that normal bus bars glow.
The resistor is a service bleed unit, not a source of useful discharge power.
Its fins do not animate. The sequence needs a separate Unreal state and material
implementation before it can respond to gameplay.

## Coordinates and limits

- Nominal placement footprint: 4 m x 4 m. Asset geometry stays inside the centered
  square with |x| and |y| at most 2 m.
- Meters, Z-up, origin at base center on the placement plane.
- `EPC4_CapacitorBank` contains asset geometry and attachment markers.
- `Studio_non_export` contains the floor, 4.6 m display foundation, lights and camera.
  These objects are not part of the building.
- `CableSocket_LV` marks the only external connection at the rear-right terminal
  eye, at `(1.12, 1.30, 2.83)` meters. It is an empty, not a tested Unreal socket.
- `metrics.json` records evaluated bounds and counts, including text, curves and
  bevel modifiers. It excludes studio objects and hidden display states.
- Separate parts, procedural surfaces, text and unapplied modifiers make this
  an editable visualization source, not a runtime mesh budget.
- No deliberate production UV layout, texture baking, LODs, collision mesh,
  FBX/GLB export, Unreal import, snapping, clearance or gameplay wiring exists.
  Primitive UVs are not a game UV layout.
- Engine delivery needs text/curve conversion, UVs, baking, mesh consolidation,
  collision, LODs, scale and socket checks, and a real Unreal material/state pass.

## References and provenance

Official Satisfactory Wiki building images provide broad style references:

- [Power Switch](https://satisfactory.wiki.gg/wiki/Power_Switch),
  [image](https://satisfactory.wiki.gg/images/Power_Switch.png): orange protective
  structure, dark inset service controls, porcelain connection hardware and
  restrained hazard marks.
- [Particle Accelerator](https://satisfactory.wiki.gg/wiki/Particle_Accelerator),
  [image](https://satisfactory.wiki.gg/images/Particle_Accelerator.png): open framed
  machinery, readable repeated modules and cyan operational feedback.
- [Power Storage](https://satisfactory.wiki.gg/wiki/Power_Storage),
  [image](https://satisfactory.wiki.gg/images/Power_Storage.png): a silhouette
  exclusion reference. EP-C4 does not use its tall enclosed vessel or central
  battery-style charge window.

These images guide proportions and material hierarchy. They are not included
or traced. All rack geometry, labels and generated surfaces are original.
No copied logo, Coffee Stain mesh, texture or extracted game file is included.
Repository licensing applies to the authored source and original generated work.
Satisfactory belongs to Coffee Stain Studios. This is an independent mod concept.
