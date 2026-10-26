#!/usr/bin/env python3
"""Generate the original EP-24 transformer and a deterministic CPU studio render set."""
import math
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'common'))
import epkit  # noqa: E402

VIEWS = {'hero': ((6.6, -8.4, 3.5), (-0.35, 0, 2.0)), 'service': ((-6.9, 8.6, 3.2), (0, 0, 2.0)), 'orthographic': ((6, -8, 5.3), (0, 0, 2.04))}
arguments = epkit.parse_arguments(VIEWS, __doc__)
kit = epkit.Kit('EP24_Transformer')
asset = kit.asset
box, cylinder, pipe, text, torus = kit.block, kit.turned, kit.pipe, kit.text, kit.torus
palette = epkit.industrial_palette()
orange, graphite, tank, steel = palette.orange, palette.graphite, palette.tank, palette.steel
ceramic, copper, rubber, yellow = palette.ceramic, palette.copper, palette.rubber, palette.yellow
white, cyan, green = palette.white, palette.cyan, palette.green


def bolt(location, direction=(0, -1, 0)):
    return kit.fastener('Captive M16 hex bolt', location, steel, 0.016, direction)


def shoulder(name, x):
    # Thin folded plates form the orange shoulder shell.
    parts = []
    for y in (-1.115, 1.115):
        for bottom, top in ((0.64,1.67),(1.678,2.93)):
            profile = [(x-0.20,bottom),(x+0.20,bottom),(x+0.20,min(top,2.65)),(x+0.04,top),(x-0.20,top)]
            parts.append(kit.extrusion(name, profile, (y-0.015,y+0.015), orange, 0.002))
    parts.append(box(name+' crown',(x-0.04,0,2.93),(0.32,2.25,0.025),orange,'sheet'))
    return parts


# Four-meter load-bearing skid and replaceable corner shoes.
for x in (-1.52, 1.52):
    kit.section('Longitudinal I-section skid', (x,-1.775,0.24), (x,1.775,0.24), 0.3,0.38,0.018,graphite,'ibeam')
    kit.section('Silver skid top rail',(x,-1.775,0.43),(x,1.775,0.43),0.30,0.075,0.012,palette.secondary)
for y in (-1.55, 1.55):
    kit.section('Crossmember channel', (-1.8,y,0.31), (1.8,y,0.31), 0.28,0.28,0.016,graphite)
    for x in (-1.6, 1.6):
        box('Anchor shoe plate', (x,y,0.018), (0.58,0.58,0.036), steel,'sheet')
        box('Skid foot web', (x,y,0.09), (0.18,0.25,0.12), graphite)
        for dx in (-0.20,0.20):
            kit.fastener('Foundation M24 anchor',(x+dx,y,0.038),steel,0.024)
box('Bund tray floor',(0,0,0.485),(3.35,2.85,0.025),steel,'sheet')
for x in (-1.67,1.67):
    box('Bund folded side',(x,0,0.535),(0.012,2.85,0.1),steel,'sheet')
for y in (-1.42,1.42):
    box('Bund folded end',(0,y,0.535),(3.35,0.012,0.1),steel,'sheet')
box('Oil vessel', (0,0,1.72), (2.48,2.15,2.32), tank)
box('Lid gasket', (0,0,2.875), (2.6,2.23,0.012), rubber,'sheet')
box('Pressure lid', (0,0,2.92), (2.65,2.28,0.07), palette.secondary,'sheet')
for y in (-1.09,1.09):
    for index in range(15):
        kit.fastener('Lid M16 fastener',(-1.22+index*0.174,y,2.956),steel)
for x in (-1.29,1.29):
    for index in range(11):
        kit.fastener('Lid M16 fastener',(x,-0.9+index*0.18,2.956),steel)
