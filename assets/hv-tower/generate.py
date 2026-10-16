#!/usr/bin/env python3
"""Generate the original EP-H16 portal transmission tower and restrained relay sequence."""
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'common'))
import epkit

VIEWS = {'hero': ((24, -35, 22), (0, 0, 7.4)),
         'service': ((-4.8, -8.2, 3.8), (0, -1.4, 1.6)),
         'orthographic': ((22, -36, 20), (0, 0, 7.4))}
args = epkit.parse_arguments(VIEWS, __doc__)
kit = epkit.Kit('EPH16_TransmissionTower')
p = epkit.standard_palette()


def beam(name, start, end, width, depth, surface):
    """Add a beveled box member from `start` to `end`."""
    direction = Vector(end) - Vector(start)
    obj = kit.box(name, (Vector(start)+Vector(end))/2, (width, depth, direction.length), surface, 0.035)
    obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    return obj


def joint(name, x, y, z, width=0.72):
    """Add a bolted gusset plate centered at (x, y, z)."""
    kit.box(name+' gusset', (x,y,z), (width,0.1,0.72), p.steel, 0.035)
    for dx in (-width*0.3,width*0.3):
        for dz in (-0.22,0.22):
            kit.cylinder(name+' structural bolt', (x+dx,y-0.075,z+dz), 0.055,0.06,p.graphite,6,(0,1,0))


# Four splayed legs, joined by only three braced bays, carry the wide portal head.
for side in (-1,1):
    for front in (-1,1):
        x,y = side*2.8,front*1.9
        kit.box('Independent foundation shoe',(x,y,0.18),(1.3,1.3,0.36),p.graphite,0.08)
        kit.box('Anchor bearing plate',(x,y,0.41),(1.04,1.04,0.14),p.steel,0.035)
        for dx in (-0.37,0.37):
            for dy in (-0.37,0.37):
                kit.cylinder('Foundation anchor',(x+dx,y+dy,0.52),0.075,0.1,p.steel,6)
        beam('Primary splayed portal leg',(x,y,0.48),(side*1.65,front*0.72,12.9),0.42,0.42,p.graphite)
        beam('Orange lower impact shield',(x,y,0.6),(side*2.58,front*1.67,2.9),0.59,0.59,p.orange)
# Brace nodes follow the taper of the primary legs.
for ysign in (-1,1):
    for lower,upper in ((3.0,6.2),(6.2,9.4),(9.4,12.6)):
        t0,t1=(lower-0.48)/12.42,(upper-0.48)/12.42
        x0,x1=2.8-1.15*t0,2.8-1.15*t1
        y0,y1=ysign*(1.9-1.18*t0),ysign*(1.9-1.18*t1)
        beam('Portal diagonal brace',(-x0,y0,lower),(x1,y1,upper),0.19,0.23,p.tank)
        beam('Portal opposite diagonal',(x0,y0,lower),(-x1,y1,upper),0.19,0.23,p.tank)
        beam('Horizontal bay tie',(-x0,y0,lower),(x0,y0,lower),0.22,0.25,p.graphite)
        for sign in (-1,1):
            joint('Bay load node',sign*x0,y0-0.14,lower)
for side in (-1,1):
    for z in (3.0,9.4,12.6):
        t=(z-0.48)/12.42
        x,y=side*(2.8-1.15*t),1.9-1.18*t
        beam('Transverse depth tie',(x,-y,z),(x,y,z),0.23,0.25,p.graphite)
    beam('Side depth diagonal',(side*2.57,-1.66,3),(side*1.97,1.05,9.4),0.16,0.18,p.steel)
# The broad double-chord head has credible diagonals and orange protective ends.
for y in (-0.73,0.73):
    beam('Lower transmission crosshead',(-5.45,y,12.8),(5.45,y,12.8),0.4,0.38,p.graphite)
    beam('Upper transmission crosshead',(-4.1,y,15.0),(4.1,y,15.0),0.32,0.34,p.graphite)
    for side in (-1,1):
        beam('Head compression diagonal',(side*5.45,y,12.8),(side*1.65,y,15.0),0.28,0.28,p.steel)
        beam('Head crown upright',(side*1.65,y,12.7),(side*1.65,y,15.15),0.31,0.31,p.graphite)
        kit.box('Orange portal crown armor',(side*1.65,y,14.7),(0.57,0.55,1.28),p.orange,0.065)
        kit.box('Orange crosshead tip',(side*5.35,y,12.8),(0.58,0.59,0.55),p.orange,0.055)
        joint('Crosshead bolted node',side*1.65,y-0.22,12.8,0.9)
for x in (-4.8,-1.65,1.65,4.8):
    beam('Crosshead depth spacer',(x,-0.73,12.8),(x,0.73,12.8),0.25,0.25,p.graphite)
