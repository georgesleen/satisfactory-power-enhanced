#!/usr/bin/env python3
"""Generate the original EP-24 transformer and a deterministic CPU studio render set."""
import math
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'common'))
import epkit  # noqa: E402

VIEWS = {'hero': ((7, -9, 6.1), (0, 0, 1.95)), 'service': ((-5.5, 9.8, 5.8), (0, 0, 1.94)), 'orthographic': ((6, -8, 5.3), (0, 0, 2.04))}
arguments = epkit.parse_arguments(VIEWS, __doc__)
kit = epkit.Kit('EP24_Transformer')
asset = kit.asset
box, cylinder, pipe, text, torus = kit.box, kit.cylinder, kit.pipe, kit.text, kit.torus
palette = epkit.standard_palette()
orange, graphite, tank, steel = palette.orange, palette.graphite, palette.tank, palette.steel
ceramic, copper, rubber, yellow = palette.ceramic, palette.copper, palette.rubber, palette.yellow
white, cyan, green = palette.white, palette.cyan, palette.green


def bolt(location, direction=(0, -1, 0)):
    return cylinder('Captive hex bolt', location, 0.035, 0.025, steel, 6, direction)


def shoulder(name, x):
    # A thick folded shell wraps the tank shoulder, not an enclosing cube.
    profile = [(x-0.2, 0.61), (x+0.2, 0.61), (x+0.2, 2.65), (x+0.04, 2.95), (x-0.26, 2.95), (x-0.2, 2.57)]
    return kit.extrusion(name, profile, (-1.13, 1.13), orange, 0.055)


# Four-meter load-bearing skid and replaceable corner shoes.
for x in (-1.52, 1.52):
    box('Longitudinal skid beam', (x, 0, 0.24), (0.3, 3.55, 0.38), graphite, 0.055)
for y in (-1.55, 1.55):
    box('Crossmember', (0, y, 0.31), (3.6, 0.28, 0.28), graphite, 0.04)
    for x in (-1.6, 1.6):
        box('Anchor shoe', (x, y, 0.095), (0.58, 0.58, 0.19), graphite, 0.04)
        for dx in (-0.16, 0.16):
            cylinder('Foundation anchor', (x+dx, y, 0.203), 0.048, 0.035, steel, 6)
box('Bund tray', (0, 0, 0.49), (3.35, 2.85, 0.14), steel, 0.05)
box('Oil vessel', (0, 0, 1.72), (2.48, 2.15, 2.32), tank, 0.18)
box('Lid gasket', (0, 0, 2.85), (2.6, 2.23, 0.07), rubber, 0.08)
box('Pressure lid', (0, 0, 2.94), (2.65, 2.28, 0.13), graphite, 0.085)
for x in (-0.98, 0.98):
    shoulder('Folded orange shoulder armor', x)
for y in (-1.13, 1.13):
    box('Lower shell cross belt', (0, y, 0.87), (2.22, 0.1, 0.45), orange, 0.045)
    box('Upper shell cross belt', (0, y, 2.64), (2.23, 0.1, 0.24), orange, 0.04)
    for x in (-0.85, 0.85):
        for z in (0.9, 2.65):
            bolt((x, y + math.copysign(0.065, y), z), (0, y, 0))

# Ribbed cooling bank on the right flank, with joined upper and lower oil headers.
for z in (0.94, 2.48):
    pipe('Radiator header', [(1.12,-0.87,z),(1.51,-0.87,z),(1.51,0.91,z),(1.12,0.91,z)], 0.085, graphite)
for index in range(13):
    y = -0.78 + index * 0.132
    box('Pressed radiator fin', (1.56,y,1.7), (0.56,0.055,1.46), graphite, 0.022)
    box('Fin crown highlight', (1.81,y,1.7), (0.035,0.058,1.31), tank, 0.012)
for y in (-0.91, 1.0):
    box('Radiator end guard', (1.6,y,1.72), (0.64,0.1,1.83), orange, 0.04)
    for z in (1.04,2.4):
        bolt((1.6,y-0.065,z))

