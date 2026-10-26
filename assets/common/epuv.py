"""Global packing of existing game-delivery UV islands."""
import math

import bpy
import numpy as np

UNIT_SCALE_TOLERANCE = 1e-5
IMPORTANCE_PROPERTY = 'ep_uv_importance'


def uv_importance(obj):
    """Return the positive linear texel-density factor authored on an object, default 1."""
    value = obj.get(IMPORTANCE_PROPERTY, 1.0)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f'{obj.name} {IMPORTANCE_PROPERTY} must be a positive finite number')
    return float(value)


def pack_mesh_objects(objects, resolution, padding_pixels):
    """Pack existing UV islands at a common world-space area-based texel density.

    Objects must have unique mesh data, an active UV layer and rigid unit-scale transforms.
    Only UV coordinates change. Padding is Blender's per-island margin in atlas pixels.
    An object's `ep_uv_importance` multiplies its linear texel density relative to objects at 1.
    """
    objects = list(objects)
    if not objects or resolution <= 0 or not 0 <= padding_pixels < resolution:
        raise ValueError('Expected meshes, a positive resolution and padding below the resolution')
    if bpy.context.mode != 'OBJECT':
        raise ValueError('UV packing requires object mode')
    for obj in objects:
        if obj.type != 'MESH' or not obj.data.uv_layers.active:
            raise ValueError(f'{obj.name} requires a mesh with an active UV layer')
        if obj.data.users != 1:
            raise ValueError(f'{obj.name} requires unique mesh data')
        if any(abs(axis - 1) > UNIT_SCALE_TOLERANCE for axis in obj.matrix_world.to_scale()):
            raise ValueError(f'{obj.name} requires a rigid unit-scale transform')
    importance = {obj.name: uv_importance(obj) for obj in objects}
    selected = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    mesh_selection = [(obj.data, [(elements, [element.select for element in elements])
                                  for elements in (obj.data.vertices, obj.data.edges, obj.data.polygons)])
                      for obj in objects]
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    try:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.average_islands_scale(scale_uv=False, shear=False)
        if any(value != 1 for value in importance.values()):
            bpy.ops.object.mode_set(mode='OBJECT')
            for obj in objects:
                if importance[obj.name] != 1:
                    _scale_uvs(obj.data, importance[obj.name])
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', rotate=True, rotate_method='ANY',
                                scale=True, merge_overlap=False, margin_method='FRACTION',
                                margin=padding_pixels / resolution, pin=False,
                                shape_method='CONCAVE')
    finally:
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        for mesh, groups in mesh_selection:
            for elements, values in groups:
                for element, value in zip(elements, values):
                    element.select = value
        for obj in selected:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = active


def _scale_uvs(mesh, factor):
    """Scale every active-layer UV coordinate about the origin."""
    layer = mesh.uv_layers.active.data
    uv = np.empty(len(layer) * 2)
    layer.foreach_get('uv', uv)
    layer.foreach_set('uv', uv * factor)
