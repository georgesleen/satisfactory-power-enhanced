"""Geometry-independent Blender delivery for EnhancedPower equipment."""
import hashlib
import heapq
import itertools
import json
import math
from pathlib import Path
import re

import bpy
import bmesh
import numpy as np
import epuv
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

RATIOS = (1.0, 0.5, 0.25, 0.12)
BAKE_DISTANCE = 0.06
UV_PADDING_PIXELS = 4
BAKE_DILATION_PIXELS = 1
TEXTURE_NAMES = ('BaseColor', 'Normal', 'AO', 'Metallic', 'Roughness', 'Emissive',
                 'EmissionMask', 'PaintMask', 'AOMasks', 'ReflectionMap')
REVIEW_IMAGE_NAMES = ('bake-check.png', 'lod-check.png', 'detailed.png',
                      'stencil-source.png', 'stencil-baked.png', 'stencil-check.png',
                      'surface-source.png', 'surface-baked.png', 'surface-check.png',
                      *(f'lod{index}.png' for index in range(len(RATIOS))))
# Smallest longest dimension in meters of a fixed body component kept at each LOD level.
OMIT_BELOW = (0, 0.16, 0.3, 0.6)
# Largest RMS surface deviation in meters that a vertex collapse may add at each LOD level.
LOD_ERROR_LIMITS = (0, 0.005, 0.015, 0.04)
# Largest triangle count of a shipped LOD as a fraction of the previous shipped LOD.
MAX_LOD_FRACTION = 0.75
# Largest RMS surface deviation in meters that a collapse may add to protected hardware at the last LOD.
PROTECTED_ERROR_LIMIT = 0.0025
# Largest bounds deviation in meters of a protected part from its LOD0 shape.
PROTECTED_BOUNDS_TOLERANCE = 0.005
# Largest distance in meters from a socket to the nearest surface of every shipped LOD.
SOCKET_SURFACE_TOLERANCE = 0.1


def select(objects, active=None):
    """Set the object selection and active object."""
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.hide_set(False)
        obj.select_set(True)
    bpy.context.view_layer.objects.active = active or objects[0]


def identifier(name):
    """Return an FBX-safe identifier."""
    return re.sub(r'[^A-Za-z0-9_]', '_', name)


def curves(obj):
    """Return animation channels from legacy or layered actions."""
    animation = obj.animation_data
    if not animation or not animation.action:
        return []
    action = animation.action
    if hasattr(action, 'fcurves'):
        return list(action.fcurves)
    result = []
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                result.extend(bag.fcurves)
    return result


def moving_root(obj):
    """Find the outermost keyed transform or named moving-part ancestor."""
    result = None
    while obj:
        if obj.name.startswith('MOVING_') or any(c.data_path in {
                'location', 'rotation_euler', 'rotation_quaternion', 'scale'} for c in curves(obj)):
            result = obj
        obj = obj.parent
    return result


def mesh_copy(source, collection, low=False):
    """Evaluate a source object into a standalone mesh."""
    states = [(m, m.show_viewport, m.show_render) for m in source.modifiers]
    old_curve = None
    if low:
        for modifier, _, _ in states:
            if modifier.type in {'BEVEL', 'WEIGHTED_NORMAL', 'SUBSURF'}:
                modifier.show_viewport = modifier.show_render = False
        if source.type == 'CURVE':
            old_curve = (source.data.resolution_u, source.data.bevel_resolution)
            source.data.resolution_u = 3
            source.data.bevel_resolution = 1
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    data = bpy.data.meshes.new_from_object(source.evaluated_get(graph), depsgraph=graph)
    obj = bpy.data.objects.new(source.name + ('_low' if low else '_high'), data)
    collection.objects.link(obj)
    data.transform(source.matrix_world)
    if source.matrix_world.to_3x3().determinant() < 0:
        bm = bmesh.new()
        bm.from_mesh(data)
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
        bm.to_mesh(data)
        bm.free()
    for modifier, viewport, render in states:
        modifier.show_viewport, modifier.show_render = viewport, render
    if old_curve:
        source.data.resolution_u, source.data.bevel_resolution = old_curve
    return obj


def join(objects, name, pivot):
    """Join objects into a mesh in the supplied pivot space."""
    select(objects)
    if len(objects) > 1:
        bpy.ops.object.join()
    obj = bpy.context.object
    world = obj.matrix_world.copy()
    obj.data.transform(pivot.inverted() @ world)
    obj.matrix_world = pivot
    obj.name = name
    return obj