# Twin guarded axial fans force air through the exposed radiator bank.
fan_rotors = []
for identifier, y in [('A', -0.43), ('B', 0.43)]:
    rotor = kit.empty('CoolingFan_Rotor_' + identifier, (1.935, y, 1.72))
    fan_rotors.append(rotor)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.355, depth=0.11, end_fill_type='NOTHING', location=(1.915,y,1.72), rotation=(0,math.pi/2,0))
    duct = kit.finish(bpy.context.object, 'CoolingFan_Duct_' + identifier, graphite)
    for polygon in duct.data.polygons:
        polygon.use_smooth = True
    wall = duct.modifiers.new('Duct wall thickness', 'SOLIDIFY')
    wall.thickness = 0.03
    wall.offset = 1
    for x in (1.865, 1.97):
        kit.torus('CoolingFan_DuctLip_' + identifier, (x,y,1.72), 0.37, 0.027, graphite, (0,math.pi/2,0), 48)
    cylinder('CoolingFan_Motor_' + identifier, (1.875,y,1.72), 0.115, 0.07, graphite, 32, (1,0,0))
    for index in range(3):
        angle = math.pi/2 + index * 2 * math.pi / 3
        strut = box('CoolingFan_SpiderStrut_' + identifier, (1.875, y+0.235*math.cos(angle), 1.72+0.235*math.sin(angle)), (0.035,0.25,0.04), graphite, 0.008)
        strut.rotation_euler.x = angle
    hub = cylinder('CoolingFan_Hub_' + identifier, (0,0,0), 0.092, 0.07, steel, 32, (1,0,0))
    hub.parent = rotor
    hub.location = (0,0,0)
    for index in range(5):
        angle = index * 2 * math.pi / 5
        profile = [(0.07,-0.018), (0.29,-0.105), (0.323,-0.015), (0.14,0.073)]
        vertices = [(0.018*(radius/0.323), radius*math.cos(angle)-offset*math.sin(angle), radius*math.sin(angle)+offset*math.cos(angle)) for radius,offset in profile]
        blade = kit.mesh('CoolingFan_Blade_' + identifier, vertices, [(0,1,2,3)], orange)
        blade.parent = rotor
        blade.modifiers.new('Blade wall thickness', 'SOLIDIFY').thickness = 0.018
        bevel = blade.modifiers.new('Blade rounded edge', 'BEVEL')
        bevel.width = 0.008
        bevel.segments = 2
    for angle in (0, math.pi/2):
        dy, dz = 0.35*math.cos(angle), 0.35*math.sin(angle)
        pipe('CoolingFan_FingerGuard_' + identifier, [(1.97,y-dy,1.72-dz),(1.985,y,1.72),(1.97,y+dy,1.72+dz)], 0.012, steel)
    for z in (1.33, 2.11):
        box('CoolingFan_Mount_' + identifier, (1.83,y,z), (0.16,0.1,0.12), graphite, 0.018)

# Distinct opposed cable towers, each with one explicit attachment eye and named socket.
for side, x, top, sheds in [('HV',-1.02,4.38,7),('MV',1.0,3.89,5)]:
    cylinder(side+' turret foot', (x,0.14,3.08), 0.31,0.16,steel)
    cylinder(side+' orange pedestal', (x,0.14,3.26), 0.235,0.29,orange)
    stem_bottom = 3.4
    stem_top = top-0.19
    cylinder(side+' porcelain core', (x,0.14,(stem_bottom+stem_top)/2),0.115,stem_top-stem_bottom,ceramic)
    for index in range(sheds):
        z=stem_bottom+0.04+index*(stem_top-stem_bottom-0.07)/sheds
        cylinder(side+' porcelain weather shed',(x,0.14,z),0.225 if side=='HV' else 0.19,0.072,ceramic,48)
    cylinder(side+' contact crown',(x,0.14,top-0.12),0.12,0.16,copper)
    torus(side+' cable attachment eye',(x,0.14,top+0.015),0.105,0.032,steel,(math.pi/2,0,0))
    kit.socket('CableSocket_'+side,(x,0.14,top+0.015))
    for dx,dy in ((-0.21,0),(0.21,0),(0,-0.21),(0,0.21)):
        cylinder('Turret flange fastener',(x+dx,0.14+dy,3.17),0.027,0.035,steel,6)
    text(side+' tower label',side,(x-0.16,-0.107,3.23),0.12,white)

# Top expansion tank, pressure relief and reinforced lifting lugs.
cylinder('Expansion reservoir',(0,0.66,3.22),0.24,0.94,tank,48,(1,0,0))
for x in (-0.32,0.32):
    box('Reservoir saddle',(x,0.66,3.025),(0.12,0.55,0.15),steel)
