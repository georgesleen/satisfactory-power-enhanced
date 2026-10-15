#!/usr/bin/env python3
"""Generate the original EP-24 transformer and a deterministic CPU studio render set."""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--samples', type=int, default=40)
parser.add_argument('--width', type=int, default=1280)
parser.add_argument('--views', nargs='+', choices=['hero', 'service', 'orthographic'], default=['hero', 'service', 'orthographic'])
parser.add_argument('--animate', action='store_true', help='Key operating, warning and trip states in the source scene')
parser.add_argument('--render-animation', action='store_true', help='Also render a 60-frame 12 fps operating preview')
parser.add_argument('--animation-width', type=int, default=640)
parser.add_argument('--animation-samples', type=int, default=12)
arguments = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for collection in list(bpy.data.collections):
    if collection.name != 'Collection':
        bpy.data.collections.remove(collection)
asset = bpy.data.collections.get('Collection')
asset.name = 'EP24_Transformer'
studio = bpy.data.collections.new('Studio_non_export')
bpy.context.scene.collection.children.link(studio)


def material(name, color, metallic=0.0, roughness=0.4, emission=0.0):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1)
    result.use_nodes = True
    shader = result.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = roughness
    if emission:
        shader.inputs['Emission Color'].default_value = (*color, 1)
        shader.inputs['Emission Strength'].default_value = emission
    return result


orange = material('Enamel | safety ochre', (0.8, 0.215, 0.035), 0.25, 0.4)
graphite = material('Structure | graphite powdercoat', (0.047, 0.063, 0.073), 0.3, 0.43)
tank = material('Tank | charcoal enamel', (0.085, 0.11, 0.12), 0.28, 0.4)
steel = material('Fasteners | satin stainless', (0.43, 0.5, 0.53), 0.82, 0.28)
ceramic = material('Insulators | glazed warm porcelain', (0.74, 0.69, 0.53), 0.08, 0.22)
copper = material('Terminals | tinned copper', (0.49, 0.27, 0.12), 0.8, 0.25)
rubber = material('Seals | elastomer', (0.012, 0.018, 0.022), 0.05, 0.55)
yellow = material('Markings | warm yellow', (0.95, 0.61, 0.07), 0.18, 0.4)
white = material('Markings | warm off-white', (0.8, 0.83, 0.78), 0.1, 0.45)
cyan = material('Display | soft cyan', (0.12, 0.72, 0.79), 0.2, 0.3, 2)
green = material('Status | running', (0.25, 0.8, 0.35), 0.1, 0.25, 2)
# A restrained microsurface breaks up large painted highlights without grunge textures.
for paint in (orange, graphite, tank):
    nodes = paint.node_tree.nodes
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 145
    noise.inputs['Detail'].default_value = 2
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.12
    bump.inputs['Distance'].default_value = 0.012
    paint.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    paint.node_tree.links.new(bump.outputs['Normal'], nodes.get('Principled BSDF').inputs['Normal'])


def finish(obj, name, surface, bevel=0):
    obj.name = name
    obj.data.materials.append(surface)
    if bevel:
        modifier = obj.modifiers.new('Manufactured edge radius', 'BEVEL')
        modifier.width = bevel
        modifier.segments = 3
        modifier = obj.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
        modifier.keep_sharp = True
    return obj


def box(name, location, dimensions, surface, bevel=0.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, name, surface, bevel)


