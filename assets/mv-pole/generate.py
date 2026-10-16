#!/usr/bin/env python3
"""Generate the original EP-M6 regional distribution pole and operating previews."""
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'common'))
import epkit

VIEWS = {'hero': ((11, -16, 10), (0, 0, 3.5)),
         'service': ((-10, 15, 9), (0, 0, 3.5)),
         'orthographic': ((9, -15, 9), (0, 0, 3.5))}
READOUT_LOCATION = (-0.31, -0.746, 1.61)
args = epkit.parse_arguments(VIEWS, __doc__)
kit = epkit.Kit('EPM6_DistributionPole')
p = epkit.standard_palette()


def beam(name, start, end, width, depth, surface):
    """Add a beveled box member from `start` to `end`."""
    direction = Vector(end) - Vector(start)
    obj = kit.box(name, (Vector(start) + Vector(end)) / 2, (width, depth, direction.length), surface, 0.025)
    obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    return obj


kit.box('Armored foundation shoe', (0, 0, 0.14), (1.8, 1.8, 0.28), p.graphite, 0.09)
kit.box('Raised mast plinth', (0, 0, 0.42), (1.15, 1.15, 0.42), p.steel, 0.07)
for x in (-0.69, 0.69):
    for y in (-0.69, 0.69):
        kit.cylinder('Foundation captive bolt', (x, y, 0.31), 0.08, 0.08, p.steel, 6)
kit.box('Structural mast lower', (0, 0, 2.1), (0.64, 0.7, 3.5), p.graphite, 0.065)
kit.box('Telescoping upper mast', (0, 0, 4.925), (0.43, 0.48, 2.55), p.tank, 0.045)
for z in (0.8, 3.65, 6.15):
    kit.box('Mast clamp collar', (0, 0, z), (0.78 if z < 4 else 0.58, 0.82 if z < 4 else 0.62, 0.15), p.steel, 0.025)
for x in (-0.43, 0.43):
    kit.extrusion('Orange folded base cheek', [(x-0.09, 0.45), (x+0.09, 0.45), (x+0.09, 2.8), (x-0.09, 3.05)], (-0.4, 0.4), p.orange, 0.035)
kit.box('Service orange band', (0, 0, 2.68), (0.86, 0.88, 0.48), p.orange, 0.055)
kit.text('Mast class stencil', 'EP / MV', (-0.31, -0.452, 2.64), 0.14, p.graphite)
# Raised side terminals leave a clear upper cable corridor above the service equipment.
for identifier, x, z in [('A', -1.28, 6.2), ('B', 1.28, 6.2), ('C', 0, 7.0)]:
    if x:
        beam('Crossarm structural outrigger', (0, 0, 5.4), (x, 0, 5.4), 0.22, 0.36, p.graphite)
        beam('Crossarm knee brace', (0, 0, 4.65), (x, 0, 5.4), 0.12, 0.17, p.steel)
        kit.box('Orange crossarm end cap', (x, 0, 5.4), (0.3, 0.43, 0.28), p.orange, 0.04)
    bottom = z - 0.78
    kit.cylinder('Terminal mounting flange '+identifier, (x, 0, bottom), 0.22, 0.1, p.steel)
    kit.cylinder('Ceramic terminal core '+identifier, (x, 0, z-0.39), 0.11, 0.7, p.ceramic)
    for index in range(5):
        kit.cylinder('MV ceramic shed '+identifier, (x, 0, bottom+0.1+index*0.12), 0.21-index*0.009, 0.055, p.ceramic)
    kit.cylinder('Conductor terminal neck '+identifier, (x, 0, z-0.03), 0.08, 0.16, p.copper)
    kit.torus('Conductor attachment eye '+identifier, (x, 0, z+0.11), 0.115, 0.037, p.steel, (math.pi/2, 0, 0))
    kit.socket('CableSocket_MV_'+identifier, (x, 0, z+0.11))
