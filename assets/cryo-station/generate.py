#!/usr/bin/env python3
"""Generate the original EP-C8 superconducting link cooler and operating study."""
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'common'))
import epkit

VIEWS = {
    'hero': ((9, -12, 8.3), (0, 0, 1.75)),
    'service': ((-9, -10, 7.2), (0, -0.3, 1.65)),
    'orthographic': ((8, -11, 8), (0, 0, 1.7)),
}
arguments = epkit.parse_arguments(VIEWS, __doc__)
kit = epkit.Kit('EPC8_CryoStation')
p = epkit.standard_palette()
box, cylinder, pipe, text, torus = kit.box, kit.cylinder, kit.pipe, kit.text, kit.torus


def bolt(location, direction=(0, -1, 0)):
    """Add a captive hex flange bolt."""
    cylinder('Captive flange bolt', location, 0.04, 0.035, p.steel, 6, direction)


# A low, long equipment skid gives this cooler a different silhouette from the transformer.
for x in (-1.55, 1.55):
    box('Graphite longitudinal skid', (x, 0, 0.2), (0.28, 6.9, 0.4), p.graphite, 0.055)
for y in (-3.25, -1.9, 1.9, 3.25):
    box('Structural crossmember', (0, y, 0.24), (3.65, 0.28, 0.32), p.graphite)
    for x in (-1.55, 1.55):
        box('Anchor shoe', (x, y, 0.09), (0.62, 0.52, 0.18), p.steel)
        bolt((x, y, 0.19), (0, 0, 1))
box('Equipment drip deck', (0, 0, 0.44), (3.4, 6.55, 0.12), p.tank)
for y in (-2.05, 2.05):
    for x in (-1.5, 1.5):
        box('Portal graphite upright', (x, y, 1.87), (0.23, 0.34, 2.95), p.graphite)
        box('Replaceable orange shoulder', (x, y, 2.43), (0.39, 0.46, 1.58), p.orange, 0.085)
        bolt((x, y-0.245, 1.9))
        bolt((x, y-0.245, 3.0))
    box('Orange overhead portal', (0, y, 3.32), (3.39, 0.46, 0.32), p.orange, 0.075)
    box('Portal underside reinforcement', (0, y, 3.1), (2.8, 0.23, 0.15), p.graphite)
for x in (-1.52, 1.52):
    box('Upper graphite longitudinal tie', (x, 0, 3.16), (0.16, 3.9, 0.18), p.graphite)

# Vacuum-insulated longitudinal bus vessel joins the two obvious SC terminations.
cylinder('Vacuum cryostat outer jacket', (-0.45, 0, 2.13), 0.67, 4.85, p.steel, 64, (0, 1, 0))
for y in (-1.75, 0, 1.75):
    cylinder('Cryostat segmented thermal collar', (-0.45, y, 2.13), 0.705, 0.16, p.ceramic, 48, (0, 1, 0))
    if y:
        box('Cryostat saddle foot', (-0.45, y, 1.0), (1.3, 0.28, 1.0), p.graphite)
for side, sign in [('In', -1), ('Out', 1)]:
    y = sign * 2.8
    cylinder('SC '+side+' armored end module', (-0.45, y, 2.13), 0.76, 0.62, p.graphite, 64, (0, 1, 0))
    cylinder('SC '+side+' orange locking collar', (-0.45, sign*3.04, 2.13), 0.72, 0.19, p.orange, 48, (0, 1, 0))
    cylinder('SC '+side+' pale vacuum feedthrough', (-0.45, sign*3.27, 2.13), 0.49, 0.32, p.ceramic, 48, (0, 1, 0))
    cylinder('SC '+side+' cyan identification band', (-0.45, sign*3.37, 2.13), 0.505, 0.06, p.cyan, 48, (0, 1, 0))
    cylinder('SC '+side+' cable coupling', (-0.45, sign*3.51, 2.13), 0.39, 0.18, p.steel, 48, (0, 1, 0))
    cylinder('SC '+side+' recessed cable port', (-0.45, sign*3.608, 2.13), 0.28, 0.018, p.rubber, 48, (0, 1, 0))
    for angle in range(0, 360, 60):
        a = math.radians(angle)
        bolt((-0.45+0.59*math.cos(a), sign*3.15, 2.13+0.59*math.sin(a)), (0, 1, 0))
    kit.socket('CableSocket_SC_'+side, (-0.45, sign*3.63, 2.13))
    box('Terminal plaque stand', (-0.45, sign*3.13, 0.74), (0.16, 0.06, 0.48), p.graphite)
    box('Terminal identification plaque', (-0.45, sign*3.13, 1.13), (1.1, 0.07, 0.31), p.graphite)
    text('Terminal SC '+side, 'SC / '+side.upper(), (-0.89 if sign<0 else -0.05, sign*3.175, 1.05), 0.16, p.white, '-Y' if sign<0 else '+Y')

