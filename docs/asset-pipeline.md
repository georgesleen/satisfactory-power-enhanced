# Asset pipeline

## Scope

`assets/` holds original equipment models and a standalone browser panel.
None is integrated with Satisfactory. A render is not a game screenshot, and a
browser interaction is not a gameplay feature.

Use the assets shell independently of the licensed mod toolchain:

```sh
nix develop .#assets
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
nix develop .#assets --command blender --background --factory-startup --threads 3 --python assets/<model>/generate.py -- --animate
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

## Preview the browser building menus

Build and serve from the repository root:

```sh
nix develop .#ui -c make ui
nix develop .#ui -c make ui-preview
```

Open <http://127.0.0.1:8080/>. Stop with Ctrl+C. Use `UI_PORT=8081` for another
loopback port. The separate UI shell supplies Emscripten and Python without
licensed game tools. The assets shell is for Blender and ffmpeg.

`make ui` stages `assets/ui/index.html`, `menu.css`, `menu.js`, fonts and the
generated WebAssembly module in `build/ui/`. Serve that built directory, not
raw `assets/ui/`. The module compiles the real engine-free C++ core; a load
failure is an error, not a fallback to authored traces. There are no external
browser requests or Unreal, SML, or live-game connections. See the
[UI guide](../assets/ui/README.md) for controls and runtime limits and the
[UI specification](ui-spec.md) for the native widget contract.

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
The authored source scenes do not contain the separate game UV/bake/LOD/collision
delivery outputs. See [Game asset delivery](#game-asset-delivery) for derived
candidates and validation. Unreal and game-context readiness require explicit
import evidence.

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

The browser menus are interface studies, not native UMG/FactoryGame widgets.
Transformer transport and heat, capacitor storage and island loss use the real
core and balance tuning in synthetic scenarios. The imposed-load thermal test
is not ordinary end-to-end overload behavior. Cryo supply is a presentation
concept; warm-line capacity, loss, cooling consumption and trip rules remain
unspecified. The pole view previews a small vanilla-menu addition with a fixed
LV simulation and tier-capacity metadata, not an installed vanilla hook or
discovered game topology. Keep MW/MWh storage distinct from reactive-power
correction; optional power-quality mechanics are not implemented by these menus.

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

## Game asset delivery

The editable source remains `assets/<name>/generate.py` and
`assets/<name>/<name>.blend`. Export reads the saved scene, not the generator.
`assets/common/epexport.py` implements the delivery pipeline;
`assets/common/export_asset.py` is its background-Blender entry point.
The source scene is not modified on disk.

```sh
make asset-export ASSET=transformer
make asset-export                 # all five, sequentially
nix develop .#assets --command flock /tmp/enhancedpower-blender.lock \
  blender --background --factory-startup --threads 3 --python-exit-code 1 \
  --python assets/common/export_asset.py -- assets/transformer