# Three widely separated ceramic strings hang below their supporting crossheads.
for identifier,x,top in [('A',-4.8,12.6),('B',0,14.8),('C',4.8,12.6)]:
    if identifier=='B':
        beam('Central crown support',(0,-0.73,15),(0,0.73,15),0.3,0.3,p.graphite)
    kit.torus('Suspension clevis upper '+identifier,(x,0,top),0.16,0.055,p.steel,(math.pi/2,0,0))
    kit.cylinder('Hanging ceramic core '+identifier,(x,0,top-1.25),0.14,2.12,p.ceramic)
    for index in range(10):
        kit.cylinder('HV deep ceramic shed '+identifier,(x,0,top-0.3-index*0.2),0.34,0.085,p.ceramic)
    kit.cylinder('Suspension lower yoke '+identifier,(x,0,top-2.38),0.12,0.35,p.steel)
    kit.torus('Conductor suspension eye '+identifier,(x,0,top-2.65),0.22,0.07,p.steel,(math.pi/2,0,0))
    kit.socket('CableSocket_HV_'+identifier,(x,0,top-2.65))
# Ground-level relay cabinet and linkage are operational details, not rotating tower parts.
kit.box('Relay plinth',(0,-1.62,0.19),(2.4,1.1,0.38),p.graphite,0.06)
kit.box('Orange protection cabinet',(0,-1.6,1.36),(1.75,0.66,2.0),p.orange,0.09)
kit.box('Cabinet dark door',(0,-1.96,1.4),(1.48,0.09,1.7),p.graphite,0.055)
kit.text('Equipment identity','EP / H16',(-0.6,-2.016,1.98),0.2,p.white)
kit.text('Cabinet role','LINE PROTECTION',(-0.6,-2.016,1.72),0.105,p.white)
kit.text('Service warning','ISOLATE BEFORE ACCESS',(-0.6,-2.016,0.69),0.085,p.yellow)
kit.box('Switch position plate',(0.32,-2.03,1.1),(0.47,0.05,0.48),p.steel,0.035)
kit.cylinder('Switch hub',(0.32,-2.08,1.1),0.09,0.06,p.rubber,32,(0,1,0))
pivot=kit.empty('HV_BaseIsolation_HandlePivot',(0.32,-2.1,1.1))
epkit.attach(kit.box('HV_BaseIsolation_Handle',(0.32,-2.15,1.28),(0.1,0.1,0.45),p.orange,0.025),pivot)
for x in (-0.72,0.72):
    for z in (0.85,1.85):
        kit.cylinder('Cabinet captive screw',(x,-2.025,z),0.035,0.03,p.steel,6,(0,1,0))
kit.pipe('Bonded cabinet conduit',[(0.7,-1.6,0.45),(1.25,-1.62,0.18),(2.0,-1.66,0.13),(2.5,-1.68,0.25)],0.055,p.rubber)
status=epkit.material('HV | relay state',(0.06,0.95,0.34),emission=3)
kit.cylinder('Cabinet relay lamp',(-0.45,-2.04,1.1),0.11,0.04,status,24,(0,1,0))
kit.box('Head relay beacon support',(0,-0.95,13.07),(0.8,0.8,0.18),p.graphite,0.03)
kit.cylinder('Head relay beacon lens',(0,-0.95,13.32),0.28,0.36,status)
kit.cylinder('Head beacon protective cap',(0,-0.95,13.55),0.34,0.1,p.graphite)
readout_location=(-0.6,-2.016,1.5)
energized=kit.text('Relay readout ENERGIZED','ENERGIZED',readout_location,0.105,p.cyan)
kit.configure_render(args.samples,args.width)
kit.build_studio(p.steel)
kit.orthographic_scale=25
for obj in kit.studio.objects:
    if obj.name=='Studio floor':
        obj.dimensions=(2000,2000,0.2)
    if obj.name=='Display foundation':
        obj.scale.x=8/4.6
        obj.scale.y=8/4.6
    if obj.name.startswith('Foundation edge inlay'):
        obj.hide_render=True
    if obj.type=='LIGHT':
        obj.location*=3.6
        obj.data.energy*=12.96
        obj.data.size*=3.6
if args.animate or args.render_animation:
    kit.set_timeline(12,60,[('ENERGIZED',1),('WARNING',17),('ISOLATING',30),('ISOLATED',37)])
    epkit.key_rotation(pivot,1,[(1,0),(29,0),(37,-math.pi/2),(60,-math.pi/2)],'HV base isolation handle')
    epkit.key_emission(status,[(1,(0.06,0.95,0.34,1),3),(16,(0.06,0.95,0.34,1),3),(17,(1,0.48,0.02,1),4),(29,(1,0.48,0.02,1),4),(37,(0.05,0.12,0.16,1),0),(60,(0.05,0.12,0.16,1),0)],'HV protection state')
    states=[
        (energized,1,16),
        (kit.text('Relay readout WARNING','WARNING',readout_location,0.105,p.yellow),17,36),
        (kit.text('Relay readout ISOLATED','ISOLATED',readout_location,0.105,p.white),37,60),
    ]
    for obj,start,end in states:
        epkit.key_state_window(obj,start,end,(1,16,17,29,30,36,37,60),'HV relay readout '+obj.name.split()[-1])
    kit.scene.frame_set(1)
kit.export_metrics(ROOT/'metrics.json',args.samples)
kit.render_stills(ROOT/'renders',VIEWS,args.views,ROOT/'hv-tower.blend')
if args.render_animation:
    kit.render_animation(ROOT/'renders'/'animation',VIEWS['hero'],args.animation_width,args.animation_samples)
print('ASSET_RENDER_COMPLETE',flush=True)