pipe('Reservoir feed',[(0.36,0.65,3.22),(0.56,0.65,3.22),(0.56,0.78,2.9)],0.044,copper)
cylinder('Pressure vent',(0,-0.46,3.12),0.085,0.19,steel)
cylinder('Pressure vent cap',(0,-0.46,3.23),0.13,0.045,orange)
for x in (-0.86,0.86):
    for y in (-0.84,0.84):
        torus('Lifting eye',(x,y,3.055),0.09,0.032,steel,(math.pi/2,0,0),24,8)

# Front service cabinet with legible emissive load state and physical isolator.
box('Cabinet rear seal',(-0.18,-1.18,1.78),(1.48,0.18,1.42),rubber,0.075)
box('Orange instrument cabinet',(-0.18,-1.32,1.78),(1.4,0.28,1.34),orange,0.07)
box('Inset service door',(-0.18,-1.48,1.72),(1.21,0.065,1.12),graphite,0.045)
box('Display bezel',(-0.18,-1.528,2.04),(0.99,0.055,0.34),steel,0.035)
box('Recessed display glass',(-0.18,-1.563,2.04),(0.89,0.024,0.245),rubber,0.018)
text('Load readout','LOAD  72%',(-0.57,-1.581,2.058),0.105,cyan)
for index in range(10):
    box('Load bar',(-0.56+index*0.085,-1.581,1.988),(0.063,0.014,0.031),cyan if index<7 else tank,0.002)
text('Cabinet model','EP / 24',(-0.64,-1.527,1.7),0.105,white)
text('Cabinet voltage','HV > MV',(-0.64,-1.527,1.55),0.072,white)
box('Isolator escutcheon',(0.12,-1.535,1.48),(0.29,0.045,0.28),steel,0.025)
cylinder('Isolator pivot',(0.12,-1.58,1.48),0.075,0.055,rubber,32,(0,1,0))
box('Isolator handle',(0.12,-1.64,1.48),(0.21,0.07,0.06),orange,0.018)
for z in (1.39,1.8):
    box('Door hinge',(-0.76,-1.54,z),(0.07,0.065,0.16),steel,0.012)
cylinder('Running lamp',(0.32,-1.538,1.75),0.035,0.025,green,24,(0,1,0))
for x in (-0.78,0.42):
    for z in (1.2,2.33):
        bolt((x,-1.48,z))
# Cable conduits go from cabinet underside into the tank, behind the access step.
for x in (-0.5,0.21):
    pipe('Instrument conduit',[(x,-1.32,1.17),(x,-1.33,0.94),(x+0.22,-1.2,0.77),(x+0.3,-1.05,0.78)],0.035,rubber)

# Restrained hazard marking on a front threshold; individual stripes stay in its border.
box('Access tread',(0,-1.55,0.58),(1.95,0.67,0.13),graphite,0.035)
box('Warning threshold',(0,-1.875,0.59),(1.85,0.025,0.115),yellow,0.004)
for index in range(9):
    stripe=box('Threshold black slash',(-0.8+index*0.2,-1.892,0.59),(0.088,0.012,0.116),rubber,0.001)
    stripe.rotation_euler.y=-0.35
for index in range(12):
    box('Step traction rib',(-0.86+index*0.156,-1.57,0.655),(0.027,0.46,0.018),steel,0.004)
box('Lower step',(0,-1.71,0.3),(1.25,0.48,0.15),graphite,0.035)
for x in (-0.66,0.66):
    pipe('Access grab rail',[(x,-1.28,0.62),(x,-1.65,0.97),(x,-1.67,1.1)],0.032,steel)

# Rear oil circuit, service hatch, drain, guarded level gauge and informative labels.
box('Rear inspection flange',(0,1.14,1.76),(1.38,0.15,1.13),steel,0.075)
box('Rear inspection cover',(0,1.245,1.76),(1.2,0.085,0.97),tank,0.065)
for x in (-0.51,0,0.51):
    for z in (1.37,2.15):
        bolt((x,1.3,z),(0,1,0))
text('Rear warning','ISOLATE BEFORE SERVICE',(0.46,1.297,1.84),0.068,white,'+Y')
text('Rear nameplate','EP-24  /  OIL COOLED',(0.42,1.297,1.68),0.07,white,'+Y')
for x in (-0.94,0.94):
    pipe('Rear oil return',[(x,1.03,2.55),(x,1.43,2.55),(x,1.48,0.92),(x,1.08,0.78)],0.085,graphite)
    for z in (1.05,2.4):
        cylinder('Pipe union',(x,1.48,z),0.125,0.1,steel,32)