for side in (-1,1):
    for y in (-0.72,-0.24,0.24,0.72):
        kit.section('Tank welded vertical stiffener',(side*1.251,y,0.72),(side*1.251,y,2.72),0.06,0.07,0.006,tank)
    if side > 0:
        continue
    box('Tank circumferential weld band',(side*1.246,0,1.06),(0.014,2.15,0.045),steel,'sheet')
    box('Tank specification plate',(side*1.31,0,2.35),(0.018,1.1,0.30),palette.secondary,'sheet')
    text('Tank side identification','EP-24 / OIL',(side*1.321,-side*0.46,2.33),0.08,graphite,'+X' if side > 0 else '-X')
    for y in (-0.24,0.24):
        for z in (2.25,2.45):
            cylinder('Specification plate spacer',(side*1.30,y,z),0.012,0.04,steel,12,(side,0,0))
            kit.fastener('Specification plate fixing',(side*1.319,y,z),steel,0.012,(side,0,0))
    cylinder('Tank thermometer bezel',(side*1.32,0.53,1.82),0.12,0.07,steel,32,(side,0,0))
    cylinder('Tank thermometer dial',(side*1.36,0.53,1.82),0.1,0.014,white,32,(side,0,0))
    needle = box('Tank thermometer needle',(side*1.37,0.53,1.85),(0.008,0.012,0.13),graphite,'sheet')
    needle.rotation_euler.x = 0.45
    pipe('Tank sampling line',[(side*1.28,-0.53,1.42),(side*1.39,-0.53,1.42),(side*1.39,-0.53,1.15)],0.018,copper)
    cylinder('Tank sampling valve',(side*1.39,-0.53,1.42),0.04,0.09,steel,16)
    box('Tank sampling lever',(side*1.39,-0.53,1.48),(0.04,0.16,0.014),orange,'sheet')
for x in (-0.98, 0.98):
    shoulder('Folded orange shoulder armor', x)
for x in (-1.06,1.06):
    box('Armor seam bonding strap',(x,-1.134,1.678),(0.045,0.008,0.20),steel,'sheet')
    for z in (1.61,1.745):
        kit.fastener('Bond strap M12 fixing',(x,-1.139,z),steel,0.012,(0,-1,0))
for y in (-1.13, 1.13):
    box('Lower shell cross belt', (0,y,0.87), (2.22,0.036,0.45), orange,'sheet')
    box('Upper shell cross belt', (0,y,2.64), (2.23,0.036,0.24), orange,'sheet')
    for x in (-0.85, 0.85):
        for z in (0.9, 2.65):
            bolt((x, math.copysign(1.148, y), z), (0, y, 0))

# Ribbed cooling bank on the right flank, with joined upper and lower oil headers.
for z in (0.94, 2.48):
    pipe('Radiator header', [(1.12,-0.87,z),(1.51,-0.87,z),(1.51,0.91,z),(1.12,0.91,z)], 0.058, graphite)
for index in range(27):
    y = -0.78 + index * 0.064
    box('Pressed radiator panel', (1.56,y,1.7), (0.56,0.008,1.46), palette.secondary,'sheet')
    for x in (1.38,1.56,1.74):
        box('Radiator pressed oil channel',(x,y,1.7),(0.032,0.018,1.36),palette.secondary,'sheet')