kit.box('Control enclosure orange shell', (0, -0.47, 1.62), (0.98, 0.42, 1.18), p.orange, 0.07)
kit.box('Recessed sealed control door', (0, -0.7, 1.63), (0.82, 0.07, 0.98), p.graphite, 0.045)
kit.text('Panel identity', 'EP-M6', (-0.31, -0.744, 1.92), 0.14, p.white)
kit.text('Circuit identifier', 'REGIONAL / MV', (-0.31, -0.744, 1.73), 0.075, p.white)
kit.text('Safety legend', 'ISOLATE TO SERVICE', (-0.31, -0.744, 1.19), 0.055, p.white)
kit.cylinder('Switch escutcheon', (0.05, -0.76, 1.35), 0.1, 0.04, p.steel, 32, (0, 1, 0))
kit.cylinder('Switch hub', (0.05, -0.79, 1.35), 0.06, 0.04, p.rubber, 32, (0, 1, 0))
pivot = kit.empty('BaseIsolation_HandlePivot', (0.05, -0.81, 1.35))
epkit.attach(kit.box('BaseIsolation_OrangeHandle', (0.05, -0.84, 1.45), (0.07, 0.07, 0.27), p.orange, 0.02), pivot)
for z in (1.25, 1.9):
    kit.box('Door hinge', (-0.42, -0.75, z), (0.06, 0.05, 0.13), p.steel)
kit.pipe('Sealed relay conduit', [(0.28, -0.43, 1.1), (0.28, -0.4, 0.85), (0.2, -0.23, 0.65)], 0.035, p.rubber)
# Two linked beacons make the restrained relay state readable at pole and service distance.
status = epkit.material('MV | relay status', (0.06, 0.95, 0.34), emission=3)
kit.cylinder('Panel relay lamp', (-0.23, -0.76, 1.47), 0.065, 0.04, status, 24, (0, 1, 0))
kit.box('Upper beacon mounting bracket', (0, -0.32, 5.93), (0.36, 0.58, 0.1), p.graphite)
kit.cylinder('Upper beacon guard', (0, -0.48, 6.01), 0.22, 0.12, p.graphite)
kit.cylinder('Upper relay status lens', (0, -0.48, 6.14), 0.19, 0.14, status)
energized = kit.text('Panel state ENERGIZED', 'ENERGIZED', READOUT_LOCATION, 0.068, p.cyan)
kit.configure_render(args.samples, args.width)
kit.build_studio(p.steel)
kit.orthographic_scale = 11.0
for obj in kit.studio.objects:
    if obj.name == 'Studio floor':
        obj.dimensions = (2000, 2000, 0.2)
    if obj.type == 'LIGHT':
        obj.location *= 1.8
        obj.data.energy *= 3.24
        obj.data.size *= 1.8
if args.animate or args.render_animation:
    kit.set_timeline(12, 60, [('ENERGIZED', 1), ('WARNING', 17), ('ISOLATING', 30), ('ISOLATED', 37)])
    epkit.key_rotation(pivot, 1, [(1, 0), (29, 0), (37, -math.pi/2), (60, -math.pi/2)], 'MV base isolation handle')
    epkit.key_emission(status, [(1, (0.06, 0.95, 0.34, 1), 3), (16, (0.06, 0.95, 0.34, 1), 3), (17, (1, 0.48, 0.02, 1), 4), (29, (1, 0.48, 0.02, 1), 4), (37, (0.05, 0.12, 0.16, 1), 0), (60, (0.05, 0.12, 0.16, 1), 0)], 'MV relay state')
    states = [
        (energized, 1, 16),
        (kit.text('Panel state WARNING', 'WARNING', READOUT_LOCATION, 0.068, p.yellow), 17, 36),
        (kit.text('Panel state ISOLATED', 'ISOLATED', READOUT_LOCATION, 0.068, p.white), 37, 60),
    ]
    for obj, start, end in states:
        epkit.key_state_window(obj, start, end, (1, 16, 17, 29, 30, 36, 37, 60), 'MV readout ' + obj.name.split()[-1])
    kit.scene.frame_set(1)
kit.export_metrics(ROOT / 'metrics.json', args.samples)
kit.render_stills(ROOT / 'renders', VIEWS, args.views, ROOT / 'mv-pole.blend')
if args.render_animation:
    kit.render_animation(ROOT / 'renders' / 'animation', VIEWS['hero'], args.animation_width, args.animation_samples)
print('ASSET_RENDER_COMPLETE', flush=True)