# An exposed fin stack and guarded twin fans reject compressor heat on the right flank.
box('Heat exchanger core', (1.05, 0, 1.62), (0.63, 2.9, 1.72), p.graphite, 0.05)
for index in range(27):
    box('Aluminium exchanger plate', (1.13, -1.32+index*0.102, 1.62), (0.73, 0.025, 1.58), p.steel, 0.006)
rotors = []
for identifier, y in [('A', -0.73), ('B', 0.73)]:
    center = (1.53, y, 1.65)
    cylinder('Fixed fan duct '+identifier, center, 0.65, 0.2, p.graphite, 64, (1, 0, 0))
    cylinder('Fan dark recess '+identifier, (1.64, y, 1.65), 0.56, 0.025, p.rubber, 48, (1, 0, 0))
    pivot = kit.empty('HeatRejectionFan_'+identifier, (1.71, y, 1.65))
    rotors.append(pivot)
    epkit.attach(cylinder('Fan hub '+identifier, (1.71, y, 1.65), 0.16, 0.12, p.steel, 32, (1, 0, 0)), pivot)
    for index in range(7):
        a = index*math.tau/7
        blade = box('Pitched fan blade '+identifier, (1.71, y+0.31*math.cos(a), 1.65+0.31*math.sin(a)), (0.065, 0.46, 0.13), p.tank, 0.025)
        blade.rotation_euler = (Matrix.Rotation(a, 4, 'X') @ Matrix.Rotation(0.35, 4, 'Y')).to_euler()
        epkit.attach(blade, pivot)
    for radius in (0.27, 0.43, 0.59):
        torus('Stationary finger guard '+identifier, (1.79, y, 1.65), radius, 0.017, p.steel, (0, math.pi/2, 0), 48, 8)
    for a in (0, math.pi/3, 2*math.pi/3):
        pipe('Guard radial strut', [(1.79,y-0.59*math.cos(a),1.65-0.59*math.sin(a)),(1.79,y+0.59*math.cos(a),1.65+0.59*math.sin(a))], 0.018, p.graphite)
for y in (-1.53, 1.53):
    box('Exchanger orange end cheek', (1.12, y, 1.7), (1.05, 0.15, 2.0), p.orange, 0.055)

# Compressor, insulated coolant manifold and accessible utility coupling on the service flank.
cylinder('Compressor motor', (-0.78, 0.25, 0.99), 0.36, 1.4, p.graphite, 48, (0, 1, 0))
for y in (-0.32, -0.18, -0.04, 0.1, 0.24, 0.38, 0.52, 0.66):
    cylinder('Compressor motor fin', (-0.78, y, 0.99), 0.39, 0.045, p.tank, 32, (0, 1, 0))
cylinder('Scroll compressor housing', (-0.78, -0.65, 1.04), 0.46, 0.42, p.steel, 48, (0, 1, 0))
box('Compressor mounting rail', (-0.78, -0.05, 0.56), (0.7, 1.75, 0.12), p.graphite)
for y in (-1.45, 1.45):
    pipe('Insulated coolant circulation loop', [(-0.55,y,2.68),(-1.23,y,2.9),(-1.38,y,2.6),(-1.38,y,1.3),(-0.82,math.copysign(0.95,y),1.0)], 0.14, p.steel)
    for z in (1.5, 1.95, 2.4):
        cylinder('Pale insulation jacket', (-1.38, y, z), 0.165, 0.33, p.ceramic)
        cylinder('Insulation cyan seam', (-1.38, y, z-0.16), 0.172, 0.035, p.cyan)
pipe('Coolant inlet manifold', [(-1.85,-1.45,1.1),(-1.38,-1.45,1.1),(-1.05,-0.65,1.1)], 0.115, p.steel)
cylinder('Coolant coupling flange', (-1.79,-1.45,1.1), 0.23, 0.17, p.orange, 40, (1,0,0))
cylinder('Coolant coupling bore', (-1.885,-1.45,1.1), 0.12, 0.025, p.rubber, 32, (1,0,0))
kit.socket('CoolantSocket', (-1.9,-1.45,1.1))
box('Coolant label backing', (-1.55,-1.45,0.66), (0.08,1.08,0.32), p.graphite)
text('Generic coolant label', 'COOLANT', (-1.6,-1.05,0.53), 0.145, p.white, '-X')
# The quarter-turn lever is animated about the vertical valve stem.
cylinder('Isolation valve body', (-1.38,-1.45,1.23), 0.19, 0.28, p.graphite)
cylinder('Isolation valve spindle', (-1.38,-1.45,1.47), 0.045, 0.28, p.steel)
valve = kit.empty('CoolantIsolationValve', (-1.38,-1.45,1.64))
epkit.attach(box('Valve quarter-turn lever', (-1.38,-1.45,1.64), (0.52,0.09,0.07), p.orange), valve)
epkit.attach(box('Valve position pointer', (-1.16,-1.45,1.7), (0.06,0.14,0.05), p.white), valve)