for y in (-0.91, 1.0):
    box('Radiator folded end guard', (1.6,y,1.72), (0.48,0.025,1.64), orange,'sheet')
    for z in (1.04,2.4):
        bolt((1.6,y-0.0125,z))
        kit.section('Radiator guard standoff',(1.25,y+0.026,z),(1.68,y+0.026,z),0.07,0.10,0.008,steel,'angle')
        kit.fastener('Radiator bracket fixing',(1.29,y+0.026,z),steel,0.016,(1,0,0))

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
    wall.thickness = 0.012
    wall.offset = 1
    for x in (1.865, 1.97):
        kit.torus('CoolingFan_DuctLip_' + identifier, (x,y,1.72), 0.37, 0.009, graphite, (0,math.pi/2,0), 48)
    cylinder('CoolingFan_Motor_' + identifier, (1.875,y,1.72), 0.080, 0.07, graphite, 32, (1,0,0))
    for index in range(3):
        angle = math.pi/2 + index * 2 * math.pi / 3
        strut = box('CoolingFan_SpiderStrut_' + identifier, (1.875, y+0.235*math.cos(angle), 1.72+0.235*math.sin(angle)), (0.018,0.25,0.025), graphite)
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
        blade.modifiers.new('Blade wall thickness', 'SOLIDIFY').thickness = 0.004
        bevel = blade.modifiers.new('Blade edge break', 'BEVEL')
        bevel.width = 0.001
        bevel.segments = 1
    for radius in (0.12,0.21,0.29,0.355):
        torus('CoolingFan_FingerGuardRing_'+identifier,(1.985,y,1.72),radius,0.0035,steel,(0,math.pi/2,0),48,6)
    for angle in (0,math.pi/3,2*math.pi/3):
        dy,dz = 0.355*math.cos(angle),0.355*math.sin(angle)
        pipe('CoolingFan_FingerGuard_'+identifier,[(1.988,y-dy,1.72-dz),(1.988,y+dy,1.72+dz)],0.0035,steel)
    for z in (1.33, 2.11):
        kit.section('CoolingFan_Mount_'+identifier,(1.81,y-0.08,z),(1.95,y-0.08,z),0.08,0.08,0.006,graphite,'angle')

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
    torus(side+' cable attachment eye',(x,0.14,top+0.015),0.045,0.009,steel,(math.pi/2,0,0))
    kit.socket('CableSocket_'+side,(x,0.14,top+0.015))
    for dx,dy in ((-0.21,0),(0.21,0),(0,-0.21),(0,0.21)):
        cylinder('Turret flange fastener',(x+dx,0.14+dy,3.17),0.027,0.035,steel,6)
    text(side+' tower label',side,(x-0.16,-0.107,3.23),0.12,white)

for obj in asset.objects:
    if obj.type != 'FONT' and obj.name.startswith(('HV ', 'MV ')):
        obj['ep_lod_preserve'] = True
        obj['ep_lod_assembly'] = obj.name.split()[0] + '_Terminal'

# Top expansion tank, pressure relief and reinforced lifting lugs.
cylinder('Expansion reservoir',(0,0.66,3.22),0.24,0.94,tank,48,(1,0,0))
for x in (-0.32,0.32):
    box('Reservoir saddle',(x,0.66,3.025),(0.12,0.55,0.15),steel)
pipe('Reservoir feed',[(0.36,0.65,3.22),(0.56,0.65,3.22),(0.56,0.78,2.9)],0.044,copper)
cylinder('Pressure vent',(0.50,-0.75,3.12),0.085,0.19,steel)
cylinder('Pressure vent cap',(0.50,-0.75,3.23),0.13,0.045,orange)
cylinder('Lid bolted inspection manhole',(0,-0.52,2.982),0.29,0.05,graphite,48)
cylinder('Manhole cover',(0,-0.52,3.013),0.24,0.018,steel,48)
for index in range(10):
    angle = index*math.tau/10
    kit.fastener('Manhole M12 fastener',(0.264*math.cos(angle),-0.52+0.264*math.sin(angle),3.009),steel,0.012)
for y in (-0.98,0.98):
    kit.section('Lid stiffening channel',(-0.7,y,2.99),(0.7,y,2.99),0.06,0.07,0.006,steel)
for x in (-0.86,0.86):
    for y in (-0.84,0.84):
        torus('Lifting eye',(x,y,3.055),0.055,0.012,steel,(math.pi/2,0,0),24,8)
        cylinder('Lifting eye mounting flange',(x,y,2.967),0.075,0.024,steel)
        cylinder('Lifting eye mounting neck',(x,y,2.994),0.022,0.032,steel)

