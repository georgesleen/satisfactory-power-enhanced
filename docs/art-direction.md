# Equipment art direction

## Identity

Make full-size FICSIT-compatible equipment, not a scale model.
Keep the bold silhouette, amber armor, graphite structure, grey service panels,
exposed mechanisms and small cyan displays of Satisfactory buildings.
Keep the source footprint, sockets and moving parts.
Use original meshes, labels and surface patterns. Do not copy game art or logos.
Do not replace stylization with photorealism, rust, dirt or random detail.

## Shape and fabrication

Author in meters. Use these edge breaks, not one radius on all parts:

| Part | Bevel width | Example |
| --- | --- | --- |
| Sheet and plate edges | min(2 mm, 8% of thickness) | Covers, fins, flange plates |
| Fabricated parts | min(12 mm, 8% of smallest dimension) | Tank, cabinet, beams |
| Cast parts | min(25 mm, 8% of smallest dimension) | Cast feet and housings |
| Fasteners | 4.5% of nominal bolt diameter | M16 head: 0.72 mm |

Keep large flat faces flat. Keep deliberate formed corners separate from edge
breaks. Do not round a thin lid through half its thickness.
Use 1 to 3 bevel segments. Prefer a clear highlight to a pill-shaped edge.

Use open steel sections where the load path is visible:

- Skid I-beam: 300 x 380 mm, 18 mm web and flanges.
- Skid cross channel: 280 x 280 mm, 16 mm plate.
- Small bracket angle: 80 x 80 x 6 mm.
- Tank stiffener channel: 60 x 70 x 6 mm.
- Folded guards: 12 to 30 mm visual sheet thickness.
- Plate shoes: 25 to 40 mm. Show anchors and a supported vertical web.
- Cable attachment eyes: outer diameter 40 to 50% of the terminal cap diameter.
- Open guards and hoods: show at least two standoffs or gussets per panel.
- Grated stairs: show load-bearing stringers, landing ties and feet.

Use pipes for fluid and cable routes. Do not use round bars for all structure.
Let medium details explain joints, service access, cooling and support.
No plain single-material face may exceed 1.5 x 1.5 m without a seam, stiffener,
plate or fitting. A large tank side and lid must each show at least three
distinct medium-size features. Use functional details, not random surface noise.

## Materials

Base colors below are sRGB bytes, not scene-linear values.
Convert with `epkit.srgb`. AgX and daylight alter the displayed color.
Do not sample a lit image and use that number as a linear shader color.

| Material | sRGB | Roughness | Metallic |
| --- | --- | --- | --- |
| Painted primary amber | 226, 139, 48 | 0.39 to 0.53 | 0 |
| Painted secondary grey | 172, 181, 184 | 0.41 to 0.55 | 0 |
| Painted graphite structure | 55, 64, 70 | 0.45 to 0.59 | 0 |
| Painted tank charcoal | 78, 91, 96 | 0.42 to 0.56 | 0 |
| Bare galvanized steel | 163, 174, 180 | 0.36 to 0.50 | 1 |
| Bare dark steel | 66, 74, 79 | 0.49 to 0.63 | 1 |
| Rubber | 24, 29, 31 | 0.69 to 0.83 | 0 |
| Glazed grey ceramic | 171, 175, 164 | 0.13 to 0.27 | 0 |
| Copper | 176, 107, 67 | 0.25 to 0.39 | 1 |
| Hazard yellow | 235, 185, 42 | 0.55 | 0 |
| Stencil ivory | 218, 224, 215 | 0.58 | 0 |

Paint is a dielectric coating over metal. Keep the broad painted faces at zero
metallic. Expose metal only at narrow wear edges. Use restrained roughness
variation, not a uniform satin finish. Keep galvanized spangle near 10 mm.
Give ceramic a smooth clear glaze. Keep rubber matte and copper warm.

Target 15 to 25% light-grey or silver area on visible equipment surfaces.
Use secondary grey on skid top rails and cabinet frames. Use galvanized steel
on handrail posts, flange rings and brackets. Keep amber armor distinct from
charcoal pressure vessels. Do not make every structural member dark.

## Surface and scale