box('Oil sight gauge housing',(-0.45,1.36,1.15),(0.17,0.13,0.48),graphite,0.025)
box('Oil sight gauge',(-0.45,1.434,1.15),(0.062,0.024,0.34),ceramic,0.008)
box('Oil level',(-0.45,1.45,1.08),(0.043,0.012,0.17),yellow,0.004)
pipe('Drain outlet',[(0.55,1.02,0.76),(0.55,1.46,0.76),(0.55,1.52,0.64)],0.055,steel)
cylinder('Drain valve stem',(0.55,1.47,0.85),0.035,0.15,copper)
box('Drain valve handle',(0.55,1.47,0.94),(0.24,0.055,0.035),orange,0.012)
# Clear large-format panel stencil, not a borrowed brand mark.
text('Front equipment class','GRID / TRANSFORMER',(-0.78,-1.195,2.57),0.077,rubber)
for x in (-1.06,1.06):
    box('Danger plaque',(x,-1.2,1.34),(0.2,0.025,0.2),yellow,0.015)
    text('Voltage warning','!',(x-0.026,-1.218,1.285),0.15,rubber)

# A reusable asset collection is isolated from presentation geometry.
kit.configure_render(arguments.samples, arguments.width)
kit.build_studio(steel)

if arguments.animate or arguments.render_animation:
    kit.set_timeline(12, 60, [('OPERATING',1), ('OVERLOAD_WARNING',25), ('BREAKER_TRIP',41), ('COAST_DOWN',46), ('ISOLATED',60)])
    for rotor in fan_rotors:
        epkit.key_rotation(rotor, 0, [(frame, turns * 2 * math.pi) for frame, turns in [(1,0), (24,4), (40,8), (46,9.1), (52,9.7), (60,9.9)]], rotor.name + '_OperateWarningCoast')
    handle = bpy.data.objects.get('Isolator handle')
    handle.name = 'Breaker_Handle'
    epkit.key_rotation(handle, 1, [(1,0), (40,0), (42,-math.pi/2), (60,-math.pi/2)], 'Breaker_Trip')
    readout = bpy.data.objects.get('Load readout')
    overload_readout = text('Display_Overload', 'LOAD 108%', readout.location, 0.105, cyan)
    tripped_readout = text('Display_Tripped', 'TRIPPED', readout.location, 0.105, cyan)
    isolated_readout = text('Display_Isolated', 'ISOLATED', readout.location, 0.105, white)
    for obj, start, end in [(readout,1,24), (overload_readout,25,40), (tripped_readout,41,59), (isolated_readout,60,60)]:
        epkit.key_state_window(obj, start, end, (1,24,25,40,41,59,60), obj.name + '_StateVisibility')
    bars = [obj for obj in asset.objects if obj.name.startswith('Load bar')]
    for index, obj in enumerate(bars):
        obj.data.materials.clear()
        obj.data.materials.append(cyan)
        epkit.key_visibility(obj, [(1,index<7), (24,index<7), (25,True), (40,True), (41,False), (60,False)])
    epkit.key_emission(green, [(1,(0.25,0.8,0.35,1),2), (24,(0.25,0.8,0.35,1),2), (25,(1,0.32,0.015,1),3), (29,(1,0.32,0.015,1),0.2), (33,(1,0.18,0.015,1),4), (37,(1,0.18,0.015,1),0.2), (40,(1,0.08,0.01,1),4), (41,(1,0.045,0.01,1),1.3), (59,(1,0.045,0.01,1),1.3), (60,(0.06,0.065,0.07,1),0)], 'Status_OperatingWarningTrip')
    kit.scene.frame_set(1)
# Frame-one visible mesh totals include bevels and exclude the studio and inactive states.
kit.export_metrics(ROOT / 'metrics.json', arguments.samples)
kit.render_stills(ROOT / 'renders', VIEWS, arguments.views, ROOT / 'transformer.blend')
if arguments.render_animation:
    kit.render_animation(ROOT / 'renders' / 'animation', VIEWS['hero'], arguments.animation_width, arguments.animation_samples)
print('ASSET_RENDER_COMPLETE',flush=True)
