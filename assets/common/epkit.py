"""Shared Blender kit for Enhanced Power asset generators.

Import it from a generator script that runs inside Blender:

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'common'))
    import epkit
"""
import argparse
import json
import math
from pathlib import Path
from types import SimpleNamespace
import sys

import bpy
from mathutils import Vector

STILL_ASPECT = 0.75
FOUNDATION_SIZE = 4.6
WORLD_COLOR = (0.095, 0.12, 0.16, 1)
WORLD_STRENGTH = 0.35
# Name, location, power in watts, color, disk size in meters and aim target of each studio area light.
STUDIO_LIGHTS = [
    ('Warm softbox', (1, -5, 7), 950, (1.0, 0.84, 0.68), 5, (0, 0, 1.8)),
    ('Cool edgebox', (-4, 2, 6), 1500, (0.59, 0.76, 1), 4, (0, 0, 2)),
    ('Radiator rim', (4, 4, 5), 1700, (1, 0.89, 0.71), 3, (0, 0, 1.8)),
    ('Front fill', (-4, -4, 3), 420, (0.73, 0.84, 1), 3, (0, 0, 1.8)),
]
CAMERA_LENS = 54
ORTHOGRAPHIC_SCALE = 8.3
# Z rotation of a text object for each direction its readable face points.
TEXT_FACING = {'-Y': 0, '+Y': math.pi, '+X': math.pi / 2, '-X': -math.pi / 2}