def material(name):
    """Create a node material with a Principled shader."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    return mat


def image(name, size, color=False):
    """Create a floating-point bake target."""
    img = bpy.data.images.new(name, width=size, height=size, alpha=False, float_buffer=True)
    if name == 'Normal':
        img.generated_color = (0.5, 0.5, 1.0, 1.0)
    elif name == 'AO':
        img.generated_color = (1.0, 1.0, 1.0, 1.0)
    img.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
    return img


def target(obj, img):
    """Assign the active image node used by Cycles baking."""
    mat = obj.data.materials[0]
    nodes = mat.node_tree.nodes
    node = nodes.get('Bake target') or nodes.new('ShaderNodeTexImage')
    node.name = 'Bake target'
    node.image = img
    nodes.active = node


def channel_material(original, channel):
    """Create an emission shader exposing a source material channel."""
    mat = original.copy()
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    output = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
    emit = nodes.new('ShaderNodeEmission')
    if channel == 'PaintMask':
        role = original.get('ep_paint', '')
        if not role:
            role = 'primary' if original.name.startswith('Enamel |') else (
                'secondary' if original.name.startswith(('Structure |', 'Tank |')) else 'fixed')
        emit.inputs['Color'].default_value = {'primary': (1, 0, 0, 1),
            'secondary': (0, 1, 0, 1), 'fixed': (0, 0, 0, 1)}[role]
    elif channel == 'EmissionMask':
        value = min(1, max(0, shader.inputs['Emission Strength'].default_value)) if shader else 0
        emit.inputs['Color'].default_value = (value, value, value, 1)
    elif shader:
        socket = shader.inputs[channel]
        if socket.is_linked:
            links.new(socket.links[0].from_socket, emit.inputs['Color'])
        else:
            value = socket.default_value
            if isinstance(value, (int, float)):
                value = (value, value, value, 1)
            emit.inputs['Color'].default_value = value
        if channel == 'Emission Color':
            emit.inputs['Strength'].default_value = shader.inputs['Emission Strength'].default_value
    links.new(emit.outputs[0], output.inputs['Surface'])
    return mat


def unwrap(objects, size):
    """Unwrap and normalize all shared-atlas islands together."""
    select(objects)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(45), island_margin=0.001)
    bpy.ops.object.mode_set(mode='OBJECT')
    epuv.pack_mesh_objects(objects, size, UV_PADDING_PIXELS)
    select(objects)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.seams_from_islands(mark_seams=True, mark_sharp=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in objects:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        for edge in bm.edges:
            if edge.is_manifold:
                edge.smooth = edge.calc_face_angle() < math.radians(60)
        bm.to_mesh(obj.data)
        bm.free()
        select([obj])
        modifier = obj.modifiers.new('Fixed bake triangulation', 'TRIANGULATE')
        bpy.ops.object.modifier_apply(modifier=modifier.name)


def save_texture(img, directory, name):
    """Save a completed texture stage as a PNG."""
    img.filepath_raw = str(directory / f'{name}.png')
    img.file_format = 'PNG'
    img.save()
    print(f'BAKE_SAVED {name}', flush=True)


def bake(parts, size, directory):
    """Bake surface channels and tangent normals into shared UV images."""
    components = [component for part in parts for component in part['components']]
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 8
    scene.render.bake.margin = BAKE_DILATION_PIXELS
    scene.render.bake.use_clear = False
    scene.render.bake.use_selected_to_active = True
    scene.render.bake.cage_extrusion = BAKE_DISTANCE
    scene.render.bake.max_ray_distance = BAKE_DISTANCE * 2
    scene.render.bake.normal_space = 'TANGENT'
    scene.render.bake.normal_r = 'POS_X'
    scene.render.bake.normal_b = 'POS_Z'
    scene.render.bake.normal_g = 'NEG_Y'
    passes = {'BaseColor': 'Base Color', 'Roughness': 'Roughness',
              'Metallic': 'Metallic', 'Emissive': 'Emission Color', 'PaintMask': 'PaintMask',
              'EmissionMask': 'EmissionMask', 'Normal': None}
    textures = {}
    for name, channel in passes.items():
        print(f'BAKE_PASS {name} size={size} samples=8 receivers={len(components)}', flush=True)
        img = image(name, size, name in {'BaseColor', 'Emissive'})
        for component in components:
            low, high = component['low'], component['high']
            saved = [list(obj.data.materials) for obj in high]
            if channel:
                for obj in high:
                    originals = list(obj.data.materials)
                    obj.data.materials.clear()
                    for mat in originals:
                        obj.data.materials.append(channel_material(mat, channel))
            target(low, img)
            select(high + [low], low)
            bpy.ops.object.bake(type='EMIT' if channel else 'NORMAL')
            for obj, mats in zip(high, saved):
                obj.data.materials.clear()
                for mat in mats:
                    obj.data.materials.append(mat)
        textures[name] = img
        save_texture(img, directory, name)
    for part in parts:
        for obj in part['high']:
            obj.hide_render = True
    scene.render.bake.use_selected_to_active = False
    scene.cycles.samples = 24
    print(f'BAKE_PASS AO size={size} samples=24 receivers={len(components)}', flush=True)
    ao = image('AO', size)
    for component in components:
        target(component['low'], ao)
    select([component['low'] for component in components])
    bpy.ops.object.bake(type='AO')
    textures['AO'] = ao
    save_texture(ao, directory, 'AO')
    channels = {}
    for name in ('AO', 'PaintMask', 'Metallic', 'Roughness', 'EmissionMask'):
        pixels = np.empty(size * size * 4, dtype=np.float32)
        textures[name].pixels.foreach_get(pixels)
        channels[name] = pixels.reshape(-1, 4)
    for name, sources in {
            'AOMasks': [('AO', 0), ('PaintMask', 0), ('PaintMask', 1)],
            'ReflectionMap': [('Metallic', 0), ('Roughness', 0), ('EmissionMask', 0)]}.items():
        packed = np.ones((size * size, 4), dtype=np.float32)
        for channel, (source, component) in enumerate(sources):
            packed[:, channel] = channels[source][:, component]
        img = image(name, size)
        img.pixels.foreach_set(packed.ravel())
        textures[name] = img
    for name in ('AOMasks', 'ReflectionMap'):
        save_texture(textures[name], directory, name)
    return textures


def preview_material(textures, asset_name):
    """Build the asset-specific Blender preview shader from the baked maps."""
    mat = material(f'M_{identifier(asset_name)}_Baked')
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes.get('Principled BSDF')
    for name, socket in [('BaseColor', 'Base Color'), ('Roughness', 'Roughness'),
                         ('Metallic', 'Metallic'), ('Emissive', 'Emission Color')]:
        node = nodes.new('ShaderNodeTexImage')
        node.image = textures[name]
        links.new(node.outputs['Color'], shader.inputs[socket])
    shader.inputs['Emission Strength'].default_value = 1
    node = nodes.new('ShaderNodeTexImage')
    node.image = textures['Normal']
    separate = nodes.new('ShaderNodeSeparateColor')
    combine = nodes.new('ShaderNodeCombineColor')
    invert = nodes.new('ShaderNodeMath')
    invert.operation = 'SUBTRACT'
    invert.inputs[0].default_value = 1
    links.new(node.outputs['Color'], separate.inputs[0])
    links.new(separate.outputs[0], combine.inputs[0])
    links.new(separate.outputs[1], invert.inputs[1])
    links.new(invert.outputs[0], combine.inputs[1])
    links.new(separate.outputs[2], combine.inputs[2])
    normal = nodes.new('ShaderNodeNormalMap')
    links.new(combine.outputs[0], normal.inputs['Color'])
    links.new(normal.outputs[0], shader.inputs['Normal'])
    return mat


def cross2(a, b):
    """Return the scalar two-dimensional cross product."""
    return a[0] * b[1] - a[1] * b[0]


def intersection_area(first, second):
    """Compute convex triangle intersection area by half-plane clipping."""
    polygon = [tuple(p) for p in first]
    orientation = 1 if cross2(second[1] - second[0], second[2] - second[0]) > 0 else -1
    for a, b in zip(second, np.roll(second, -1, axis=0)):
        edge = b - a
        clipped = []
        if not polygon:
            return 0
        previous = polygon[-1]
        previous_distance = orientation * cross2(edge, (previous[0] - a[0], previous[1] - a[1]))
        for current in polygon:
            distance = orientation * cross2(edge, (current[0] - a[0], current[1] - a[1]))
            if (distance >= 0) != (previous_distance >= 0):
                factor = previous_distance / (previous_distance - distance)
                clipped.append((previous[0] + factor * (current[0] - previous[0]),
                                previous[1] + factor * (current[1] - previous[1])))
            if distance >= 0:
                clipped.append(current)
            previous, previous_distance = current, distance
        polygon = clipped
    if len(polygon) < 3:
        return 0
    return abs(sum(cross2(a, b) for a, b in zip(polygon, polygon[1:] + polygon[:1]))) / 2


def overlap_area(triangles):
    """Measure pairwise UV intersection area using a spatial candidate grid."""
    grid = {}
    total, intersections = 0.0, 0
    for index, triangle in enumerate(triangles):
        low = np.floor(triangle.min(axis=0) * 64).astype(int)
        high = np.floor(triangle.max(axis=0) * 64).astype(int)
        candidates = set()
        for x in range(low[0], high[0] + 1):
            for y in range(low[1], high[1] + 1):
                cell = grid.setdefault((x, y), [])
                candidates.update(cell)
                cell.append(index)
        for previous in candidates:
            other = triangles[previous]
            if np.any(triangle.max(axis=0) <= other.min(axis=0)) or np.any(other.max(axis=0) <= triangle.min(axis=0)):
                continue
            area = intersection_area(triangle, other)
            if area > 1e-12:
                total += area
                intersections += 1
    return {'pairwise_overlap_area': total, 'intersecting_triangle_pairs': intersections}


def uv_layout_signature(objects):
    """Hash active UV0 coordinates per named receiver for matching layout evidence."""
    digest = hashlib.sha256()
    for obj in sorted(objects, key=lambda item: item.name):
        digest.update(obj.name.encode() + b'\0')
        coordinates = np.empty(len(obj.data.uv_layers.active.data) * 2, dtype=np.float32)
        obj.data.uv_layers.active.data.foreach_get('uv', coordinates)
        digest.update(coordinates.tobytes())
    return digest.hexdigest()


def uv_metrics(objects, size, resolution=1024):
    """Measure UV intersections, sampled coverage and face-area texel density."""
    coverage = np.zeros((resolution, resolution), dtype=np.uint16)
    density, outside, degenerate = [], 0, 0
    triangles, surface_area, uv_area_total = [], 0.0, 0.0
    for obj in objects:
        mesh = obj.data
        mesh.calc_loop_triangles()
        uv = mesh.uv_layers.active.data
        outside += sum(any(v < -1e-6 or v > 1 + 1e-6 for v in item.uv) for item in uv)
        for tri in mesh.loop_triangles:
            points = np.array([uv[i].uv[:] for i in tri.loops], dtype=np.float64)
            a, b, c = points
            determinant = cross2(b - a, c - a)
            uv_area = abs(determinant) / 2
            if tri.area > 1e-10 and uv_area <= 1e-14:
                degenerate += 1
            elif tri.area > 1e-10:
                density.append(math.sqrt(uv_area / tri.area) * size / 100)
                surface_area += tri.area
                uv_area_total += uv_area
            if abs(determinant) < 1e-14:
                continue
            triangles.append(points)
            lo = np.maximum(np.floor(points.min(axis=0) * resolution).astype(int), 0)
            hi = np.minimum(np.ceil(points.max(axis=0) * resolution).astype(int), resolution)
            if np.any(hi <= lo):
                continue
            yy, xx = np.mgrid[lo[1]:hi[1], lo[0]:hi[0]]
            px, py = (xx + 0.5) / resolution - a[0], (yy + 0.5) / resolution - a[1]
            u = (px * (c[1] - a[1]) - py * (c[0] - a[0])) / determinant
            v = ((b[0] - a[0]) * py - (b[1] - a[1]) * px) / determinant
            inside = (u > 1e-8) & (v > 1e-8) & (u + v < 1 - 1e-8)
            coverage[lo[1]:hi[1], lo[0]:hi[0]] += inside.astype(np.uint16)
    occupied = np.count_nonzero(coverage)
    geometric = overlap_area(triangles)
    return {'overlap_percent_sampled': 100 * np.count_nonzero(coverage > 1) / max(occupied, 1),
            'sample_resolution': resolution, 'outside_0_1_loop_count': int(outside),
            'zero_area_uv_triangles': degenerate,
            'coverage_percent_sampled': 100 * occupied / resolution ** 2,
            'geometric_overlap': {**geometric, 'pairwise_overlap_area_percent':
                100 * geometric['pairwise_overlap_area'] / max(uv_area_total, 1e-20)},
            'texel_density_px_per_cm': {'min': min(density, default=0),
                'max': max(density, default=0), 'median': float(np.median(density)) if density else 0,
                'area_weighted': math.sqrt(uv_area_total / max(surface_area, 1e-20)) * size / 100,
                'p05': float(np.percentile(density, 5)) if density else 0,
                'p95': float(np.percentile(density, 95)) if density else 0}}


def topology(obj):
    """Count triangles and non-manifold edges."""
    obj.data.calc_loop_triangles()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    count = sum(not edge.is_manifold for edge in bm.edges)
    bm.free()
    return {'triangles': len(obj.data.loop_triangles), 'non_manifold_edges': count}


def bounds(obj):
    """Return world-space extrema."""
    points = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return (Vector(tuple(min(p[i] for p in points) for i in range(3))),
            Vector(tuple(max(p[i] for p in points) for i in range(3))))


def edge_feature(edge, uv):
    """Classify an edge as open, non-manifold, a UV seam or sharp crease, or None."""
    if len(edge.link_faces) == 1:
        return ('open',)
    if len(edge.link_faces) != 2:
        return ('nonmanifold',)
    first, second = edge.link_loops
    uvs = []
    for loop in (first, second):
        uvs.append({loop.vert: loop[uv].uv, loop.link_loop_next.vert: loop.link_loop_next[uv].uv})
    seam = any((uvs[0][vert] - uvs[1][vert]).length > 1e-6 for vert in edge.verts)
    sharp = not edge.smooth
    return (seam, sharp) if seam or sharp else None


def collapse_targets(vert, uv):
    """Return the neighbors a vertex may collapse onto without moving a seam or crease off its line."""
    if not vert.is_manifold:
        return []
    marked = [(edge, feature) for edge in vert.link_edges
              for feature in [edge_feature(edge, uv)] if feature]
    if not marked:
        return [edge.other_vert(vert) for edge in vert.link_edges]
    if len(marked) == 2 and marked[0][1] == marked[1][1] != ('nonmanifold',):
        return [edge.other_vert(vert) for edge, _ in marked]
    return []


def face_fans(vert, uv):
    """Group the faces around a vertex into fans separated by feature edges."""
    remaining = set(vert.link_faces)
    groups = []
    while remaining:
        stack = [remaining.pop()]
        group = set(stack)
        while stack:
            face = stack.pop()
            for edge in face.edges:
                if vert in edge.verts and edge_feature(edge, uv) is None:
                    for other in edge.link_faces:
                        if other in remaining:
                            remaining.discard(other)
                            group.add(other)
                            stack.append(other)
        groups.append(group)
    return groups


def collapse_plan(vert, target, uv):
    """Return the UV of each surviving face loop after collapsing vert onto target, or None if invalid."""
    edge = next((e for e in vert.link_edges if e.other_vert(vert) is target), None)
    if edge is None:
        return None
    opposite = {loop.link_loop_prev.vert for loop in edge.link_loops}
    vert_ring = {e.other_vert(vert) for e in vert.link_edges}
    target_ring = {e.other_vert(target) for e in target.link_edges}
    if vert_ring & target_ring != opposite:
        return None
    plan = {}
    for group in face_fans(vert, uv):
        source = next((face for face in group if target in face.verts), None)
        if source is None:
            return None
        target_uv = next(loop for loop in source.loops if loop.vert is target)[uv].uv.copy()
        for face in group:
            if target in face.verts:
                continue
            loops = list(face.loops)
            old = [loop.vert.co for loop in loops]
            new = [target.co if loop.vert is vert else loop.vert.co for loop in loops]
            old_normal = (old[1] - old[0]).cross(old[2] - old[0])
            new_normal = (new[1] - new[0]).cross(new[2] - new[0])
            if new_normal.length < 1e-10 or old_normal.normalized().dot(new_normal.normalized()) < 0.5:
                return None
            old_uv = [loop[uv].uv for loop in loops]
            new_uv = [target_uv if loop.vert is vert else loop[uv].uv for loop in loops]
            old_area = cross2(old_uv[1] - old_uv[0], old_uv[2] - old_uv[0])
            new_area = cross2(new_uv[1] - new_uv[0], new_uv[2] - new_uv[0])
            if abs(new_area) < 1e-12 or (old_area > 0) != (new_area > 0):
                return None
            plan[face] = target_uv
    return plan


def reduce_mesh(obj, ratio, error_limit):
    """Collapse vertices onto neighbors until a triangle ratio or RMS error limit is reached.

    UV seams, sharp creases and open borders only shorten along their own line, so UV0 stays valid.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    uv = bm.loops.layers.uv.active
    quadrics = {vert: [np.zeros((4, 4)), 0.0] for vert in bm.verts}
    for face in bm.faces:
        plane = np.array([*face.normal, -face.normal.dot(face.verts[0].co)])
        area = face.calc_area()
        for vert in face.verts:
            quadrics[vert][0] += area * np.outer(plane, plane)
            quadrics[vert][1] += area
    order = itertools.count()
    heap = []

    def error(vert, target):
        point = np.array([*target.co, 1.0])
        quadric = quadrics[vert][0] + quadrics[target][0]
        return math.sqrt(max(point @ quadric @ point, 0) / max(quadrics[vert][1] + quadrics[target][1], 1e-20))

    def push(vert):
        for target in collapse_targets(vert, uv):
            value = error(vert, target)
            if value <= error_limit:
                heapq.heappush(heap, (value, next(order), vert, target))

    for vert in list(bm.verts):
        push(vert)
    goal = len(bm.faces) * ratio
    while heap and len(bm.faces) > goal:
        value, _, vert, target = heapq.heappop(heap)
        if not vert.is_valid or not target.is_valid or target not in collapse_targets(vert, uv):
            continue
        current = error(vert, target)
        if current > error_limit:
            continue
        if current > value + 1e-12:
            heapq.heappush(heap, (current, next(order), vert, target))
            continue
        plan = collapse_plan(vert, target, uv)
        if plan is None:
            continue
        for face, coordinate in plan.items():
            next(loop for loop in face.loops if loop.vert is vert)[uv].uv = coordinate
        merged = [quadrics[vert][0] + quadrics[target][0], quadrics[vert][1] + quadrics[target][1]]
        bmesh.ops.pointmerge(bm, verts=[target, vert], merge_co=target.co)
        survivor = target if target.is_valid else vert
        quadrics[survivor] = merged
        for neighbor in [survivor] + [e.other_vert(survivor) for e in survivor.link_edges]:
            push(neighbor)
    bm.to_mesh(obj.data)
    bm.free()