# Front service cabinet with legible emissive load state and physical isolator.
box('Cabinet rear seal',(-0.18,-1.18,1.78),(1.48,0.08,1.42),rubber,'sheet')
box('Orange instrument cabinet',(-0.18,-1.32,1.78),(1.4,0.28,1.34),orange)
for x in (-0.874,0.514):
    box('Silver cabinet jamb',(x,-1.474,1.78),(0.045,0.035,1.38),palette.secondary,'sheet')
for z in (1.11,2.45):
    box('Silver cabinet header',( -0.18,-1.474,z),(1.42,0.035,0.045),palette.secondary,'sheet')
box('Door perimeter seam',(-0.18,-1.47,1.72),(1.226,0.009,1.136),rubber,'sheet')
box('Inset service door',(-0.18,-1.48,1.72),(1.21,0.018,1.12),graphite,'sheet')
box('Cabinet drip hood',(-0.18,-1.355,2.466),(1.47,0.42,0.018),steel,'sheet')
for x in (-0.68,0.32):
    vertices = [(x+dx,y,z) for dx in (-0.008,0.008) for y,z in ((-1.46,2.455),(-1.555,2.455),(-1.46,2.32))]
    kit.mesh('Drip hood gusset',vertices,[(2,1,0),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],steel,0.001)
box('Display bezel',(-0.18,-1.505,2.04),(0.99,0.025,0.34),steel,'sheet')
box('Recessed display glass',(-0.18,-1.53,2.04),(0.89,0.024,0.245),rubber,'sheet')
box('Cabinet ventilation recess',(-0.38,-1.501,1.36),(0.52,0.012,0.23),rubber,'sheet')
kit.louvres('Cabinet folded vent',(-0.38,-1.516,1.36),0.48,0.20,palette.secondary)
text('Load readout','LOAD  72%',(-0.57,-1.581,2.058),0.105,cyan)
for index in range(10):
    box('Load bar',(-0.56+index*0.085,-1.551,1.988),(0.063,0.014,0.031),cyan if index<7 else tank,'sheet')
text('Cabinet model','EP / 24',(-0.64,-1.527,1.7),0.105,white)
text('Cabinet voltage','HV > MV',(-0.64,-1.527,1.55),0.072,white)
box('Isolator escutcheon',(0.12,-1.505,1.48),(0.24,0.018,0.24),steel,'sheet')
cylinder('Isolator pivot',(0.12,-1.54,1.48),0.045,0.04,rubber,32,(0,1,0))
box('Isolator handle',(0.12,-1.58,1.48),(0.17,0.04,0.04),orange)
for z in (1.39,1.8):
    box('Door hinge',(-0.795,-1.505,z),(0.035,0.03,0.095),steel,'sheet')
cylinder('Running lamp',(0.32,-1.538,1.75),0.035,0.025,green,24,(0,1,0))
for x in (-0.78,0.42):
    for z in (1.2,2.33):
        bolt((x,-1.489 if z < 2.28 else -1.46,z))
# Cable conduits go from cabinet underside into the tank, behind the access step.
for x in (-0.5,0.21):
    pipe('Instrument conduit',[(x,-1.32,1.17),(x,-1.33,0.94),(x+0.22,-1.2,0.77),(x+0.3,-1.05,0.78)],0.018,steel)

# Restrained hazard marking on a front threshold; individual stripes stay in its border.
kit.grating('Access platform',(0,-1.37,0.60),1.8,0.40,steel)
box('Warning threshold',(0,-1.578,0.59),(1.85,0.025,0.115),yellow,'sheet')
for index in range(9):
    stripe=box('Threshold black slash',(-0.8+index*0.2,-1.595,0.59),(0.088,0.012,0.116),rubber,'sheet')
    stripe.rotation_euler.y=-0.35