def cylinder(name, location, radius, depth, surface, vertices=32, direction=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    if direction:
        obj.rotation_euler = Vector(direction).to_track_quat('Z', 'Y').to_euler()
    for polygon in obj.data.polygons:
        polygon.use_smooth = len(polygon.vertices) == 4
    return finish(obj, name, surface, 0.009)


def pipe(name, points, radius, surface):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 12
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(len(points) - 1)
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = 'AUTO'
        point.handle_right_type = 'AUTO'
    obj = bpy.data.objects.new(name, curve)
    asset.objects.link(obj)
    obj.data.materials.append(surface)
    return obj


def text(name, content, location, size, surface, rear=False):
    curve = bpy.data.curves.new(name, 'FONT')
    curve.body = content
    curve.size = size
    curve.extrude = 0.0008
    curve.space_character = 1.1
    obj = bpy.data.objects.new(name, curve)
    asset.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (math.pi / 2, 0, math.pi if rear else 0)
    obj.data.materials.append(surface)
    return obj


def bolt(location, direction=(0, -1, 0)):
    return cylinder('Captive hex bolt', location, 0.035, 0.025, steel, 6, direction)


def shoulder(name, x):
    # A thick folded shell wraps the tank shoulder, not an enclosing cube.
    profile = [(x-0.2, 0.61), (x+0.2, 0.61), (x+0.2, 2.65), (x+0.04, 2.95), (x-0.26, 2.95), (x-0.2, 2.57)]
    vertices = [(a, y, z) for y in (-1.13, 1.13) for a, z in profile]
    count = len(profile)
    faces = [tuple(reversed(range(count))), tuple(range(count, 2*count))]
    faces += [(i, (i+1)%count, (i+1)%count+count, i+count) for i in range(count)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    asset.objects.link(obj)
    return finish(obj, name, orange, 0.055)


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
    rotor = bpy.data.objects.new('CoolingFan_Rotor_' + identifier, None)
    asset.objects.link(rotor)
    rotor.location = (1.935, y, 1.72)
    fan_rotors.append(rotor)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.355, depth=0.11, end_fill_type='NOTHING', location=(1.915,y,1.72), rotation=(0,math.pi/2,0))
    duct = finish(bpy.context.object, 'CoolingFan_Duct_' + identifier, graphite)
    for polygon in duct.data.polygons:
        polygon.use_smooth = True
    wall = duct.modifiers.new('Duct wall thickness', 'SOLIDIFY')
    wall.thickness = 0.03
    wall.offset = 1
    for x in (1.865, 1.97):
        bpy.ops.mesh.primitive_torus_add(major_segments=48, minor_segments=10, major_radius=0.37, minor_radius=0.027, location=(x,y,1.72), rotation=(0,math.pi/2,0))
        finish(bpy.context.object, 'CoolingFan_DuctLip_' + identifier, graphite)
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
        mesh = bpy.data.meshes.new('Pitched impeller blade')
        mesh.from_pydata(vertices, [], [(0,1,2,3)])
        mesh.update()
        blade = bpy.data.objects.new('CoolingFan_Blade_' + identifier, mesh)
        asset.objects.link(blade)
        blade.parent = rotor
        finish(blade, blade.name, orange)
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
    bpy.ops.mesh.primitive_torus_add(major_segments=32,minor_segments=10,location=(x,0.14,top+0.015),major_radius=0.105,minor_radius=0.032,rotation=(math.pi/2,0,0))
    finish(bpy.context.object,side+' cable attachment eye',steel)
    socket=bpy.data.objects.new('CableSocket_'+side,None)
    asset.objects.link(socket)
    socket.location=(x,0.14,top+0.015)
    socket.empty_display_type='ARROWS'
    socket.empty_display_size=0.2
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
        bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=8,major_radius=0.09,minor_radius=0.032,location=(x,y,3.055),rotation=(math.pi/2,0,0))
        finish(bpy.context.object,'Lifting eye',steel)

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
text('Rear warning','ISOLATE BEFORE SERVICE',(0.46,1.297,1.84),0.068,white,True)
text('Rear nameplate','EP-24  /  OIL COOLED',(0.42,1.297,1.68),0.07,white,True)
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
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1.0
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=arguments.samples
scene.cycles.use_denoising=True
scene.cycles.max_bounces=6
scene.cycles.diffuse_bounces=3
scene.cycles.glossy_bounces=3
scene.render.resolution_x=arguments.width
scene.render.resolution_y=round(arguments.width*0.75)
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
scene.world.color=(0.12,0.12,0.12)
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(0.095,0.12,0.16,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=0.35


def move_studio(obj):
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    studio.objects.link(obj)


floor=box('Studio floor',(0,0,-0.14),(200,200,0.2),material('Studio | slate',(0.038,0.048,0.062),0.2,0.5),0)
move_studio(floor)
plinth=box('Display foundation',(0,0,-0.065),(4.6,4.6,0.13),material('Studio | foundation',(0.095,0.113,0.13),0.4,0.4),0.055)
move_studio(plinth)
for x in (-2.23,2.23):
    trim=box('Foundation edge inlay',(x,0,0.005),(0.018,4.28,0.005),steel,0)
    move_studio(trim)


def aim(obj, target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()


def light(name, location, power, color, size, target):
    data=bpy.data.lights.new(name,'AREA')
    data.energy=power
    data.color=color
    data.shape='DISK'
    data.size=size
    obj=bpy.data.objects.new(name,data)
    studio.objects.link(obj)
    obj.location=location
    aim(obj,target)


light('Warm softbox', (1,-5,7),950,(1.0,0.84,0.68),5,(0,0,1.8))
light('Cool edgebox',(-4,2,6),1500,(0.59,0.76,1),4,(0,0,2))
light('Radiator rim',(4,4,5),1700,(1,0.89,0.71),3,(0,0,1.8))
light('Front fill',(-4,-4,3),420,(0.73,0.84,1),3,(0,0,1.8))
camera_data=bpy.data.cameras.new('Presentation camera')
camera=bpy.data.objects.new('Presentation camera',camera_data)
studio.objects.link(camera)
scene.camera=camera
camera.data.lens=54
camera.data.clip_end=250
views={'hero':((7,-9,6.1),(0,0,1.95)), 'service':((-5.5,9.8,5.8),(0,0,1.94)), 'orthographic':((6,-8,5.3),(0,0,2.04))}

if arguments.animate or arguments.render_animation:
    scene.render.fps = 12
    scene.frame_start = 1
    scene.frame_end = 60
    for label, frame in [('OPERATING',1), ('OVERLOAD_WARNING',25), ('BREAKER_TRIP',41), ('COAST_DOWN',46), ('ISOLATED',60)]:
        scene.timeline_markers.new(label, frame=frame)
    for rotor in fan_rotors:
        for frame, turns in [(1,0), (24,4), (40,8), (46,9.1), (52,9.7), (60,9.9)]:
            rotor.rotation_euler.x = turns * 2 * math.pi
            rotor.keyframe_insert(data_path='rotation_euler', index=0, frame=frame)
        rotor.animation_data.action.name = rotor.name + '_OperateWarningCoast'
    handle = bpy.data.objects.get('Isolator handle')
    handle.name = 'Breaker_Handle'
    for frame, angle in [(1,0), (40,0), (42,-math.pi/2), (60,-math.pi/2)]:
        handle.rotation_euler.y = angle
        handle.keyframe_insert(data_path='rotation_euler', index=1, frame=frame)
    handle.animation_data.action.name = 'Breaker_Trip'
    readout = bpy.data.objects.get('Load readout')
    overload_readout = text('Display_Overload', 'LOAD 108%', readout.location, 0.105, cyan)
    tripped_readout = text('Display_Tripped', 'TRIPPED', readout.location, 0.105, cyan)
    isolated_readout = text('Display_Isolated', 'ISOLATED', readout.location, 0.105, white)
    for obj, start, end in [(readout,1,24), (overload_readout,25,40), (tripped_readout,41,59), (isolated_readout,60,60)]:
        for frame in (1,24,25,40,41,59,60):
            obj.hide_render = not start <= frame <= end
            obj.hide_viewport = obj.hide_render
            obj.keyframe_insert(data_path='hide_render', frame=frame)
            obj.keyframe_insert(data_path='hide_viewport', frame=frame)
        obj.animation_data.action.name = obj.name + '_StateVisibility'
    bars = [obj for obj in asset.objects if obj.name.startswith('Load bar')]
    for index, obj in enumerate(bars):
        obj.data.materials.clear()
        obj.data.materials.append(cyan)
        for frame, visible in [(1,index<7), (24,index<7), (25,True), (40,True), (41,False), (60,False)]:
            obj.hide_render = not visible
            obj.hide_viewport = not visible
            obj.keyframe_insert(data_path='hide_render', frame=frame)
            obj.keyframe_insert(data_path='hide_viewport', frame=frame)
    status_shader = green.node_tree.nodes.get('Principled BSDF')
    for frame, color, strength in [(1,(0.25,0.8,0.35,1),2), (24,(0.25,0.8,0.35,1),2), (25,(1,0.32,0.015,1),3), (29,(1,0.32,0.015,1),0.2), (33,(1,0.18,0.015,1),4), (37,(1,0.18,0.015,1),0.2), (40,(1,0.08,0.01,1),4), (41,(1,0.045,0.01,1),1.3), (59,(1,0.045,0.01,1),1.3), (60,(0.06,0.065,0.07,1),0)]:
        for socket_name in ('Base Color', 'Emission Color'):
            socket = status_shader.inputs[socket_name]
            socket.default_value = color
            socket.keyframe_insert(data_path='default_value', frame=frame)
        socket = status_shader.inputs['Emission Strength']
        socket.default_value = strength
        socket.keyframe_insert(data_path='default_value', frame=frame)
    green.node_tree.animation_data.action.name = 'Status_OperatingWarningTrip'
    scene.frame_set(1)
# Frame-one visible mesh totals include bevels and exclude the studio and inactive states.
depsgraph=bpy.context.evaluated_depsgraph_get()
minimum=Vector((float('inf'),)*3)
maximum=Vector((float('-inf'),)*3)
mesh_count=0
triangles=0
for obj in asset.objects:
    if obj.type not in {'MESH','CURVE','FONT'} or obj.hide_render:
        continue
    evaluated=obj.evaluated_get(depsgraph)
    mesh=evaluated.to_mesh()
    mesh.calc_loop_triangles()
    mesh_count+=1
    triangles+=len(mesh.loop_triangles)
    for vertex in mesh.vertices:
        point=obj.matrix_world@vertex.co
        for axis in range(3):
            minimum[axis]=min(minimum[axis],point[axis])
            maximum[axis]=max(maximum[axis],point[axis])
    evaluated.to_mesh_clear()
metrics={'units':'meters','bounds_min':list(minimum),'bounds_max':list(maximum),'dimensions':list(maximum-minimum),'renderable_objects':mesh_count,'evaluated_triangles':triangles,'samples':arguments.samples,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'engine':'Cycles CPU, denoised','sockets':{obj.name:list(obj.location) for obj in asset.objects if obj.name.startswith('CableSocket_')}}
(ROOT/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
print('ASSET_METRICS '+json.dumps(metrics),flush=True)
(ROOT/'renders').mkdir(exist_ok=True)
for name in arguments.views:
    location,target=views[name]
    camera.location=location
    aim(camera,target)
    camera.data.type='ORTHO' if name=='orthographic' else 'PERSP'
    camera.data.ortho_scale=8.3
    scene.render.filepath=str(ROOT/'renders'/f'{name}.png')
    if name=='hero':
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'transformer.blend'))
    bpy.ops.render.render(write_still=True)
if arguments.render_animation:
    camera.location = views['hero'][0]
    aim(camera, views['hero'][1])
    camera.data.type = 'PERSP'
    scene.render.resolution_x = arguments.animation_width
    scene.render.resolution_y = round(arguments.animation_width * 0.75)
    scene.cycles.samples = arguments.animation_samples
    animation_directory = ROOT / 'renders' / 'animation'
    animation_directory.mkdir(exist_ok=True)
    scene.render.filepath = str(animation_directory / 'frame_')
    bpy.ops.render.render(animation=True)
print('ASSET_RENDER_COMPLETE',flush=True)