- Add panel gaps of 6 to 10 mm at removable covers and folded armor joints.
- Use welded stiffeners on pressure vessels, not decorative fake panel gaps.
- Use M12 to M20 service fasteners. M16 hex heads are about 28 mm across corners.
  Use M24 foundation anchors. Do not put 70 mm heads on cabinet doors.
- Use 45 to 65 mm vent or radiator pitch. Keep radiator sheet thin.
- Put conduit clamps, brackets and glands at supported routes and terminations.
- Put black/yellow hazards at steps, pinch points and energized access points.
  Do not stripe every perimeter.
- Keep equipment class labels readable at building distance. Use 50 to 100 mm
  text on large equipment, 20 to 50 mm on service plates.
- Seat labels, plaques and fastener washers on the face they mount to.
  Keep the gap under 2 mm. A sun shadow shows a larger gap as a double image.
  Move them again when a plate thickness changes.
- Use a narrow 1.8 mm shader edge-wear radius with at most 32% bare-metal blend.
  Do not cover panels in scratches.
- Fade ground grime from 13% at Z = 0.12 m to zero at Z = 1 m.
  Keep the silhouette and paint color clear. Do not add global brown grunge.

Human-scale dimensions:

| Feature | Dimension |
| --- | --- |
| Scale mannequin | 1.8 m high |
| Handrail | 1.1 m above landing, 42.4 mm tube |
| Knee rail | 0.55 m above landing |
| Ladder | 450 mm clear width, 300 mm rung pitch, 25 mm rungs |
| Walk-in access door | About 0.9 x 2 m |
| Cabinet door | Fit the equipment, not a walk-in door |
| Step rise | 150 to 200 mm |
| Grating | 5 mm bars at 35 mm pitch, 100 mm cross ties |

Add a ladder or walk-in door only where the function needs it.
Do not turn a sealed transformer tank into an occupied room.

## Presentation

Use a foundation-like ground plane, not a small display plinth.
Use 8 m tiles with 20 mm seams and faint 1 m subdivisions with 6 mm lines.
The pattern is original. It is not a game texture.
Use sunny daylight with a visible ground shadow in the hero view.
Put the sun 60 to 120 degrees in azimuth from the hero camera and 35 to 50
degrees above the ground. Show one bright face and one shaded face.
Use a 2 degree sun disk. Do not use close, building-sized softboxes.
Use a pale-blue horizon and a saturated blue zenith, not a flat grey world.
Set the sun to 3.5 and the gradient sky strength to 0.45.
Keep direct sun illumination at least four times the sky fill on a lit face.
Use AgX Medium High Contrast and +0.15 exposure. Keep the sky distinct from
the foundation. Do not lift the sky fill to remove all shadows.

Use a 40 mm lens with no depth of field. For a 4 to 5 m building, put the camera
at 3 to 3.5 m high and 10 to 12 m away. Aim near the building center.
Keep the down angle below 10 degrees for the hero and service views.
Use parallel projection only for the separate inspection view.
Show the original 1.8 m mannequin in the hero view. Exclude it from asset metrics.
Keep the figure outside the placement envelope. Do not copy the game character.

## Evidence and references

Reviewed source images:
[Constructor](https://satisfactory.wiki.gg/images/Constructor.png),
[Assembler](https://satisfactory.wiki.gg/images/Assembler.png),
[Coal-Powered Generator](https://satisfactory.wiki.gg/images/Coal-Powered_Generator.png),
[Power Storage](https://satisfactory.wiki.gg/images/Power_Storage.png),
[Power Switch](https://satisfactory.wiki.gg/images/Power_Switch.png),
[Power Tower](https://satisfactory.wiki.gg/images/Power_Tower.png),
[Nuclear Power Plant](https://satisfactory.wiki.gg/images/Nuclear_Power_Plant.png).
These are visual references, not licensed production inputs.

Constructor and Power Switch use inset doors, louvres, distinct grey panels and
small perimeter bolts. Assembler uses a ladder, rails, grated access and layered
angular frames. Coal-Powered Generator uses a legible exposed mechanism and small
service details. Power Tower uses open load paths. Power Storage and Nuclear
Power Plant break large faces with seams, braces and vents. Their edge highlights
are narrow compared with the panel sizes. Wear is restrained.