kit.grating('Lower step',(0,-1.88,0.20),1.25,0.22,steel)
kit.grating('Middle step',(0,-1.68,0.40),1.45,0.22,steel)
for x in (-0.53,0.53):
    profile = [(-1.99,0.18),(-1.77,0.18),(-1.77,0.38),(-1.57,0.38),(-1.57,0.58),(-1.17,0.58),(-1.17,0.46),(-1.99,0.06)]
    vertices = [(x+offset,y,z) for offset in (-0.01,0.01) for y,z in profile]
    count = len(profile)
    faces = [tuple(reversed(range(count))),tuple(range(count,2*count))]
    faces += [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    kit.mesh('Stair folded plate stringer',vertices,faces,palette.secondary,0.001)
    box('Stair ground foot',(x,-1.92,0.085),(0.08,0.06,0.17),palette.secondary,'sheet')
    box('Stair anchor plate',(x,-1.92,0.01),(0.12,0.13,0.02),steel,'sheet')
    kit.fastener('Stair foot fixing',(x,-1.965,0.02),steel,0.012)
for x in (-0.89,0.89):
    kit.section('Landing side support',(x,-1.82,0.58),(x,-1.17,0.58),0.06,0.08,0.006,graphite)
    for y in (-1.78,-1.31):
        cylinder('Handrail post',(x,y,1.15),0.0212,1.1,steel,16)
    for z in (1.15,1.70):
        pipe('Access handrail',[(x,-1.78,z),(x,-1.31,z)],0.0212,steel)

# Rear oil circuit, service hatch, drain, guarded level gauge and informative labels.
box('Rear inspection flange',(0,1.14,1.76),(1.38,0.05,1.13),steel,'sheet')
box('Rear inspection gasket',(0,1.179,1.76),(1.225,0.012,0.995),rubber,'sheet')
box('Rear inspection cover',(0,1.195,1.76),(1.2,0.024,0.97),tank,'sheet')
for x in (-0.51,0,0.51):
    for z in (1.37,2.15):
        bolt((x,1.21,z),(0,1,0))
text('Rear warning','ISOLATE BEFORE',(0.49,1.211,1.88),0.10,white,'+Y')
text('Rear warning second line','SERVICE',(0.49,1.211,1.74),0.10,white,'+Y')
text('Rear nameplate','EP-24 / OIL COOLED',(0.49,1.211,1.55),0.085,white,'+Y')
for x in (-0.94,0.94):
    pipe('Rear oil return',[(x,1.03,2.55),(x,1.43,2.55),(x,1.48,0.92),(x,1.08,0.78)],0.055,graphite)
    for z in (1.05,2.4):
        cylinder('Pipe union',(x,1.48,z),0.085,0.05,steel,32)
box('Oil sight gauge housing',(-0.45,1.36,1.15),(0.12,0.09,0.38),graphite)
box('Oil sight gauge',(-0.45,1.414,1.15),(0.045,0.014,0.29),ceramic,'sheet')
box('Oil level',(-0.45,1.425,1.08),(0.030,0.008,0.15),yellow,'sheet')
pipe('Drain outlet',[(0.55,1.02,0.76),(0.55,1.46,0.76),(0.55,1.52,0.64)],0.03,steel)
cylinder('Drain valve stem',(0.55,1.47,0.85),0.018,0.15,copper)
box('Drain valve handle',(0.55,1.47,0.94),(0.18,0.035,0.018),orange,'sheet')
# Clear large-format panel stencil, not a borrowed brand mark.
text('Front equipment class','GRID / TRANSFORMER',(-0.83,-1.149,2.57),0.10,white)
for x in (-1.06,1.06):
    box('Danger plaque',(x,-1.133,1.34),(0.16,0.006,0.20),yellow,'sheet')
    text('Voltage warning','!',(x-0.026,-1.137,1.285),0.15,rubber)

for name in ('Upper shell cross belt', 'Recessed display glass', 'Inset service door'):
    bpy.data.objects[name]['ep_uv_importance'] = 3.0

# A reusable asset collection is isolated from presentation geometry.
kit.configure_render(arguments.samples, arguments.width)
kit.build_site(steel)
kit.scale_figure((-2.65,-1.25,0))

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