def parse_arguments(views, description):
    """Parse the shared generator command line that follows Blender's `--` separator.

    `views` lists the still camera names that `--views` accepts.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--samples', type=int, default=40)
    parser.add_argument('--width', type=int, default=1280)
    parser.add_argument('--views', nargs='+', choices=list(views), default=list(views))
    parser.add_argument('--animate', action='store_true', help='Key the named state sequence in the source scene')
    parser.add_argument('--render-animation', action='store_true', help='Also render the keyed sequence as preview frames')
    parser.add_argument('--animation-width', type=int, default=640)
    parser.add_argument('--animation-samples', type=int, default=12)
    return parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])


def material(name, color, metallic=0.0, roughness=0.4, emission=0.0):
    """Create a Principled material; a nonzero `emission` makes the base color glow at that strength."""
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


def add_paint_microsurface(paint):
    """Add a fine noise bump to a painted material."""
    nodes = paint.node_tree.nodes
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 145
    noise.inputs['Detail'].default_value = 2
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.12
    bump.inputs['Distance'].default_value = 0.012
    paint.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    paint.node_tree.links.new(bump.outputs['Normal'], nodes.get('Principled BSDF').inputs['Normal'])


def standard_palette():
    """Create the shared Enhanced Power material set.

    Fields: orange, graphite, tank, steel, ceramic, copper, rubber, yellow, white, cyan, green.
    """
    palette = SimpleNamespace(
        orange=material('Enamel | safety ochre', (0.8, 0.215, 0.035), 0.25, 0.4),
        graphite=material('Structure | graphite powdercoat', (0.047, 0.063, 0.073), 0.3, 0.43),
        tank=material('Tank | charcoal enamel', (0.085, 0.11, 0.12), 0.28, 0.4),
        steel=material('Fasteners | satin stainless', (0.43, 0.5, 0.53), 0.82, 0.28),
        ceramic=material('Insulators | glazed warm porcelain', (0.74, 0.69, 0.53), 0.08, 0.22),
        copper=material('Terminals | tinned copper', (0.49, 0.27, 0.12), 0.8, 0.25),
        rubber=material('Seals | elastomer', (0.012, 0.018, 0.022), 0.05, 0.55),
        yellow=material('Markings | warm yellow', (0.95, 0.61, 0.07), 0.18, 0.4),
        white=material('Markings | warm off-white', (0.8, 0.83, 0.78), 0.1, 0.45),
        cyan=material('Display | soft cyan', (0.12, 0.72, 0.79), 0.2, 0.3, 2),
        green=material('Status | running', (0.25, 0.8, 0.35), 0.1, 0.25, 2),
    )
    for paint in (palette.orange, palette.graphite, palette.tank):
        add_paint_microsurface(paint)
    return palette


def srgb(rgb):
    """Convert an sRGB byte triplet to scene-linear RGB."""
    return tuple(channel / 3294.6 if channel <= 10.31475 else ((channel / 255 + 0.055) / 1.055) ** 2.4 for channel in rgb)


def bevel_size(dimensions, category='fabricated'):
    """Return a meter-scale edge break for a fabricated, sheet, or cast part."""
    smallest = min(dimensions)
    maximum = {'sheet': 0.002, 'fabricated': 0.012, 'cast': 0.025}[category]
    return min(smallest * 0.08, maximum)


def industrial_surface(name, rgb, roughness, metallic=0, painted=False, galvanized=False, glazed=False):
    """Create restrained procedural fabrication finishes in meter-scale coordinates."""
    surface = material(name, srgb(rgb), metallic, roughness)
    nodes, links = surface.node_tree.nodes, surface.node_tree.links
    shader = nodes.get('Principled BSDF')
    coordinate = nodes.new('ShaderNodeTexCoord')
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 18 if galvanized else 7
    noise.inputs['Detail'].default_value = 2
    links.new(coordinate.outputs['Object'], noise.inputs['Vector'])
    ramp = nodes.new('ShaderNodeMapRange')
    ramp.inputs['To Min'].default_value = max(0, roughness - 0.07)
    ramp.inputs['To Max'].default_value = min(1, roughness + 0.07)
    links.new(noise.outputs['Fac'], ramp.inputs['Value'])
    links.new(ramp.outputs['Result'], shader.inputs['Roughness'])
    tint = nodes.new('ShaderNodeMixRGB')
    tint.inputs[1].default_value = (*srgb(tuple(round(c * 0.91) for c in rgb)), 1)
    tint.inputs[2].default_value = (*srgb(rgb), 1)
    links.new(noise.outputs['Fac'], tint.inputs[0])
    color = tint.outputs[0]
    if galvanized:
        spangle = nodes.new('ShaderNodeTexVoronoi')
        spangle.inputs['Scale'].default_value = 95
        links.new(coordinate.outputs['Object'], spangle.inputs['Vector'])
        mix = nodes.new('ShaderNodeMixRGB')
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = 0.16
        links.new(color, mix.inputs[1])
        links.new(spangle.outputs['Color'], mix.inputs[2])
        color = mix.outputs[0]
    if painted:
        bevel = nodes.new('ShaderNodeBevel')
        bevel.samples = 2
        bevel.inputs['Radius'].default_value = 0.0018
        geometry = nodes.new('ShaderNodeNewGeometry')
        difference = nodes.new('ShaderNodeVectorMath')
        difference.operation = 'DOT_PRODUCT'
        links.new(bevel.outputs['Normal'], difference.inputs[0])
        links.new(geometry.outputs['Normal'], difference.inputs[1])
        mask = nodes.new('ShaderNodeMapRange')
        mask.clamp = True
        mask.inputs['From Min'].default_value = 0.94
        mask.inputs['From Max'].default_value = 0.999
        mask.inputs['To Min'].default_value = 0.32
        mask.inputs['To Max'].default_value = 0
        links.new(difference.outputs['Value'], mask.inputs['Value'])
        worn = nodes.new('ShaderNodeMixRGB')
        worn.inputs[2].default_value = (*srgb((133, 141, 142)), 1)
        links.new(mask.outputs['Result'], worn.inputs[0])
        links.new(color, worn.inputs[1])
        color = worn.outputs[0]
        links.new(mask.outputs['Result'], shader.inputs['Metallic'])
        height = nodes.new('ShaderNodeSeparateXYZ')
        links.new(geometry.outputs['Position'], height.inputs[0])
        grime = nodes.new('ShaderNodeMapRange')
        grime.clamp = True
        grime.inputs['From Min'].default_value = 0.12
        grime.inputs['From Max'].default_value = 1.0
        grime.inputs['To Min'].default_value = 0.13
        grime.inputs['To Max'].default_value = 0
        links.new(height.outputs['Z'], grime.inputs['Value'])
        dirty = nodes.new('ShaderNodeMixRGB')
        dirty.inputs[2].default_value = (*srgb((58, 53, 44)), 1)
        links.new(color, dirty.inputs[1])
        links.new(grime.outputs['Result'], dirty.inputs[0])
        color = dirty.outputs[0]
    links.new(color, shader.inputs['Base Color'])
    if glazed:
        shader.inputs['Coat Weight'].default_value = 0.65
        shader.inputs['Coat Roughness'].default_value = 0.14
    return surface


def industrial_palette():
    """Create the full-size stylized equipment palette with the standard palette fields."""
    palette = SimpleNamespace(
        orange=industrial_surface('Enamel | industrial amber', (226, 139, 48), 0.46, painted=True),
        graphite=industrial_surface('Structure | graphite enamel', (55, 64, 70), 0.52, painted=True),
        tank=industrial_surface('Tank | blue charcoal enamel', (78, 91, 96), 0.49, painted=True),
        secondary=industrial_surface('Enamel | cool grey panels', (172, 181, 184), 0.48, painted=True),
        steel=industrial_surface('Steel | galvanized', (163, 174, 180), 0.43, 1, galvanized=True),
        dark_steel=industrial_surface('Steel | dark mill finish', (66, 74, 79), 0.56, 1),
        ceramic=industrial_surface('Insulators | grey glazed porcelain', (171, 175, 164), 0.20, glazed=True),
        copper=industrial_surface('Terminals | copper', (176, 107, 67), 0.32, 1),
        rubber=industrial_surface('Seals | matte rubber', (24, 29, 31), 0.76),
        yellow=material('Markings | hazard yellow', srgb((235, 185, 42)), 0, 0.55),
        white=material('Markings | stencil ivory', srgb((218, 224, 215)), 0, 0.58),
        cyan=material('Display | cyan', srgb((105, 213, 221)), 0, 0.3, 1.2),
        green=material('Status | running', srgb((96, 213, 123)), 0, 0.25, 2),
    )
    for field, surface in vars(palette).items():
        surface['ep_paint'] = 'primary' if field == 'orange' else 'secondary' if field in {'graphite','tank','secondary'} else 'fixed'
    return palette


def aim(obj, target):
    """Rotate an object so that its local -Z axis points at `target`."""
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def attach(obj, pivot):
    """Parent `obj` to an unrotated `pivot` and keep its current world position."""
    obj.parent = pivot
    obj.location -= pivot.location
    return obj


class Kit:
    """A cleared scene with one asset collection and one presentation collection.

    Primitive builders link new objects into the asset collection. Dimensions are meters.
    """

    def __init__(self, asset_name):
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        for collection in list(bpy.data.collections):
            if collection.name != 'Collection':
                bpy.data.collections.remove(collection)
        self.asset = bpy.data.collections.get('Collection')
        self.asset.name = asset_name
        self.studio = bpy.data.collections.new('Studio_non_export')
        self.scene = bpy.context.scene
        self.scene.collection.children.link(self.studio)
        self.camera = None
        self.orthographic_scale = ORTHOGRAPHIC_SCALE
        self.socket_objects = []

    def finish(self, obj, name, surface, bevel=0):
        """Name an object, assign its material and optionally add a bevel with weighted normals."""
        obj.name = name
        obj.data.materials.append(surface)
        if bevel:
            modifier = obj.modifiers.new('Manufactured edge radius', 'BEVEL')
            modifier.width = bevel
            modifier.segments = 3
            modifier = obj.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
            modifier.keep_sharp = True
        return obj

    def box(self, name, location, dimensions, surface, bevel=0.025):
        """Add a beveled box centered at `location` with full `dimensions`."""
        bpy.ops.mesh.primitive_cube_add(size=1, location=location)
        obj = bpy.context.object
        obj.dimensions = dimensions
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        return self.finish(obj, name, surface, bevel)

    def cylinder(self, name, location, radius, depth, surface, vertices=32, direction=None):
        """Add a cylinder centered at `location`, along Z or along the `direction` vector."""
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
        obj = bpy.context.object
        if direction:
            obj.rotation_euler = Vector(direction).to_track_quat('Z', 'Y').to_euler()
        for polygon in obj.data.polygons:
            polygon.use_smooth = len(polygon.vertices) == 4
        return self.finish(obj, name, surface, 0.009)

    def torus(self, name, location, major_radius, minor_radius, surface, rotation=(0, 0, 0), major_segments=32, minor_segments=10):
        """Add a torus ring centered at `location`."""
        bpy.ops.mesh.primitive_torus_add(major_segments=major_segments, minor_segments=minor_segments, major_radius=major_radius, minor_radius=minor_radius, location=location, rotation=rotation)
        return self.finish(bpy.context.object, name, surface)

    def mesh(self, name, vertices, faces, surface, bevel=0):
        """Add an object from explicit vertices and faces."""
        data = bpy.data.meshes.new(name)
        data.from_pydata(vertices, [], faces)
        data.update()
        obj = bpy.data.objects.new(name, data)
        self.asset.objects.link(obj)
        return self.finish(obj, name, surface, bevel)

    def extrusion(self, name, profile, y_range, surface, bevel=0):
        """Add a prism from an XZ `profile` polygon extruded between the two Y values of `y_range`."""
        vertices = [(x, y, z) for y in y_range for x, z in profile]
        count = len(profile)
        faces = [tuple(reversed(range(count))), tuple(range(count, 2 * count))]
        faces += [(i, (i + 1) % count, (i + 1) % count + count, i + count) for i in range(count)]
        return self.mesh(name, vertices, faces, surface, bevel)

    def pipe(self, name, points, radius, surface):
        """Add a round tube along a smooth Bezier path through `points`."""
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
        self.asset.objects.link(obj)
        obj.data.materials.append(surface)
        return obj

    def text(self, name, content, location, size, surface, facing='-Y'):
        """Add upright text with the Blender built-in font whose readable face points along `facing`.

        `facing` is '-Y', '+Y', '+X' or '-X'; `location` is the baseline start.
        """
        curve = bpy.data.curves.new(name, 'FONT')
        curve.body = content
        curve.size = size
        curve.extrude = 0.0008
        curve.space_character = 1.1
        obj = bpy.data.objects.new(name, curve)
        self.asset.objects.link(obj)
        obj.location = location
        obj.rotation_euler = (math.pi / 2, 0, TEXT_FACING[facing])
        obj.data.materials.append(surface)
        return obj

    def empty(self, name, location):
        """Add an empty, for example a pivot that parents moving parts."""
        obj = bpy.data.objects.new(name, None)
        self.asset.objects.link(obj)
        obj.location = location
        return obj

    def socket(self, name, location):
        """Add a named arrows empty that marks an attachment point and appears in exported metrics."""
        obj = self.empty(name, location)
        obj.empty_display_type = 'ARROWS'
        obj.empty_display_size = 0.2
        self.socket_objects.append(obj)
        return obj

    def move_to_studio(self, obj):
        """Move an object from the asset collection to the presentation collection."""
        for collection in list(obj.users_collection):
            collection.objects.unlink(obj)
        self.studio.objects.link(obj)
        return obj

    def block(self, name, location, dimensions, surface, category='fabricated'):
        """Add a fabricated box with a size-based edge break."""
        return self.box(name, location, dimensions, surface, bevel_size(dimensions, category))

    def turned(self, name, location, radius, depth, surface, vertices=32, direction=None):
        """Add a turned cylinder with a proportional edge break."""
        obj = self.cylinder(name, location, radius, depth, surface, vertices, direction)
        obj.modifiers['Manufactured edge radius'].width = bevel_size((radius*2,depth))
        obj.modifiers['Manufactured edge radius'].segments = 2
        return obj

    def section(self, name, start, end, width, height, thickness, surface, shape='channel'):
        """Add a plate, channel, angle, or I-section along a straight member."""
        profiles = {
            'plate': [(-width/2,-thickness/2),(width/2,-thickness/2),(width/2,thickness/2),(-width/2,thickness/2)],
            'channel': [(-width/2,-height/2),(width/2,-height/2),(width/2,-height/2+thickness),(-width/2+thickness,-height/2+thickness),(-width/2+thickness,height/2-thickness),(width/2,height/2-thickness),(width/2,height/2),(-width/2,height/2)],
            'angle': [(-width/2,-height/2),(width/2,-height/2),(width/2,-height/2+thickness),(-width/2+thickness,-height/2+thickness),(-width/2+thickness,height/2),(-width/2,height/2)],
            'ibeam': [(-width/2,-height/2),(width/2,-height/2),(width/2,-height/2+thickness),(thickness/2,-height/2+thickness),(thickness/2,height/2-thickness),(width/2,height/2-thickness),(width/2,height/2),(-width/2,height/2),(-width/2,height/2-thickness),(-thickness/2,height/2-thickness),(-thickness/2,-height/2+thickness),(-width/2,-height/2+thickness)],
        }
        profile = profiles[shape]
        direction = Vector(end) - Vector(start)
        rotation = direction.to_track_quat('Z', 'Y')
        vertices = [Vector(start) + rotation @ Vector((x, y, z)) for z in (0, direction.length) for x, y in profile]
        count = len(profile)
        faces = [tuple(reversed(range(count))), tuple(range(count, count*2))]
        faces += [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
        return self.mesh(name, vertices, faces, surface, bevel_size((width,height,thickness),'sheet'))

    def fastener(self, name, location, surface, diameter=0.016, direction=(0,0,1)):
        """Add an ISO-proportioned hex head and washer at a mounting surface."""
        point, axis = Vector(location), Vector(direction).normalized()
        washer = self.cylinder(name + ' washer', point + axis*diameter*0.09, diameter, diameter*0.18, surface, 24, axis)
        head = self.cylinder(name, point + axis*diameter*0.5, diameter*0.87, diameter*0.64, surface, 6, axis)
        for obj in (washer, head):
            obj.modifiers['Manufactured edge radius'].width = diameter*0.045
            obj.modifiers['Manufactured edge radius'].segments = 1
        return head

    def grating(self, name, location, width, depth, surface, pitch=0.035):
        """Add a framed walkway grate with 5 mm bearing bars and 100 mm cross ties."""
        x, y, z = location
        parts = []
        for index in range(round(width/pitch)+1):
            parts.append(self.box(name+' bearing bar', (x-width/2+index*width/round(width/pitch),y,z), (0.005,depth,0.03), surface, 0))
        for index in range(round(depth/0.1)+1):
            parts.append(self.box(name+' cross tie', (x,y-depth/2+index*depth/round(depth/0.1),z+0.008), (width,0.005,0.014), surface, 0))
        for side in (-1,1):
            parts.append(self.block(name+' edge', (x+side*width/2,y,z), (0.012,depth,0.04), surface, 'sheet'))
        return parts

    def louvres(self, name, location, width, height, surface, facing='-Y'):
        """Add 45 mm pitch folded ventilation slats in a dark recess."""
        x,y,z = location
        parts = []
        for index in range(max(1,round(height/0.045))):
            slat = self.block(name, (x,y,z-height/2+index*0.045), (width,0.025,0.025), surface, 'sheet')
            slat.rotation_euler.x = -math.pi/6 if facing == '-Y' else math.pi/6
            parts.append(slat)
        return parts

    def scale_figure(self, location=(-2.8,-1.4,0)):
        """Add an original tapered 1.8 m scale mannequin to the studio."""
        surface = material('Scale | blue workwear mannequin', srgb((48,70,98)), 0, 0.61)
        x,y,z = location
        parts = []
        for name, position, dimensions in [
            ('pelvis',(0,0,0.98),(0.29,0.19,0.17)),
            ('left boot',(-0.10,-0.035,0.045),(0.12,0.20,0.09)), ('right boot',(0.10,-0.035,0.045),(0.12,0.20,0.09)),
        ]:
            parts.append(self.box('Scale figure '+name,(x+position[0],y+position[1],z+position[2]),dimensions,surface,0.03))
        vertices = [(x+side*width,y+depth,z+height) for width,height in ((0.115,1.07),(0.20,1.47)) for side,depth in ((-1,-0.10),(1,-0.10),(1,0.10),(-1,0.10))]
        parts.append(self.mesh('Scale figure tapered torso',vertices,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],surface,0.025))
        for side in (-1,1):
            for name,a,b,bottom_radius,top_radius in [
                ('thigh',(side*0.10,0,0.57),(side*0.10,0,0.95),0.055,0.08),
                ('shin',(side*0.10,0,0.11),(side*0.10,0,0.57),0.04,0.057),
                ('upper arm',(side*0.24,0,1.19),(side*0.22,0,1.44),0.043,0.057),
                ('forearm',(side*0.27,-0.025,0.94),(side*0.24,0,1.19),0.033,0.043),
            ]:
                start,end = Vector((x+a[0],y+a[1],z+a[2])),Vector((x+b[0],y+b[1],z+b[2]))
                bpy.ops.mesh.primitive_cone_add(vertices=16,radius1=bottom_radius,radius2=top_radius,depth=(end-start).length,location=(start+end)/2)
                limb = bpy.context.object
                limb.rotation_euler = (end-start).to_track_quat('Z','Y').to_euler()
                parts.append(self.finish(limb,'Scale figure '+name,surface,0.009))
        parts.append(self.cylinder('Scale figure neck',(x,y,z+1.52),0.055,0.1,surface,16))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1, location=(x,y,z+1.67))
        head = bpy.context.object
        head.scale = (0.10,0.105,0.13)
        parts.append(self.finish(head,'Scale figure head',surface))
        self.figure_objects = [self.move_to_studio(obj) for obj in parts]
        return self.figure_objects

    def build_site(self, trim_surface):
        """Add an 8 m foundation grid, daylight rig and 40 mm presentation camera."""
        self.build_studio(trim_surface)
        for obj in list(self.studio.objects):
            if obj.type == 'LIGHT' or obj.name == 'Display foundation' or obj.name.startswith('Foundation edge inlay'):
                bpy.data.objects.remove(obj, do_unlink=True)
        floor = bpy.data.objects['Studio floor']
        floor.location.z = -0.105
        floor.dimensions = (1000,1000,0.2)
        bpy.context.view_layer.objects.active = floor
        bpy.ops.object.select_all(action='DESELECT')
        floor.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        surface = material('Site | original foundation grid', srgb((138,150,154)), 0, 0.78)
        floor.data.materials.clear()
        floor.data.materials.append(surface)
        nodes,links = surface.node_tree.nodes,surface.node_tree.links
        coordinate = nodes.new('ShaderNodeTexCoord')
        separate = nodes.new('ShaderNodeSeparateXYZ')
        links.new(coordinate.outputs['Object'],separate.inputs[0])
        masks = []
        for spacing,line_width in ((8,0.020),(1,0.006)):
            axis_masks = []
            for axis in ('X','Y'):
                divide = nodes.new('ShaderNodeMath')
                divide.operation = 'DIVIDE'
                divide.inputs[1].default_value = spacing
                links.new(separate.outputs[axis],divide.inputs[0])
                fraction = nodes.new('ShaderNodeMath')
                fraction.operation = 'PINGPONG'
                fraction.inputs[1].default_value = 0.5
                links.new(divide.outputs[0],fraction.inputs[0])
                less = nodes.new('ShaderNodeMath')
                less.operation = 'LESS_THAN'
                less.inputs[1].default_value = line_width/(2*spacing)
                links.new(fraction.outputs[0],less.inputs[0])
                axis_masks.append(less.outputs[0])
            maximum = nodes.new('ShaderNodeMath')
            maximum.operation = 'MAXIMUM'
            for index, socket in enumerate(axis_masks):
                links.new(socket,maximum.inputs[index])
            masks.append(maximum.outputs[0])
        fine = nodes.new('ShaderNodeMixRGB')
        fine.inputs[1].default_value = (*srgb((138,150,154)),1)
        fine.inputs[2].default_value = (*srgb((123,134,138)),1)
        links.new(masks[1],fine.inputs[0])
        coarse = nodes.new('ShaderNodeMixRGB')
        coarse.inputs[2].default_value = (*srgb((80,91,96)),1)
        links.new(fine.outputs[0],coarse.inputs[1])
        links.new(masks[0],coarse.inputs[0])
        links.new(coarse.outputs[0],nodes.get('Principled BSDF').inputs['Base Color'])
        world_nodes = self.scene.world.node_tree.nodes
        world_links = self.scene.world.node_tree.links
        sky_coordinate = world_nodes.new('ShaderNodeTexCoord')
        sky_height = world_nodes.new('ShaderNodeSeparateXYZ')
        world_links.new(sky_coordinate.outputs['Normal'],sky_height.inputs[0])
        absolute = world_nodes.new('ShaderNodeMath')
        absolute.operation = 'ABSOLUTE'
        world_links.new(sky_height.outputs['Z'],absolute.inputs[0])
        sky = world_nodes.new('ShaderNodeValToRGB')
        sky.color_ramp.elements[0].color = (0.33,0.55,0.82,1)
        sky.color_ramp.elements[1].position = 0.40
        sky.color_ramp.elements[1].color = (0.045,0.19,0.55,1)
        world_links.new(absolute.outputs[0],sky.inputs[0])
        world_links.new(sky.outputs['Color'],world_nodes['Background'].inputs[0])
        world_nodes['Background'].inputs[1].default_value = 0.45
        self.scene.view_settings.look = 'AgX - Medium High Contrast'
        self.scene.view_settings.exposure = 0.15
        data = bpy.data.lights.new('Site sunlight','SUN')
        data.energy = 3.5
        data.angle = math.radians(2)
        data.color = (1,0.94,0.82)
        light = bpy.data.objects.new('Site sunlight',data)
        self.studio.objects.link(light)
        light.location = (-6,-4,7)
        aim(light,(0,0,0))
        self.camera.data.lens = 40

    def configure_render(self, samples, width):
        """Set metric units, denoised Cycles CPU rendering, AgX and the dark studio world."""
        scene = self.scene
        scene.unit_settings.system = 'METRIC'
        scene.unit_settings.scale_length = 1.0
        scene.render.engine = 'CYCLES'
        scene.cycles.device = 'CPU'
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
        scene.cycles.max_bounces = 6
        scene.cycles.diffuse_bounces = 3
        scene.cycles.glossy_bounces = 3
        scene.render.resolution_x = width
        scene.render.resolution_y = round(width * STILL_ASPECT)
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = 'PNG'
        scene.render.film_transparent = False
        scene.view_settings.view_transform = 'AgX'
        scene.world.color = (0.12, 0.12, 0.12)
        scene.world.use_nodes = True
        scene.world.node_tree.nodes['Background'].inputs[0].default_value = WORLD_COLOR
        scene.world.node_tree.nodes['Background'].inputs[1].default_value = WORLD_STRENGTH

    def build_studio(self, trim_surface):
        """Add the floor, the display foundation, its edge inlays, the area lights and the camera."""
        self.move_to_studio(self.box('Studio floor', (0, 0, -0.14), (200, 200, 0.2), material('Studio | slate', (0.038, 0.048, 0.062), 0.2, 0.5), 0))
        self.move_to_studio(self.box('Display foundation', (0, 0, -0.065), (FOUNDATION_SIZE, FOUNDATION_SIZE, 0.13), material('Studio | foundation', (0.095, 0.113, 0.13), 0.4, 0.4), 0.055))
        for x in (-2.23, 2.23):
            self.move_to_studio(self.box('Foundation edge inlay', (x, 0, 0.005), (0.018, 4.28, 0.005), trim_surface, 0))
        for name, location, power, color, size, target in STUDIO_LIGHTS:
            data = bpy.data.lights.new(name, 'AREA')
            data.energy = power
            data.color = color
            data.shape = 'DISK'
            data.size = size
            obj = bpy.data.objects.new(name, data)
            self.studio.objects.link(obj)
            obj.location = location
            aim(obj, target)
        camera_data = bpy.data.cameras.new('Presentation camera')
        self.camera = bpy.data.objects.new('Presentation camera', camera_data)
        self.studio.objects.link(self.camera)
        self.scene.camera = self.camera
        self.camera.data.lens = CAMERA_LENS
        self.camera.data.clip_end = 250

    def set_timeline(self, fps, frame_end, markers):
        """Set a timeline from frame 1 to `frame_end` and add (name, frame) markers."""
        self.scene.render.fps = fps
        self.scene.frame_start = 1
        self.scene.frame_end = frame_end
        for label, frame in markers:
            self.scene.timeline_markers.new(label, frame=frame)

    def export_metrics(self, path, samples):
        """Write evaluated bounds, counts and socket positions of the visible asset to JSON.

        Counts include modifiers and exclude hidden objects and the presentation collection.
        """
        depsgraph = bpy.context.evaluated_depsgraph_get()
        minimum = Vector((float('inf'),) * 3)
        maximum = Vector((float('-inf'),) * 3)
        mesh_count = 0
        triangles = 0
        for obj in self.asset.objects:
            if obj.type not in {'MESH', 'CURVE', 'FONT'} or obj.hide_render:
                continue
            evaluated = obj.evaluated_get(depsgraph)
            mesh = evaluated.to_mesh()
            mesh.calc_loop_triangles()
            mesh_count += 1
            triangles += len(mesh.loop_triangles)
            for vertex in mesh.vertices:
                point = obj.matrix_world @ vertex.co
                for axis in range(3):
                    minimum[axis] = min(minimum[axis], point[axis])
                    maximum[axis] = max(maximum[axis], point[axis])
            evaluated.to_mesh_clear()
        scene = self.scene
        metrics = {
            'units': 'meters',
            'bounds_min': list(minimum),
            'bounds_max': list(maximum),
            'dimensions': list(maximum - minimum),
            'renderable_objects': mesh_count,
            'evaluated_triangles': triangles,
            'samples': samples,
            'resolution': [scene.render.resolution_x, scene.render.resolution_y],
            'engine': 'Cycles CPU, denoised',
            'sockets': {obj.name: list(obj.location) for obj in self.asset.objects if obj in self.socket_objects or obj.name.startswith('CableSocket_')},
        }
        Path(path).write_text(json.dumps(metrics, indent=2) + '\n')
        print('ASSET_METRICS ' + json.dumps(metrics), flush=True)
        return metrics

    def render_stills(self, directory, views, names, blend_path):
        """Render each named view to `directory/<name>.png` and save the scene before the hero view.

        `views` maps a name to a (camera location, aim target) pair; 'orthographic' uses a parallel projection.
        """
        directory = Path(directory)
        directory.mkdir(exist_ok=True)
        for name in names:
            self.place_camera(views[name], 'ORTHO' if name == 'orthographic' else 'PERSP')
            for obj in getattr(self, 'figure_objects', []):
                obj.hide_render = name != 'hero'
            self.scene.render.filepath = str(directory / f'{name}.png')
            if name == 'hero':
                bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
            bpy.ops.render.render(write_still=True)
        for obj in getattr(self, 'figure_objects', []):
            obj.hide_render = False

    def place_camera(self, view, projection):
        """Move the presentation camera to a (location, target) view with 'PERSP' or 'ORTHO' projection."""
        location, target = view
        self.camera.location = location
        aim(self.camera, target)
        self.camera.data.type = projection
        self.camera.data.ortho_scale = self.orthographic_scale

    def render_animation(self, directory, view, width, samples):
        """Render the timeline from a perspective view as `directory/frame_NNNN.png` previews."""
        self.place_camera(view, 'PERSP')
        self.scene.render.resolution_x = width
        self.scene.render.resolution_y = round(width * STILL_ASPECT)
        self.scene.cycles.samples = samples
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self.scene.render.filepath = str(directory / 'frame_')
        bpy.ops.render.render(animation=True)


def key_rotation(obj, axis, keys, action_name):
    """Key one Euler rotation axis from (frame, radians) pairs and name the resulting action."""
    for frame, angle in keys:
        obj.rotation_euler[axis] = angle
        obj.keyframe_insert(data_path='rotation_euler', index=axis, frame=frame)
    obj.animation_data.action.name = action_name


def key_visibility(obj, keys, action_name=None):
    """Key render and viewport visibility from (frame, visible) pairs; optionally name the action."""
    for frame, visible in keys:
        obj.hide_render = not visible
        obj.hide_viewport = not visible
        obj.keyframe_insert(data_path='hide_render', frame=frame)
        obj.keyframe_insert(data_path='hide_viewport', frame=frame)
    if action_name:
        obj.animation_data.action.name = action_name


def key_state_window(obj, start, end, frames, action_name):
    """Key an object visible only from `start` to `end` inclusive, sampled at each of `frames`."""
    key_visibility(obj, [(frame, start <= frame <= end) for frame in frames], action_name)


def key_emission(surface, keys, action_name):
    """Key base color, emission color and emission strength from (frame, RGBA color, strength) triples."""
    shader = surface.node_tree.nodes.get('Principled BSDF')
    for frame, color, strength in keys:
        for socket_name in ('Base Color', 'Emission Color'):
            socket = shader.inputs[socket_name]
            socket.default_value = color
            socket.keyframe_insert(data_path='default_value', frame=frame)
        socket = shader.inputs['Emission Strength']
        socket.default_value = strength
        socket.keyframe_insert(data_path='default_value', frame=frame)
    surface.node_tree.animation_data.action.name = action_name