def surface_distance(objects, point):
    """Return the distance in meters from a world point to the nearest surface of the objects."""
    best = math.inf
    for obj in objects:
        tree = BVHTree.FromPolygons([obj.matrix_world @ vertex.co for vertex in obj.data.vertices],
                                    [polygon.vertices[:] for polygon in obj.data.polygons])
        hit = tree.find_nearest(point)
        if hit[0] is not None:
            best = min(best, hit[3])
    return best


def collision(objects, collection, mesh_name):
    """Build convex box collision from the largest non-contained part bounds."""
    candidates = []
    for obj in objects:
        low, high = bounds(obj)
        dimensions = high - low
        if min(dimensions) >= 0.12 and max(dimensions) >= 0.5:
            candidates.append((dimensions.x * dimensions.y * dimensions.z, low, high))
    boxes, result = [], []
    for _, low, high in sorted(candidates, key=lambda item: item[0], reverse=True):
        if any(all(low[i] >= a[i] and high[i] <= b[i] for i in range(3)) for a, b in boxes):
            continue
        if len(boxes) == 16:
            break
        boxes.append((low, high))
        vertices = [(x, y, z) for x in (low.x, high.x) for y in (low.y, high.y) for z in (low.z, high.z)]
        mesh = bpy.data.meshes.new('Collision box')
        mesh.from_pydata(vertices, [], [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
                                      (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
        obj = bpy.data.objects.new(f'UCX_{mesh_name}_{len(result):02}', mesh)
        collection.objects.link(obj)
        result.append(obj)
    return result


def render_checks(parts, originals, studio, output):
    """Render matched-camera detailed, baked and LOD contact sheets."""
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = 640, 640
    scene.render.resolution_percentage = 100
    scene.cycles.samples = 12
    scene.render.image_settings.file_format = 'PNG'
    panels = []
    for level in [-1] + list(range(max(len(part['lods']) for part in parts))):
        for obj in originals:
            obj.hide_render = level != -1
        for part in parts:
            for index, obj in enumerate(part['lods']):
                obj.hide_render = level < 0 or obj is not part['lods'][min(level, len(part['lods']) - 1)]
                obj.matrix_world = part['pivot']
        scene.render.filepath = str(output / ('detailed.png' if level == -1 else f'lod{level}.png'))
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(scene.render.filepath, check_existing=False)
        pixels = np.empty(640 * 640 * 4, dtype=np.float32)
        img.pixels.foreach_get(pixels)
        panels.append(pixels.reshape(640, 640, 4))
    for name, arrays in [('bake-check', panels[:2]), ('lod-check', panels[1:])]:
        sheet = bpy.data.images.new(name, width=640 * len(arrays), height=640, alpha=True)
        sheet.pixels.foreach_set(np.concatenate(arrays, axis=1).ravel())
        sheet.filepath_raw = str(output / f'{name}.png')
        sheet.file_format = 'PNG'
        sheet.save()
    for part in parts:
        for index, obj in enumerate(part['lods']):
            obj.hide_render = index != 0


def animation_record(owner):
    """Describe source channels without claiming runtime animation delivery."""
    return [{'path': curve.data_path, 'component': curve.array_index,
             'keys': [list(point.co) for point in curve.keyframe_points]}
            for curve in curves(owner)]


def state_inventory(objects):
    """Inventory source text variants, transform actions and animated materials."""
    states, materials = {}, {}
    for obj in objects:
        channels = animation_record(obj)
        if channels or obj.type == 'FONT':
            states[obj.name] = {'type': obj.type, 'visible_at_frame_1': not obj.hide_render,
                                'channels': channels}
            if obj.type == 'FONT':
                states[obj.name]['text'] = obj.data.body
        if obj.type in {'MESH', 'CURVE', 'FONT'}:
            for mat in obj.data.materials:
                if mat and mat.node_tree and animation_record(mat.node_tree):
                    record = materials.setdefault(mat.name, {
                        'channels': animation_record(mat.node_tree), 'source_objects': []})
                    record['source_objects'].append(obj.name)
    return {'mode': 'Frame 1 visual snapshot only', 'fbx_animation_tracks': 0,
            'source_states': states, 'animated_materials': materials,
            'unreal_runtime_setup': 'Separate moving static meshes and pivot sockets only; Blueprint transform/state logic, visibility variants, display updates and dynamic indicator materials are not exported'}


def rigid_transform(matrix):
    """Return a transform with the source location and rotation but unit scale."""
    return Matrix.Translation(matrix.translation) @ matrix.to_quaternion().to_matrix().to_4x4()


def convexity(obj):
    """Measure closed convex topology and positive world-space volume."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    bm.normal_update()
    closed = all(edge.is_manifold for edge in bm.edges)
    volume = bm.calc_volume(signed=True)
    violation = max((face.normal.dot(vertex.co - face.verts[0].co)
                     for face in bm.faces for vertex in bm.verts), default=0)
    bm.free()
    return {'closed': closed, 'signed_volume_cm3': volume * 1000000,
            'maximum_halfspace_violation_m': violation,
            'convex_closed_positive_volume': closed and volume > 0 and violation < 1e-6}


def export_fbx(path, objects):
    """Export selected geometry and helpers in centimeter FBX units."""
    select(objects)
    bpy.ops.export_scene.fbx(filepath=str(path),
        use_selection=True, object_types={'MESH', 'EMPTY'},
        apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
        axis_forward='Y', axis_up='Z', bake_space_transform=True,
        mesh_smooth_type='FACE', use_tspace=True, use_triangles=True,
        bake_anim=False, add_leaf_bones=False, path_mode='STRIP')


def reimport_check(path, meshes, extras):
    """Round-trip an FBX in an isolated scene and compare exported contracts."""
    previous = bpy.context.window.scene
    check_scene = bpy.data.scenes.new('FBX round-trip')
    bpy.context.window.scene = check_scene
    existing = {'meshes': set(bpy.data.meshes), 'materials': set(bpy.data.materials)}
    bpy.ops.import_scene.fbx(filepath=str(path), use_image_search=False,
                            use_custom_normals=True)
    imported = {re.sub(r'\.\d{3}$', '', o.name): o for o in check_scene.objects}
    result = {'meshes': {}, 'sockets': {}, 'collision_hull_count': 0, 'passed': True}
    for source in meshes:
        obj = imported.get(source.name)
        if obj is None:
            result['meshes'][source.name] = {'missing': True}
            result['passed'] = False
            continue
        actual = bounds(obj)
        expected = bounds(source)
        error = max(abs(actual[end][axis] - expected[end][axis])
                    for end in range(2) for axis in range(3)) * 100
        materials = [re.sub(r'\.\d{3}$', '', m.name) for m in obj.data.materials]
        expected_materials = [m.name for m in source.data.materials]
        count = topology(obj)['triangles']
        match = error < 0.01 and materials == expected_materials and count == topology(source)['triangles']
        scale = list(obj.matrix_world.to_scale())
        determinant = obj.matrix_world.to_3x3().determinant()
        uniform = max(scale) - min(scale) < 1e-6
        match &= determinant > 0 and uniform
        result['meshes'][source.name] = {'bounds_cm': [[v * 100 for v in end] for end in actual],
            'bounds_max_error_cm': error, 'materials': materials, 'triangles': count,
            'world_scale': scale, 'world_determinant': determinant,
            'has_nonuniform_scale': not uniform,
            'passed': match}
        result['passed'] &= match
    for source in extras:
        obj = imported.get(source.name)
        if source.name.startswith('UCX_'):
            result['collision_hull_count'] += int(obj is not None and obj.type == 'MESH')
            if obj:
                result.setdefault('collision_hulls', {})[source.name] = convexity(obj)
                result['passed'] &= result['collision_hulls'][source.name]['convex_closed_positive_volume']
        elif source.name.startswith('SOCKET_'):
            rigid = rigid_transform(obj.matrix_world) if obj else None
            error = max(abs(rigid[row][col] - source.matrix_world[row][col])
                        for row in range(4) for col in range(4)) if obj else None
            scale = list(obj.matrix_world.to_scale()) if obj else None
            uniform = scale is not None and max(scale) - min(scale) < 1e-6
            result['sockets'][source.name] = {'rigid_transform_max_error': error,
                'location_cm': [v * 100 for v in obj.matrix_world.translation] if obj else None,
                'importer_object_scale': scale,
                'expected_matrix_m': [list(row) for row in source.matrix_world],
                'imported_matrix_m': [list(row) for row in obj.matrix_world] if obj else None}
            result['passed'] &= error is not None and error < 1e-4 and uniform
    result['passed'] &= result['collision_hull_count'] == sum(o.name.startswith('UCX_') for o in extras)
    bpy.context.window.scene = previous
    objects = list(check_scene.objects)
    bpy.data.scenes.remove(check_scene)
    for obj in objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    for collection_name, before in existing.items():
        collection = getattr(bpy.data, collection_name)
        for block in set(collection) - before:
            collection.remove(block)
    return result


def transform_fixture(collection, surface, output):
    """Exercise mirrored nonuniform source geometry and rigid socket round-tripping."""
    mesh = bpy.data.meshes.new('Transform fixture source')
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)], [],
                     [(0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)])
    source = bpy.data.objects.new('Transform fixture source', mesh)
    collection.objects.link(source)
    source.location = (0.17, -0.2, 0.3)
    source.rotation_euler = (0.1, 0.2, 0.3)
    source.scale = (-1, 2, 0.5)
    bpy.context.view_layer.update()
    obj = mesh_copy(source, collection)
    obj.name = 'SM_TransformCheck'
    obj.data.materials.append(surface)
    obj.data.uv_layers.new()
    for loop, uv in zip(obj.data.loops, obj.data.uv_layers.active.data):
        point = obj.data.vertices[loop.vertex_index].co
        uv.uv = (point.x, point.y)
    socket = bpy.data.objects.new('SOCKET_SM_TransformCheck_00', None)
    collection.objects.link(socket)
    socket.matrix_world = rigid_transform(source.matrix_world)
    socket.location = source.matrix_world @ Vector((0.3, 0.2, 0.1))
    hulls = collision([obj], collection, obj.name)
    directory = output / 'validation'
    directory.mkdir(exist_ok=True)
    path = directory / 'negative-nonuniform.fbx'
    export_fbx(path, [obj, socket] + hulls)
    result = reimport_check(path, [obj], [socket] + hulls)
    result['source_scale'] = list(source.scale)
    result['source_determinant'] = source.matrix_world.to_3x3().determinant()
    result['canonical_geometry'] = convexity(obj)
    result['passed'] &= result['canonical_geometry']['convex_closed_positive_volume']
    for item in [source, obj, socket] + hulls:
        bpy.data.objects.remove(item, do_unlink=True)
    return result


def material_profile():
    """Describe the generic appearance reference and unverified FactoryGame paint profile."""
    return {
        'name': 'generic_colored_PBR_reference',
        'factory_game_paint_appearance': 'UNVERIFIED',
        'swatch_faithful_customizer_ready': False,
        'nonlegacy_instance_flags': {'CanBePainted': True, 'bUseLegacyPaintTextures': False},
        'base_paint_formula': 'lerp(Albedo, Albedo*saturate(primaryColor*G+secondaryColor*B), saturate((G+B)*PaintTintIntensity))',
        'paint_tint_intensity_default': 1,
        'warning': 'Multiplicative tint can double-tint or desaturate authored amber and colored secondary regions; correct channel packing does not establish swatch-faithful paint appearance',
        'required_decision': 'Explicit texture-authoring/material-profile choice, then game-default palette, finishes and FactoryGame-context verification',
    }


def write_json_atomic(path, data):
    """Replace a JSON artifact atomically after its complete contents are written."""
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    temporary.replace(path)


def write_assembly(asset_name, directory, report):
    """Write engine-relative assembly transforms and their authoring-space references."""
    meshes = {}
    signs = (1, -1, 1, 1)
    basis = [[signs[row] if row == col else 0 for col in range(4)] for row in range(4)]
    root = [[0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    for key, part in report['parts'].items():
        name = f'SM_{identifier(asset_name)}_{identifier(key)}'
        source_transform = [row[:] for row in part['pivot_matrix_m']]
        for axis in range(3):
            source_transform[axis][3] *= 100
        engine_transform = [[signs[row] * source_transform[row][col] * signs[col]
                             for col in range(4)] for row in range(4)]
        helper = report['socket_export_names'].get('Pivot_' + key)
        meshes[key] = {'file': name + '.fbx', 'lod0_render_object': name + '_LOD0',
            'parent': None if key == 'Body' else 'Body',
            'role': 'fixed' if key == 'Body' else 'independently moving',
            'source_reference_transform_cm': source_transform,
            'relative_transform_cm': root if key == 'Body' else engine_transform,
            'transform_space': 'Unreal assembly root centimeters' if key == 'Body' else 'Unreal Body-relative centimeters',
            'body_pivot_helper': helper, 'body_pivot_socket': helper.removeprefix('SOCKET_') if helper else None,
            'lod_count': len(part['lods']), 'lod_triangles': [lod['triangles'] for lod in part['lods']],
            'material_slots': part['fbx_round_trip']['meshes'][name + '_LOD0']['materials']}
    manifest = {'schema': 2, 'units': 'centimeters', 'source_reference_frame': 1,
        'unreal_import_verified': False, 'body_file': meshes['Body']['file'], 'static_meshes': meshes,
        'source': report['source'], 'source_sha256': report['source_sha256'],
        'generic_blender_bake_validation': report['generic_blender_bake_validation'],
        'material_profile': report['material_profile'],
        'source_to_asset_basis': basis, 'assembly_root_transform_cm': root,
        'global_root_is_explanatory_duplicate': True,
        'product_files_sha256': dict(report['files_sha256']),
        'validation_manifest': 'validation.json',
        'root_application': 'Body.relative_transform_cm already contains this root; apply once, not again',
        'service_front_asset_axis': [0, 1, 0], 'assembly_front_axis': [1, 0, 0],
        'orientation': 'Raw FBX maps Blender(x,y,z) to UE(x,-y,z); Body root yaw -90 makes service front +X',
        'socket_helpers': report['socket_export_names'],
        'unreal_socket_names': {key: value.removeprefix('SOCKET_') for key, value in report['socket_export_names'].items()},
        'source_attachment_positions_cm': report['sockets_cm'],
        'asset_attachment_positions_cm': {key: [point[0], -point[1], point[2]] for key, point in report['sockets_cm'].items()},
        'fbx_animation_tracks': 0, 'state_inventory': 'validation.json:state_delivery',
        'socket_import_contract': 'One socket-bearing render asset per FBX; final ownership and transforms require the separate Unreal report',
        'engine_reference': 'https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-static-mesh-pipeline-in-unreal-engine?application_version=5.6'}
    write_json_atomic(Path(directory) / 'assembly.json', manifest)
    return manifest


def prepare_output(output, asset_name):
    """Invalidate prior completion evidence and remove only exporter-owned stale files."""
    (output / 'delivery-complete.json').unlink(missing_ok=True)
    names = ('validation.json', 'assembly.json', 'hashes.json', 'SHA256SUMS', 'game.blend',
             'validation.json.tmp', 'assembly.json.tmp', 'delivery-complete.json.tmp', *REVIEW_IMAGE_NAMES)
    for name in names:
        (output / name).unlink(missing_ok=True)
    for path in output.glob(f'SM_{identifier(asset_name)}_*.fbx'):
        path.unlink()
    (output / 'validation' / 'negative-nonuniform.fbx').unlink(missing_ok=True)
    for name in TEXTURE_NAMES:
        (output / 'textures' / f'{name}.png').unlink(missing_ok=True)
    unknown = list(output.glob('SM_*.fbx')) + list((output / 'textures').glob('*.png'))
    if unknown:
        raise ValueError(f'Unmanaged files in export output; choose a separate directory: {unknown}')


def delivered_file_hashes(output, asset_name):
    """Hash exported meshes, textures, derived scene and review images."""
    paths = list(output.glob(f'SM_{identifier(asset_name)}_*.fbx'))
    paths += [output / 'textures' / f'{name}.png' for name in TEXTURE_NAMES]
    paths += [output / name for name in REVIEW_IMAGE_NAMES]
    paths += [output / 'game.blend', output / 'validation' / 'negative-nonuniform.fbx']
    return {str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(set(paths)) if path.is_file()}


def write_completion(output, asset_name, report):
    """Write the final completion marker only for a fully hashed generic-PASS delivery."""
    path = output / 'delivery-complete.json'
    if report['generic_blender_bake_validation']['status'] != 'PASS':
        path.unlink(missing_ok=True)
        return None
    files = dict(report['files_sha256'])
    files['validation.json'] = hashlib.sha256((output / 'validation.json').read_bytes()).hexdigest()
    marker = {'schema': 1, 'asset': asset_name, 'status': 'COMPLETE',
              'generic_blender_bake_validation': report['generic_blender_bake_validation'],
              'renders_skipped': report['renders_skipped'], 'files_sha256': files}
    write_json_atomic(path, marker)
    return marker


def export_asset(asset, blend=None, output=None, size=2048, renders=True):
    """Deliver FBX meshes, textures, review sheets and measured validation."""
    output = Path(output or Path('build/assets') / asset.name).resolve()
    output.mkdir(parents=True, exist_ok=True)
    texture_dir = output / 'textures'
    texture_dir.mkdir(exist_ok=True)
    source = Path(blend or asset / f'{asset.name}.blend').resolve()
    if source == output / 'game.blend':
        raise ValueError('The source scene must be separate from the derived game.blend output')
    threads_mode = bpy.context.scene.render.threads_mode
    threads = bpy.context.scene.render.threads
    bpy.ops.wm.open_mainfile(filepath=str(source))
    bpy.context.preferences.filepaths.save_version = 0
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.threads_mode = threads_mode
    scene.render.threads = threads
    collections = [c for c in scene.collection.children if not c.name.endswith('_non_export')]
    if len(collections) != 1:
        raise ValueError('Expected one asset collection and *_non_export staging collections')
    prepare_output(output, asset.name)
    source_states = state_inventory(list(collections[0].all_objects))
    originals = [o for o in collections[0].all_objects if o.type in {'MESH', 'CURVE', 'FONT'} and not o.hide_render]
    markers = [o for o in collections[0].all_objects if o.type == 'EMPTY' and 'Socket' in o.name]
    generated = bpy.data.collections.new('Game_delivery_non_export')
    scene.collection.children.link(generated)
    groups = {}
    for obj in originals:
        root = moving_root(obj)
        key = root.name if root else 'Body'
        groups.setdefault(key, {'sources': [], 'root': root})['sources'].append(obj)
    parts, hulls = [], []
    bake_material = material('Bake target')
    for key, group in groups.items():
        root = group['root']
        pivot = rigid_transform(root.matrix_world) if root else Matrix.Identity(4)
        high = [mesh_copy(o, generated) for o in group['sources']]
        components, details = [], []
        for source_obj, source_high in zip(group['sources'], high):
            socket_hardware = source_obj.type != 'FONT' and any(
                surface_distance([source_high], marker.matrix_world.translation) <= SOCKET_SURFACE_TOLERANCE
                for marker in markers)
            preserved = bool(source_obj.get('ep_lod_preserve', False))
            if not (socket_hardware or preserved) and (source_obj.type == 'FONT' or source_obj.name.startswith('BAKE_') or (
                    max(source_obj.dimensions) < 0.12 and not root)):
                details.append(source_high)
                continue
            low = mesh_copy(source_obj, generated, True)
            low[epuv.IMPORTANCE_PROPERTY] = epuv.uv_importance(source_obj)
            low.data.materials.clear()
            low.data.materials.append(bake_material)
            tree = BVHTree.FromPolygons(
                [low.matrix_world @ vertex.co for vertex in low.data.vertices],
                [polygon.vertices[:] for polygon in low.data.polygons])
            components.append({'low': low, 'high': [source_high], 'tree': tree,
                               'source': source_obj.name, 'lod_preserve': preserved,
                               'lod_assembly': source_obj.get('ep_lod_assembly', 'preserved')})
        if not components:
            raise ValueError(f'No receiving game geometry in part {key}')
        for detail in details:
            minimum, maximum = bounds(detail)
            point = (minimum + maximum) / 2
            receiver = min(components, key=lambda item: item['tree'].find_nearest(point)[3])
            receiver['high'].append(detail)
        if key == 'Body':
            hulls = collision([c['low'] for c in components], generated,
                              f'SM_{identifier(asset.name)}_Body_LOD0')
        name = f'SM_{identifier(asset.name)}_{identifier(key)}'
        parts.append({'name': name, 'key': key, 'components': components,
                      'high': high, 'pivot': pivot})
    for obj in originals:
        obj.hide_render = True
    staging = [c for c in scene.collection.children if c.name.endswith('_non_export') and c != generated]
    for collection in staging:
        for obj in list(collection.all_objects):
            if obj.type in {'MESH', 'CURVE', 'FONT'}:
                obj.hide_render = True
    for obj in hulls:
        obj.hide_render = True
    receivers = [c['low'] for p in parts for c in p['components']]
    unwrap(receivers, size)
    atlas = uv_metrics(receivers, size)
    atlas_signature = uv_layout_signature(receivers)
    if atlas['zero_area_uv_triangles'] or atlas['outside_0_1_loop_count'] or atlas['geometric_overlap']['intersecting_triangle_pairs']:
        raise RuntimeError(f'Invalid UV atlas at {size} px: {json.dumps(atlas)}')
    uv_priority_metrics = {}
    for importance in sorted({epuv.uv_importance(obj) for obj in receivers}):
        group = [obj for obj in receivers if epuv.uv_importance(obj) == importance]
        uv_priority_metrics[str(importance)] = {
            'receiver_count': len(group), 'receivers': [obj.name for obj in group],
            'uv0': uv_metrics(group, size)}
    textures = bake(parts, size, texture_dir)
    preview = preview_material(textures, asset.name)
    socket_points = {marker.name: marker.matrix_world.translation.copy() for marker in markers}
    for part in parts:
        for component in part['components']:
            component['socket_bearing'] = part['key'] == 'Body' and any(
                surface_distance([component['low']], point) <= SOCKET_SURFACE_TOLERANCE
                for point in socket_points.values())
        candidates = []
        for level, ratio in enumerate(RATIOS):
            meshes, dropped, kept_whole, assembly_checks = [], [], [], {}
            for component in part['components']:
                source_low = component['low']
                bearing = component['socket_bearing']
                if level and part['key'] == 'Body' and not (bearing or component['lod_preserve']) and max(source_low.dimensions) < OMIT_BELOW[level]:
                    dropped.append(component['source'])
                    continue
                obj = source_low.copy()
                obj.data = source_low.data.copy()
                generated.objects.link(obj)
                protected = bearing or component['lod_preserve']
                if protected and level < len(RATIOS) - 1:
                    kept_whole.append(component['source'])
                elif level:
                    reduce_mesh(obj, ratio, PROTECTED_ERROR_LIMIT if protected else LOD_ERROR_LIMITS[level])
                if component['lod_preserve']:
                    check = assembly_checks.setdefault(component['lod_assembly'], {
                        'components': 0, 'present': 0, 'max_bounds_deviation_m': 0.0})
                    check['components'] += 1
                    if obj.data.polygons:
                        check['present'] += 1
                        deviation = max(abs(a - b) for expected, actual in zip(bounds(source_low), bounds(obj))
                                        for a, b in zip(expected, actual))
                        check['max_bounds_deviation_m'] = max(check['max_bounds_deviation_m'], deviation)
                meshes.append(obj)
            if not meshes:
                raise ValueError(f'LOD{level} removes every component of {part["key"]}')
            obj = join(meshes, f'{part["name"]}_candidate{level}', part['pivot'])
            obj.data.materials.clear()
            obj.data.materials.append(preview)
            obj.hide_render = True
            candidates.append((level, obj, {'omitted_fixed_components': dropped,
                'socket_bearing_components_unreduced': kept_whole,
                'preserved_assembly_checks': assembly_checks,
                'error_limit_m': LOD_ERROR_LIMITS[level], 'target_ratio': ratio}))
        part['lods'], part['lod_details'], part['dropped_lods'] = [], [], []
        for level, obj, details in candidates:
            triangles = topology(obj)['triangles']
            if part['lods'] and triangles > MAX_LOD_FRACTION * topology(part['lods'][-1])['triangles']:
                part['dropped_lods'].append({'candidate_level': level, 'triangles': triangles, **details})
                bpy.data.objects.remove(obj, do_unlink=True)
                continue
            obj.name = f'{part["name"]}_LOD{len(part["lods"])}'
            obj.hide_render = bool(part['lods'])
            part['lods'].append(obj)
            part['lod_details'].append({'candidate_level': level, **details})
        part['low'] = part['lods'][0]
        for component in part['components']:
            bpy.data.objects.remove(component['low'], do_unlink=True)
    levels = max(len(p['lods']) for p in parts)
    uv_lods = [uv_metrics([p['lods'][min(i, len(p['lods']) - 1)] for p in parts], size) for i in range(levels)]
    socket_surface = {}
    body = next(p for p in parts if p['key'] == 'Body')
    for logical, point in socket_points.items():
        socket_surface[logical] = [surface_distance([obj], point) for obj in body['lods']]
    pivot_surface = {part['key']: [surface_distance([obj], part['pivot'].translation) for obj in part['lods']]
                     for part in parts if part['key'] != 'Body'}
    report = {'source': str(source), 'blender_version': bpy.app.version_string,
              'texture_size': size, 'normal_convention': 'DirectX Y-', 'lod_ratios': RATIOS,
              'uv0': uv_lods[0], 'uv_per_lod': uv_lods,
              'collision_hull_count': len(hulls), 'sockets_cm': {}, 'parts': {},
              'socket_export_names': {},
              'unreal_import_verified': False,
              'delivery_status': 'Blender candidate; requires visual review and Unreal checks',
              'uv_exclusions': [],
              'material_contract_source': 'https://docs.ficsit.app/satisfactory-modding/latest/Development/Modeling/MainMaterials.html#_factory_baked_mm_factorybaked',
              'hidden_source_objects': [o.name for o in collections[0].all_objects if o.hide_render and o not in originals],
              'paint_mask_contract': 'AOMasks RGB = AO, primary paint, secondary paint',
              'reflection_map_contract': 'ReflectionMap RGB = metallic, roughness, emission mask'}
    report['uv_priority_groups'] = uv_priority_metrics
    report['uv_layout_sha256'] = atlas_signature
    report['uv_packing'] = {'method': 'SmartProject charts, global area normalization, authored linear importance, CONCAVE packing',
                            'per_island_padding_px': UV_PADDING_PIXELS,
                            'bake_dilation_px': BAKE_DILATION_PIXELS}
    report['render_threads'] = scene.render.threads
    report['lod_rules'] = {'omit_below_m': OMIT_BELOW, 'error_limits_m': LOD_ERROR_LIMITS,
                           'max_fraction_of_previous': MAX_LOD_FRACTION,
                           'protected_error_limit_m': PROTECTED_ERROR_LIMIT,
                           'protected_bounds_tolerance_m': PROTECTED_BOUNDS_TOLERANCE}
    report['socket_surface_distance_m'] = {'tolerance': SOCKET_SURFACE_TOLERANCE, 'per_lod': socket_surface}
    report['pivot_surface_distance_m'] = pivot_surface
    report['paint_mask_polarity'] = 'Project convention: 1 selected, 0 fixed; numeric current shader polarity and remap remain unverified'
    report['state_delivery'] = source_states
    report['texture_color_spaces'] = {name: img.colorspace_settings.name for name, img in textures.items()}
    report['normal_bake_swizzle'] = {'space': 'TANGENT', 'R': 'POS_X', 'G': 'NEG_Y', 'B': 'POS_Z',
                                    'unreal_flip_green_channel': False}
    report['collision_hulls'] = {obj.name: convexity(obj) for obj in hulls}
    report['source_transforms'] = {obj.name: {
        'scale': list(obj.matrix_world.to_scale()),
        'determinant': obj.matrix_world.to_3x3().determinant(),
        'nonuniform': max(obj.matrix_world.to_scale()) - min(obj.matrix_world.to_scale()) > 1e-6
        } for obj in originals}
    all_points = []
    for part in parts:
        low, high = bounds(part['low'])
        all_points.extend([low, high])
        report['parts'][part['key']] = {'lods': [
            {**topology(obj), **details} for obj, details in zip(part['lods'], part['lod_details'])],
            'pivot_cm': [v * 100 for v in part['pivot'].translation],
            'pivot_matrix_m': [list(row) for row in part['pivot']],
            'dropped_lods': part['dropped_lods']}
        lod_group = bpy.data.objects.new(part['name'], None)
        generated.objects.link(lod_group)
        lod_group['fbx_type'] = 'LodGroup'
        for obj in part['lods']:
            obj.matrix_world = Matrix.Identity(4)
            obj.parent = lod_group
        extras = []
        if part['key'] == 'Body':
            for index, marker in enumerate(markers):
                socket = bpy.data.objects.new(f'SOCKET_{part["name"]}_LOD0_{index:02}', None)
                generated.objects.link(socket)
                socket.matrix_world = rigid_transform(marker.matrix_world)
                extras.append(socket)
                report['sockets_cm'][marker.name] = [v * 100 for v in socket.location]
                report['socket_export_names'][marker.name] = socket.name
            for moving in parts:
                if moving['key'] != 'Body':
                    socket = bpy.data.objects.new(
                        f'SOCKET_{part["name"]}_LOD0_{len(extras):02}', None)
                    generated.objects.link(socket)
                    socket.matrix_world = moving['pivot']
                    extras.append(socket)
                    report['socket_export_names']['Pivot_' + moving['key']] = socket.name
            extras += hulls
        export_fbx(output / f'{part["name"]}.fbx', [lod_group] + part['lods'] + extras)
        report['parts'][part['key']]['fbx_round_trip'] = reimport_check(
            output / f'{part["name"]}.fbx', part['lods'], extras)
        for obj in extras:
            obj.hide_render = True
    report['bounds_cm'] = {'min': [min(p[i] for p in all_points) * 100 for i in range(3)],
                           'max': [max(p[i] for p in all_points) * 100 for i in range(3)]}
    report['negative_nonuniform_scale_fixture'] = transform_fixture(generated, preview, output)
    if renders:
        render_checks(parts, originals, staging, output)
    for part in parts:
        for index, obj in enumerate(part['lods']):
            obj.matrix_world = part['pivot']
            obj.hide_render = index != 0
    for img in textures.values():
        img.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(output / 'game.blend'))
    report['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    report['material_profile'] = material_profile()
    failures = [name for name, values in socket_surface.items() if max(values) > SOCKET_SURFACE_TOLERANCE]
    failures += [f'uv_lod{index}' for index, metrics in enumerate(uv_lods)
                 if metrics['zero_area_uv_triangles'] or metrics['outside_0_1_loop_count']
                 or metrics['geometric_overlap']['intersecting_triangle_pairs']]
    if not report['negative_nonuniform_scale_fixture']['passed']:
        failures.append('negative_nonuniform_scale_fixture')
    failures += [f'fbx_round_trip_{key}' for key, part in report['parts'].items() if not part['fbx_round_trip']['passed']]
    failures += [f'preserved_assembly_{key}_{level}_{name}' for key, part in report['parts'].items()
                 for level, lod in enumerate(part['lods'])
                 for name, check in lod['preserved_assembly_checks'].items()
                 if check['present'] < check['components'] or check['max_bounds_deviation_m'] > PROTECTED_BOUNDS_TOLERANCE]
    report['generic_blender_bake_validation'] = {'status': 'FAIL' if failures else 'PASS',
                                               'failures': failures, 'scope': 'Blender generic PBR/UV/LOD/socket/collision/FBX round-trip only'}
    report['schema'] = 2
    report['renders_skipped'] = not renders
    report['stage_statuses'] = {
        'geometry': 'FAIL' if not report['negative_nonuniform_scale_fixture']['passed'] else 'PASS',
        'uv': 'FAIL' if any(name.startswith('uv_lod') for name in failures) else 'PASS',
        'lod': 'FAIL' if any(name.startswith('preserved_assembly') for name in failures) else 'PASS',
        'collision': 'PASS' if all(item['convex_closed_positive_volume'] for item in report['collision_hulls'].values()) else 'FAIL',
        'socket': 'FAIL' if any(name in socket_surface for name in failures) else 'PASS',
        'fbx_round_trip': 'FAIL' if any(name.startswith('fbx_round_trip') for name in failures) else 'PASS',
        'texture_bake': 'PASS', 'review_images': 'NOT_RUN' if not renders else 'RENDERED'}
    report['files_sha256'] = delivered_file_hashes(output, asset.name)
    write_assembly(asset.name, output, report)
    report['files_sha256']['assembly.json'] = hashlib.sha256((output / 'assembly.json').read_bytes()).hexdigest()
    write_json_atomic(output / 'validation.json', report)
    write_completion(output, asset.name, report)
    if failures:
        raise RuntimeError(f'Validation failed: {failures}; see validation.json')
    print('GAME_EXPORT ' + json.dumps(report), flush=True)