# A narrow protected flow meter is instrumentation, not an exposed glowing energy core.
box('Flow meter armored backing', (-1.18,0,2.13), (0.12,1.35,0.27), p.graphite)
flow_materials = []
for index in range(8):
    surface = epkit.material('Flow meter segment '+str(index), (0.12,0.72,0.79), 0.25, 0.24, 1)
    flow_materials.append(surface)
    box('Protected coolant flow segment', (-1.253,-0.55+index*0.16,2.13), (0.025,0.11,0.11), surface, 0.008)
for z in (2.0,2.26):
    box('Flow meter guard rail', (-1.27,0,z), (0.07,1.4,0.04), p.steel)

# Controls face the front with a second side-facing state repeater.
box('Front service enclosure', (0.89,-2.62,1.25), (1.06,0.55,1.5), p.orange, 0.075)
box('Removable service access door', (0.89,-2.915,1.27), (0.88,0.06,1.26), p.graphite, 0.04)
box('Status display recessed bezel', (0.89,-2.96,1.57), (0.8,0.04,0.5), p.rubber)
text('EP equipment branding','EP / C8', (0.52,-2.965,1.04),0.15,p.white)
text('Equipment function','LINK COOLER', (0.52,-2.965,0.85),0.095,p.white)
for z in (0.78,1.73):
    bolt((0.54,-2.96,z))
    bolt((1.24,-2.96,z))
box('Service side repeater backing', (-1.55,-0.15,0.66), (0.08,1.4,0.32), p.graphite)
state_specs = [('STARTUP',1,10),('COOLING',11,22),('READY',23,36),('COOLANT LOST',37,46),('SAFE SHUTDOWN',47,60)]
frames = list(range(1,61))
for label,start,end in state_specs:
    surface = p.yellow if label in ('STARTUP','COOLANT LOST') else p.cyan if label=='COOLING' else p.green if label=='READY' else p.white
    front = text('Front state '+label,label,(0.53,-2.99,1.57),0.079,surface)
    side = text('Service state '+label,label,(-1.6,0.36,0.64),0.105,surface,'-X')
    if arguments.animate or arguments.render_animation:
        for obj in (front,side):
            epkit.key_state_window(obj,start,end,frames,'Readout_'+label.replace(' ','_'))
    else:
        front.hide_render = side.hide_render = label!='READY'
text('Front portal equipment stencil','EP / SUPERCONDUCTING LINK',(-1.26,-2.292,3.25),0.11,p.rubber)
box('Service access tread', (0.8,-3.17,0.49), (1.3,0.48,0.14), p.graphite)
for index in range(9):
    box('Step traction rib',(0.3+index*0.125,-3.17,0.57),(0.025,0.36,0.018),p.steel,0.003)
box('Access threshold warning',(0.8,-3.415,0.5),(1.25,0.025,0.08),p.yellow,0.004)

kit.configure_render(arguments.samples, arguments.width)
kit.build_studio(p.steel)
for obj in kit.studio.objects:
    if obj.name == 'Display foundation':
        obj.dimensions = (4.6,8.1,0.13)
    elif obj.name.startswith('Foundation edge inlay'):
        obj.dimensions.y = 7.8
# Framing reflects the long 4 x 8 m station rather than the shared square transformer.
kit.orthographic_scale = 10.6
if arguments.animate or arguments.render_animation:
    kit.set_timeline(12,60,[(label.replace(' ','_'),start) for label,start,end in state_specs])
    for pivot in rotors:
        epkit.key_rotation(pivot,0,[(1,0),(10,1),(22,12),(36,35),(46,48),(54,51),(60,51)],'FanRamp_Run_Coast_'+pivot.name)
    epkit.key_rotation(valve,2,[(1,math.pi/2),(10,0),(36,0),(40,0),(47,math.pi/2),(60,math.pi/2)],'Coolant_Open_Isolate')
    for index,surface in enumerate(flow_materials):
        keys = []
        for frame in frames:
            active = 11<=frame<=36
            bright = active and (frame//2-index)%8<3
            color = (0.12,0.72,0.79,1) if active else (0.025,0.07,0.08,1)
            keys.append((frame,color,3.0 if bright else 0.25 if active else 0))
        epkit.key_emission(surface,keys,'CoolantFlow_'+str(index))
    kit.scene.frame_set(28)
kit.export_metrics(ROOT/'metrics.json',arguments.samples)
kit.render_stills(ROOT/'renders',VIEWS,arguments.views,ROOT/'cryo-station.blend')
if arguments.render_animation:
    kit.render_animation(ROOT/'renders'/'animation',VIEWS['hero'],arguments.animation_width,arguments.animation_samples)
print('ASSET_RENDER_COMPLETE',flush=True)