```

Every Blender run takes the shared lock. Cycles uses the thread count given by
Blender's `--threads` option; the commands above use three.
The CLI accepts `--blend <path>` for a preserved source copy,
`--output <directory>`, `--texture-size <pixels>` (default 2048), and
`--skip-renders`. The atlas uses 4-pixel per-island padding and a separate
1-pixel bake dilation. The export stops with an invalid-atlas error before
baking if the layout has overlap, zero-area UVs or coordinates outside 0 to 1.
A development export can read
`build/export-dev/transformer.blend` without competing with source art changes.

### Scene naming contract

- Keep exactly one root asset collection. Name staging collections with the
  `_non_export` suffix. Only visible frame-one asset geometry is delivered.
- Use meshes, curves, and text for render geometry. Modifiers remain on the
  detailed bake source. The low mesh omits bevel, weighted-normal and subdivision
  modifiers and reduces curve tessellation.
- Parent moving geometry to a transform-keyed pivot, or name its pivot
  `MOVING_<part>`. A transform-keyed mesh is also a separate part. Visibility
  keys alone do not make mechanical parts. Hidden state variants and animation
  curves are not exported as runtime behavior.
- Prefix bake-only details with `BAKE_`. Text and unparented details whose longest
  dimension is below 0.12 m are also bake-only. Keep these details within the
  0.06 m projection cage of a receiving surface. Any non-text part within 0.1 m
  of a socket stays real geometry, whatever its size.
- Tag complete critical hardware with `ep_lod_preserve=True` and an
  `ep_lod_assembly` semantic name. The transformer tags its complete HV and MV
  terminal supports, porcelain stacks, caps and eyes. Tagged geometry is never
  baked away or omitted. It stays unreduced through LOD2. At LOD3 it is reduced
  only within a 2.5 mm RMS error limit. Validation checks that every tagged part
  is present in every shipped LOD, with bounds within 5 mm of LOD0.
- Name attachment empties with `Socket`, for example `CableSocket_HV` or
  `CoolantSocket`. Export uses `SOCKET_<LOD0 mesh name>_<index>` and records
  the logical-to-FBX name mapping in `validation.json`.
- Paint categories use material prefixes: `Enamel |` is primary paint;
  `Structure |` and `Tank |` are secondary paint. Other materials are fixed.
  A material's `ep_paint` custom property can explicitly select `primary`,
  `secondary`, or `fixed`. Source materials use Principled BSDF inputs.
- Author meters, Z up, origin at the base-center placement plane. Moving-part
  origins are their actual pivots.
- Author optional `ep_uv_importance` as a positive finite linear density
  factor on a source receiving mesh. The exporter copies it to that mesh's
  `_low` receiver; the shared packer has no object-name exceptions. Default 1
  preserves ordinary body density. The transformer's front equipment belt,
  recessed readout glass and inset identity/voltage door use factor 3.
  Importance does not change geometry, fonts or shader style.

### Derived delivery

All outputs live under the gitignored `build/assets/<name>/`:

- `SM_<name>_Body.fbx` and one FBX per moving part. Each contains a Blender
  `fbx_type=LodGroup` empty with up to four LOD mesh children. Each file
  represents one Unreal static mesh, not the entire blueprint.
- `assembly.json` schema 2 identifies every independent static-mesh FBX, actual
  LOD count, shared material slot and body pivot socket. It retains Blender-axis
  `source_reference_transform_cm` and supplies Unreal-axis
  `relative_transform_cm`. Moving meshes are not silently merged into the body.
  The generic-bake result and unverified FactoryGame paint profile are separate.
  The shared baked slot is asset-specific and identifier-safe, such as
  `M_transformer_Baked`.
- `UCX_<LOD0 mesh name>_<index>` collision boxes in the body FBX. Up to 16
  non-contained major source-part bounds become convex boxes. These are
  traversal collision, not placement clearance, and do not model cable clearance.
- Attachment and moving-part pivot empties in the body FBX follow Epic's
  `SOCKET_<RenderMeshName>_<index>` helper convention. Each moving-part mesh
  is exported at its own local origin; the pivot socket supplies its placement
  and orientation in the buildable blueprint. Use the report's
  `socket_export_names` mapping rather than assuming imported socket names.
- `textures/BaseColor.png`, `Normal.png`, `AOMasks.png`, and
  `ReflectionMap.png` are the material delivery textures. Standalone AO,
  roughness, metallic, emissive, emission-mask, and semantic paint-mask maps
  are retained for inspection and repacking.
- `game.blend` is the derived scene with packed baked maps.
- `validation.json` records measured geometry, UVs for every LOD, density,
  collision, socket positions, pivots and centimeter bounds. No mirrored or
  shared UV regions are excluded from overlap measurement. Each FBX is
  reimported into an isolated Blender scene and checked for triangle counts,
  bounds, material slots, collision convexity and count, and socket transforms.
  Blender's importer converts the centimeter FBX back to meters as a uniform
  0.01 object scale; the check compares world bounds and rigid socket
  location and rotation, and requires that scale to be uniform. A mismatch
  fails the export. This is a Blender round-trip, not an Unreal import check.
  The export also stops before baking if the LOD0 atlas has zero-area UV
  triangles, UVs outside 0 to 1, or intersecting UV triangles.
  `generic_blender_bake_validation` is PASS only when every Blender check
  passes, and it lists each failure otherwise. `material_profile` is a
  separate field: it names the delivery `generic_colored_PBR_reference` and
  marks FactoryGame paint appearance UNVERIFIED. The report also records the
  source `.blend` SHA-256.
- `delivery-complete.json` schema 1 is the authoritative sealed release marker.
  It is invalidated first on a new export and written atomically last, only on
  generic validation PASS. It lists SHA-256 hashes for every delivered FBX,
  texture and review product, plus `validation.json` and `assembly.json`.
  Validation hashes the products and assembly; assembly's
  `product_files_sha256` excludes itself to avoid a recursive hash. Importers
  verify all hashes and reject unlisted FBXs or texture PNGs, with no legacy
  unhashed-PASS fallback. `renders_skipped` and stage statuses are explicit.
  Unknown user files are not deleted; conflicting unmanaged products make the
  export refuse the output directory. Archived prior bakes remain separate.
- `validation/negative-nonuniform.fbx` is a synthetic mirrored, rotated,
  nonuniform-scale tetrahedron round-trip fixture, not an equipment mesh.
  Its report checks canonical positive winding, centimeter bounds, rigid socket
  transforms and convex collision. Evaluated equipment copies likewise bake
  source transforms into vertices and correct mirrored winding; source negative
  and nonuniform transforms remain inventoried.
- `bake-check.png` compares detailed geometry at left with textured LOD0 at
  right, using the same source camera. `lod-check.png` shows LOD0, LOD1, LOD2
  and LOD3 left to right. Individual panel PNGs are also retained.

The exporter consolidates fixed geometry into the body and preserves moving
parts separately. All parts share one UV0 atlas and material slot. Smart
projection authors the charts; `assets/common/epuv.py` normalizes their area
scale and packs all selected islands globally with Blender's CONCAVE shape
method. After common area normalization, authored importance scales critical
receiver UVs relative to ordinary body UVs before packing. Charts and seams
are retained, not merged. The global fit can change absolute body density;
factor 3 is a relative ratio, not a guarantee of a particular pixels-per-meter
value. Validation reports the actual density and coverage for each priority
group, as well as the combined atlas. The 4-pixel per-island
margin produced a measured 7.9988-pixel minimum total inter-chart gap and
3.9998-pixel atlas-edge margin on the 457-receiver transformer proof.
Cycles expands each baked island by only 1 pixel, leaving about 6 pixels
between the two expanded borders and 3 pixels at the atlas edge at mip 0.
Normal and surface channels project component by component from detailed
geometry onto triangulated low meshes before consolidation. Bake-only details
are assigned to the nearest receiving component's surface. Each projection
selects only its matching detailed component and assigned details, excluding
neighboring thin panels from the ray source set. AO is baked on all low meshes
with detailed source copies hidden.

The smaller gutters recover useful texel density without increasing texture
resolution. They shrink in lower mips: a 6-pixel filtering guard at mip 0 is
about 1.5 pixels at mip 2 and less than one pixel at mip 3. Mip generation stays
enabled. Filtering and distant-LOD bleed still require engine inspection; no
finite small gutter guarantees isolation through every mip. Review both the
actual 2048 stencil crop and LOD contact sheet, not an enlarged old bake.
Uncovered normal-map texels start at flat tangent normal `(0.5, 0.5, 1)`;
AO starts at white before the component bakes. These neutral fills avoid black
invalid-normal and fully occluded backgrounds, but do not eliminate
inter-island filtering or lower-mip bleeding.

LODs use a UV-preserving edge collapse. A vertex merges onto a neighbor only if
the merge keeps every UV triangle unfolded with nonzero area. A vertex on a UV
seam, a sharp edge or an open edge moves only along that edge. Open-edge and
non-manifold vertices stay fixed. Each LOD has an RMS surface error limit of
5 mm, 15 mm and 40 mm, and a triangle target of 50%, 25% and 12%. LOD1, LOD2 and
LOD3 also omit fixed components shorter than 0.16 m, 0.3 m and 0.6 m.
Components within 0.1 m of a socket are never omitted, and they are not reduced
before LOD3. Moving components are not omitted. A LOD with more than 75% of the
triangles of the previous shipped LOD is dropped; the report lists dropped LODs
and the actual triangle counts.
Semantic `ep_lod_preserve` assemblies follow the same rule and are never
omitted. Nearby socket geometry alone does not preserve a complete support
structure, so tag the whole assembly.

Validation fails if any socket is more than 0.1 m from the nearest surface of
any shipped body LOD. Non-manifold edges are reported per LOD. They are
acceptable on the render-only mesh when the bake is clean; collision uses
separate closed convex boxes.

The 2048-pixel default is a delivery choice, not a claimed Satisfactory standard.
The report measures density in pixels per centimeter from UV and triangle area.
UV validation clips candidate triangle pairs geometrically and reports summed
pairwise overlap area, ignoring only intersections below 1e-12 UV-square units.
It also samples coverage and multiply-covered pixels on a 1024-square grid.
Pairwise area can exceed unique overlapped area when three triangles coincide.
Density includes minimum, maximum, percentiles and an area-weighted value.
Non-manifold edges are reported rather than hidden. Review the report and
contact sheets before importing; generation alone is not acceptance.
### State delivery boundary

The bake is explicitly a frame-one visual snapshot, not animation support.
Visible readout text and indicator colors can therefore be fixed in the baked
atlas. `validation.json` inventories every keyed object, all text variants
including hidden-at-frame-one messages, source channel keyframes, animated
material channels and the objects using them. The editable source `.blend`
retains those variants and actions. No hidden variant is silently treated as
unnecessary.

FBX carries separate moving meshes and their pivot/socket transforms, but no
animation tracks, visibility tracks, display text swapping or dynamic material
curves. In Unreal, supply Blueprint transform/state logic, replace snapshot
readouts with runtime display geometry or textures, and drive indicator
materials from actual production status. Source colors and timing are visual
studies, not implemented runtime behavior.


### Game material and Unreal import

The documented unique-bake workflow uses a material instance based on
`MM_FactoryBaked`. The docs suggest `/Utils/Materials/MI_BakedMachineStarter`;
the pinned local starter lacks that helper, so create a child instance of the
actual master material instead.
The separate `MM_Factory_Array` / `MI_Factory_Base_01` workflow expects the
game's atlas UV layout and is not compatible with these unique atlases.
See [Main Materials](https://docs.ficsit.app/satisfactory-modding/latest/Development/Modeling/MainMaterials.html#_factory_baked_mm_factorybaked).

Bind the baked textures to the instance's matching parameters:

| Parameter | File | RGB meaning | sRGB |
| --- | --- | --- | --- |
| `Albedo` | `BaseColor.png` | Base color | On |
| `Normal` | `Normal.png` | Tangent-space normal, DirectX Y- | Off |
| `AOMasks` | `AOMasks.png` | AO, primary paint, secondary paint | Off |
| `ReflectionMap` | `ReflectionMap.png` | Metallic, roughness, emission mask | Off |

`PaintMask.png` is an intermediate semantic map with red primary, green
secondary and black fixed; do not bind it directly to `AOMasks`.
For the nonlegacy base-paint path, explicitly enable `CanBePainted` and disable
`bUseLegacyPaintTextures`. The inspected defaults are false and true,
respectively. The base-color stage blends raw Albedo toward
`Albedo * saturate(primaryColor * G + secondaryColor * B)`, with blend weight
`saturate((G + B) * PaintTintIntensity)`; the inspected intensity default is 1.
Thus zero masks leave Albedo unchanged, unit G or B selects the corresponding
multiplicative tint, and overlapping masks add before saturation rather than
selecting a priority color.

This description comes from a read of the starter material graph through generic
UE 5.6. It does not establish final FactoryGame shading,
paint finishes, runtime Customizer color values or emissive behavior. The
approved colored BaseColor remains the authored appearance reference, so paint
swatches multiply that tint rather than replacing it. Neutral grayscale Albedo
is a possible swatch-faithful authoring option that is not tested. It is not an
automatic change to this approved art or a universal material requirement.

Multiplicative tint can double-tint or desaturate the authored amber and colored
secondary regions. This generic PBR bake is therefore **not a swatch-faithful
FactoryBaked/Customizer-ready texture set**. Correct channel packing alone does
not solve paint appearance. An explicit material-profile or texture-authoring
decision remains necessary, followed by game-default palette, finish and
FactoryGame-context validation. Keep the original PBR preview as the approved
appearance reference.

Blender's normal-map convention is OpenGL positive Y and Unreal's is DirectX
negative Y, as tabulated in
[Polycount's swizzle reference](http://wiki.polycount.com/wiki/Normal_Map_Technical_Details#Common_Swizzle_Coordinates).
The exporter explicitly bakes tangent normals with `normal_r='POS_X'`,
`normal_g='NEG_Y'`, `normal_b='POS_Z'`. Unreal's
[Flip Green Channel](https://dev.epicgames.com/documentation/en-us/unreal-engine/texture-properties?application_version=4.27)
must stay **off**. The Blender-only preview shader reverses that green swizzle
for display; no second green flip is written to the exported normal map.
The report records this choice and every image's color space. AO, normals,
semantic masks, metallic, roughness, emission masks and packed reflection data
are linear; only color images use sRGB.


Epic's [UE 5.6 FBX Static Mesh Pipeline](https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-static-mesh-pipeline-in-unreal-engine?application_version=5.6)
sets these import limits:

- Only one socket-bearing render asset can be set up in an FBX file. Separate
  independent meshes with their own sockets require separate files.
- `SOCKET_<RenderMeshName>_<index>` and `UCX_<RenderMeshName>_<index>` must match
  the associated render mesh name exactly. This delivery matches the LOD0
  child name; the sealed transformer's generic import recognized its LOD groups
  and five body sockets. Other deliveries need their own engine readbacks.
- Only the first mesh's custom collision is imported from a multi-mesh file.
  The body owns the only collision set here; moving parts are separate FBXs
  without collision.
- All LODs must occupy the same space and share the same pivot. Enable Import
  LODs, then inspect the resulting LOD picker.
- Epic recommends non-intersecting convex collision pieces. Major-part bound
  boxes can overlap, so a convexity pass does not replace traversal review.
- The Unreal importer targets FBX 2020.2. Bundled Blender writes binary FBX
  version 7400. Its Blender round-trip does not prove UE 5.6 compatibility.

Use schema 2 `relative_transform_cm` directly for the Unreal hierarchy.
Measured generic UE 5.6 import maps Blender `(x,y,z)` to Unreal `(x,-y,z)`.
Child transforms are conjugated by that basis, `C*M*C`. The source design front
is Blender -Y, so the raw imported mesh faces Unreal +Y. An explicit Body-root
yaw of -90 degrees makes the assembled service front +X without modifying the
FBX geometry or socket basis. `Body.relative_transform_cm` contains that
rotation already. Global `assembly_root_transform_cm` is an explanatory
duplicate, **not a second rotation to apply**.

The manifest's `unreal_socket_names` removes the FBX `SOCKET_` helper prefix,
as observed in the early body import. Its source-reference matrices are for
provenance, not values to copy directly into Unreal. Electrical components
still need explicit Blueprint setup. The sealed transformer's complete-set generic
import verified socket ownership, the saved hierarchy and transformed child pivots;
this does not prove runtime animation.

Use these explicit FBX import settings as the starting contract. The sealed
transformer has separate generic engine evidence below:

- Static Mesh; Import Mesh LODs on; Combine Meshes off; Import Uniform Scale 1.
- Convert Scene on; Convert Scene Unit on; Force Front XAxis off.
  Export uses Y forward and Z up, with the meter-to-centimeter factor baked
  into FBX geometry and an FBX unit scale of one centimeter.
  These axis and pivot options are project choices, not a proven universal
  Satisfactory preset; Blender round-trip bounds do not establish in-game facing.
- Transform Vertex to Absolute off; Bake Pivot in Vertex off.
  Place moving parts at the exported body pivot sockets.
- Normal Import Method: Import Normals and Tangents; Normal Generation Method:
  MikkTSpace. Do not recompute the baked tangent basis.
- Import Materials off; Import Textures off. Create and assign the material
  instance explicitly. Use Normalmap compression for `Normal.png` with
  Flip Green Channel off. Use Masks compression and sRGB off for both packed
  masks. Use Default compression with sRGB on for BaseColor.
- Auto Generate Collision off; One Convex Hull per UCX on. Check all imported
  UCX boxes in the static mesh collision viewer.
- Generate Lightmap UVs off for the dynamic-lighting delivery. UV0 is the
  texture channel; no authored lightmap channel is delivered.
- Build Nanite off. Disable Auto Compute LOD Distances and begin with screen
  sizes 1.0, 0.5, 0.25, 0.125. These are project starting values, not measured
  vanilla thresholds; tune them in the game at the target resolution.

After import, verify centimeter dimensions, orientation, pivots, tangent
shading, texture color spaces, paint swatches and finishes, LOD transitions,
collision, and socket transforms. Place actual `UFGPowerConnectionComponent`
components at the marker transforms in the buildable blueprint; an imported
socket is not an electrical connection. Author blueprint clearance separately
from traversal collision, plus hologram/snapping, descriptor, recipe,
customization and state/animation behavior.
The documented material layout is established, but current shader switches and
paint-finish behavior still need the actual editor.


The sealed transformer passed generic UE 5.6.1 import in an isolated blank
content-only project using UnrealEditor-Cmd Python with NullRHI, without
FactoryGame or Wwise modules. All 35 listed package hashes matched before and
after import. Engine readbacks matched the manifest's mesh LODs, material slots,
12 body collision hulls, five body sockets and texture settings. Four actual
StaticMeshActors were attached and saved with the prescribed transforms; the
single Body-root yaw placed the service front along +X.

The commandlet exited zero with no errors and eight retained editor ACL
compression-configuration warnings, not a warning-free result. No mesh normal,
tangent, degenerate, UV, collision or helper import warnings were observed.
This evidence does not validate rendered PBR shading, mip/gutter quality,
runtime LOD transitions, collision cooking or traversal. The Blender report's
`unreal_import_verified` flag remains separate from the engine report.

The full FactoryEditor build and FactoryGame material-context checks require
the deferred Wwise SDK.

Generic import still does not establish FactoryGame master-material behavior,
Customizer paint/finish compatibility, electrical wiring, production indicators,
clearance or hologram behavior. The earlier source-model limitations describe
the editable visualization scenes; this section defines their separate derived
delivery and the remaining engine-context boundary.
