"""Verify an exported asset package, then import it in a blank Unreal project and report engine readbacks.

Host Python runs only the package verification. The Unreal Python commandlet verifies the same package again,
imports it, and verifies it once more after import.
"""

import hashlib
import importlib.util
import json
import math
import os
import sys
from pathlib import Path

COMPLETION_NAME = "delivery-complete.json"
COMPLETION_SCHEMA = 1
ASSEMBLY_SCHEMA = 2
SRGB = "sRGB"
LINEAR = "Non-Color"
REQUIRED_COLOR_SPACES = {"BaseColor": SRGB, "Normal": LINEAR, "AOMasks": LINEAR, "ReflectionMap": LINEAR}
FINAL_SCOPE = "FINAL_PACKAGE"
EARLY_SCOPE = "EARLY_NONFINAL_DIAGNOSTIC"
HASH_CHUNK_BYTES = 1 << 20


class DeliveryError(Exception):
    """A package or diagnostic input that must not be imported."""


def require(condition, message):
    if not condition:
        raise DeliveryError(message)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(HASH_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path):
    require(path.is_file(), f"Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise DeliveryError(f"Malformed JSON in {path}: {error}") from error


def listed_path(directory, relative):
    """Returns the absolute path of a package-relative entry.

    The entry must stay inside the package directory.
    """
    require(isinstance(relative, str) and relative and not Path(relative).is_absolute(),
            f"Invalid package path {relative!r}")
    path = (directory / relative).resolve()
    require(path.is_relative_to(directory), f"Package path {relative!r} leaves {directory}")
    return path


def require_matrix(name, matrix):
    require(isinstance(matrix, list) and len(matrix) == 4
            and all(isinstance(row, list) and len(row) == 4
                    and all(isinstance(value, (int, float)) for value in row) for row in matrix),
            f"{name}: relative_transform_cm is not a 4x4 numeric matrix")
    require(matrix[3] == [0, 0, 0, 1], f"{name}: relative_transform_cm last row is not [0, 0, 0, 1]")


def verify_delivery(directory):
    """Returns the verified contents of a completed final package.

    Raises DeliveryError unless the completion record, every listed hash, the validation and assembly
    contracts, and the absence of unlisted meshes and textures all hold.
    """
    directory = Path(directory).resolve()
    require(directory.is_dir(), f"Package directory {directory} does not exist")
    completion = load_json(directory / COMPLETION_NAME)
    require(completion.get("schema") == COMPLETION_SCHEMA,
            f"{COMPLETION_NAME} schema is {completion.get('schema')!r}, not {COMPLETION_SCHEMA}")
    require(completion.get("status") == "COMPLETE", f"{COMPLETION_NAME} status is {completion.get('status')!r}")
    generic = completion.get("generic_blender_bake_validation")
    require(isinstance(generic, dict) and generic.get("status") == "PASS",
            f"Generic Blender validation is not PASS: {generic!r}")
    require(isinstance(completion.get("renders_skipped"), bool), f"{COMPLETION_NAME} renders_skipped is not a boolean")
    hashes = completion.get("files_sha256")
    require(isinstance(hashes, dict) and hashes, f"{COMPLETION_NAME} files_sha256 is empty or missing")
    for relative, expected in hashes.items():
        path = listed_path(directory, relative)
        require(path.is_file(), f"Listed file {relative} is missing")
        actual = sha256_file(path)
        require(actual == expected, f"Listed file {relative} has sha256 {actual}, expected {expected}")

    require(COMPLETION_NAME not in hashes, f"{COMPLETION_NAME} lists itself")
    for name in ("validation.json", "assembly.json"):
        require(name in hashes, f"{name} is not listed in {COMPLETION_NAME}")
    validation = load_json(directory / "validation.json")
    assembly = load_json(directory / "assembly.json")
    require(validation.get("generic_blender_bake_validation") == generic,
            "validation.json generic_blender_bake_validation differs from the completion record")
    require(assembly.get("generic_blender_bake_validation") == generic,
            "assembly.json generic_blender_bake_validation differs from the completion record")
    require(assembly.get("schema") == ASSEMBLY_SCHEMA, f"assembly.json schema is {assembly.get('schema')!r}")
    require(assembly.get("validation_manifest") == "validation.json",
            f"assembly.json validation_manifest is {assembly.get('validation_manifest')!r}")
    validation_hashes = validation.get("files_sha256")
    products = assembly.get("product_files_sha256")
    require(isinstance(validation_hashes, dict) and isinstance(products, dict) and products,
            "validation.json files_sha256 or assembly.json product_files_sha256 is missing")
    require(validation_hashes == {**products, "assembly.json": hashes["assembly.json"]},
            "validation.json files_sha256 is not assembly.json product_files_sha256 plus the assembly.json hash")
    stale = sorted(relative for relative, value in validation_hashes.items() if hashes.get(relative) != value)
    require(not stale, f"validation.json hashes differ from {COMPLETION_NAME}: {stale}")

    meshes = assembly.get("static_meshes")
    require(isinstance(meshes, dict) and meshes, "assembly.json static_meshes is empty or missing")
    require(assembly.get("body_file") in hashes, f"Body file {assembly.get('body_file')!r} is not listed")
    roots = [name for name, specification in meshes.items() if specification.get("parent") is None]
    require(len(roots) == 1, f"assembly.json needs exactly one root mesh, found {roots}")
    mesh_files = []
    for name, specification in meshes.items():
        relative = specification.get("file")
        require(isinstance(relative, str) and relative.endswith(".fbx"), f"{name}: file {relative!r} is not an FBX")
        require(relative in hashes, f"{name}: {relative} is not listed in {COMPLETION_NAME}")
        require(validation_hashes.get(relative) == hashes[relative],
                f"{name}: {relative} hash differs between validation.json and {COMPLETION_NAME}")
        parent = specification.get("parent")
        require(parent is None or parent in meshes, f"{name}: unknown parent {parent!r}")
        require_matrix(name, specification.get("relative_transform_cm"))
        mesh_files.append(relative)
    require(len(set(mesh_files)) == len(mesh_files), "assembly.json lists one FBX for several meshes")

    color_spaces = validation.get("texture_color_spaces")
    require(isinstance(color_spaces, dict) and color_spaces, "validation.json texture_color_spaces is missing")
    for name, space in REQUIRED_COLOR_SPACES.items():
        require(color_spaces.get(name) == space,
                f"Texture {name} color space is {color_spaces.get(name)!r}, expected {space!r}")
    textures = {}
    for name, space in color_spaces.items():
        require(space in (SRGB, LINEAR), f"Texture {name} has unknown color space {space!r}")
        relative = f"textures/{name}.png"
        require(relative in hashes, f"{relative} is not listed in {COMPLETION_NAME}")
        require(validation_hashes.get(relative) == hashes[relative],
                f"{relative} hash differs between validation.json and {COMPLETION_NAME}")
        textures[name] = relative

    present = list(directory.glob("SM_*.fbx")) + list((directory / "textures").glob("*.png"))
    orphans = sorted(str(path.relative_to(directory)) for path in present
                     if str(path.relative_to(directory)) not in hashes)
    require(not orphans, f"Unlisted package files: {orphans}")

    return {
        "scope": FINAL_SCOPE,
        "directory": directory,
        "completion_sha256": sha256_file(directory / COMPLETION_NAME),
        "generic_blender_bake_validation": generic,
        "renders_skipped": completion["renders_skipped"],
        "files_sha256": dict(hashes),
        "validation": validation,
        "assembly": assembly,
        "mesh_files": mesh_files,
        "textures": textures,
    }


def verify_early(paths, hashes):
    """Returns the verified raw FBX inputs of an early, nonfinal diagnostic run."""
    require(paths and len(paths) == len(hashes),
            "EP_UNREAL_EARLY_FBX and EP_UNREAL_EARLY_SHA256 need the same nonzero number of entries")
    files = {}
    for path, expected in zip(paths, hashes):
        path = Path(path).resolve()
        require(path.is_file() and path.suffix == ".fbx", f"Early input {path} is not an FBX file")
        actual = sha256_file(path)
        require(actual == expected, f"Early input {path} has sha256 {actual}, expected {expected}")
        files[str(path)] = actual
    return {"scope": EARLY_SCOPE, "files_sha256": files, "mesh_files": list(files)}


def plan_from_environment():
    """Returns the verified import plan selected by the environment.

    EP_UNREAL_DELIVERY selects a final package directory. EP_UNREAL_EARLY_FBX and EP_UNREAL_EARLY_SHA256
    select raw FBX files for a nonfinal diagnostic; both are os.pathsep-separated and paired by position.
    """
    delivery = os.environ.get("EP_UNREAL_DELIVERY") or None
    early = os.environ.get("EP_UNREAL_EARLY_FBX") or None
    require((delivery is None) != (early is None), "Set exactly one of EP_UNREAL_DELIVERY and EP_UNREAL_EARLY_FBX")
    if delivery:
        return verify_delivery(delivery)
    split = lambda name: [value for value in os.environ.get(name, "").split(os.pathsep) if value]
    return verify_early(split("EP_UNREAL_EARLY_FBX"), split("EP_UNREAL_EARLY_SHA256"))


def mesh_source(plan, relative):
    return plan["directory"] / relative if plan["scope"] == FINAL_SCOPE else Path(relative)


def vector(value):
    return [value.x, value.y, value.z]


def box(minimum, maximum):
    return {"min_cm": vector(minimum), "max_cm": vector(maximum)}


def points_box(points):
    return {
        "min_cm": [min(point[axis] for point in points) for axis in range(3)],
        "max_cm": [max(point[axis] for point in points) for axis in range(3)],
    }


def lod_source_bounds(mesh, lod_index):
    """Returns signed bounds of the stored source mesh description for one LOD."""
    description = mesh.get_static_mesh_description(lod_index)
    points = []
    for value in range(description.get_vertex_count()):
        vertex = unreal.VertexID(value)
        if description.is_vertex_valid(vertex):
            points.append(vector(description.get_vertex_position(vertex)))
    return {"vertices": len(points), **points_box(points)}


def inspect_mesh(mesh):
    bounds = mesh.get_bounds()
    bounding_box = mesh.get_bounding_box()
    materials = mesh.get_editor_property("static_materials")
    geometry = mesh.get_editor_property("body_setup").get_editor_property("agg_geom")
    lod_count = mesh.get_num_lods()
    sockets = []
    for socket in mesh.get_sockets_by_tag(""):
        rotation = socket.get_editor_property("relative_rotation")
        sockets.append({
            "name": str(socket.get_editor_property("socket_name")),
            "location_cm": vector(socket.get_editor_property("relative_location")),
            "rotation_degrees_pitch_yaw_roll": [rotation.pitch, rotation.yaw, rotation.roll],
            "axes_forward_right_up": [
                vector(rotation.get_forward_vector()),
                vector(rotation.get_right_vector()),
                vector(rotation.get_up_vector()),
            ],
            "scale": vector(socket.get_editor_property("relative_scale")),
        })
    return {
        "asset": mesh.get_path_name(),
        "bounds_origin_cm": vector(bounds.origin),
        "bounds_extent_cm": vector(bounds.box_extent),
        "bounds_size_cm": [2 * value for value in vector(bounds.box_extent)],
        "bounding_box": box(bounding_box.min, bounding_box.max),
        "material_slots": [str(slot.get_editor_property("material_slot_name")) for slot in materials],
        "lod_count": lod_count,
        "lod_geometry": [
            {
                "index": index,
                "triangles": mesh.get_num_triangles(index),
                "vertices": mesh.get_num_vertices(index),
                "sections": mesh.get_num_sections(index),
                "source_bounds": lod_source_bounds(mesh, index),
            }
            for index in range(lod_count)
        ],
        "simple_primitive_collision_count": sum(
            len(geometry.get_editor_property(name)) for name in ("box_elems", "sphere_elems", "sphyl_elems")
        ),
        "convex_collision_count": len(geometry.get_editor_property("convex_elems")),
        "sockets": sockets,
    }


def import_mesh(source):
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    options.set_editor_property("automated_import_should_detect_type", False)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("auto_compute_lod_distances", False)
    for index, screen_size in enumerate((1.0, 0.5, 0.25, 0.125)):
        options.set_editor_property(f"lod_distance{index}", screen_size)
    mesh_options = options.get_editor_property("static_mesh_import_data")
    mesh_options.set_editor_property("combine_meshes", False)
    mesh_options.set_editor_property("import_mesh_lods", True)
    mesh_options.set_editor_property("auto_generate_collision", False)
    mesh_options.set_editor_property("one_convex_hull_per_ucx", True)
    mesh_options.set_editor_property("import_uniform_scale", 1.0)
    mesh_options.set_editor_property("convert_scene", True)
    mesh_options.set_editor_property("convert_scene_unit", True)
    mesh_options.set_editor_property("force_front_x_axis", False)
    mesh_options.set_editor_property("transform_vertex_to_absolute", False)
    mesh_options.set_editor_property("bake_pivot_in_vertex", False)
    mesh_options.set_editor_property("normal_import_method", unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
    mesh_options.set_editor_property("normal_generation_method", unreal.FBXNormalGenerationMethod.MIKK_T_SPACE)
    mesh_options.set_editor_property("generate_lightmap_u_vs", False)
    mesh_options.set_editor_property("build_nanite", False)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(source))
    task.set_editor_property("destination_path", "/Game/Smoke")
    task.set_editor_property("destination_name", source.stem)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("factory", unreal.FbxFactory())
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    meshes = [asset for asset in task.get_objects() if isinstance(asset, unreal.StaticMesh)]
    if len(meshes) != 1:
        raise RuntimeError(f"Expected one StaticMesh from {source}, got {len(meshes)}")
    return meshes[0]


def import_textures(plan):
    results = []
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    color_spaces = plan["validation"]["texture_color_spaces"]
    for name, relative in plan["textures"].items():
        source = plan["directory"] / relative
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", str(source))
        task.set_editor_property("destination_path", "/Game/Smoke/Textures")
        task.set_editor_property("destination_name", name)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", False)
        task.set_editor_property("factory", unreal.TextureFactory())
        tools.import_asset_tasks([task])
        textures = [item for item in task.get_objects() if isinstance(item, unreal.Texture2D)]
        if len(textures) != 1:
            raise RuntimeError(f"Expected one Texture2D from {source}, got {len(textures)}")
        texture = textures[0]
        texture.set_editor_property("srgb", color_spaces[name] == SRGB)
        texture.set_editor_property("flip_green_channel", False)
        if name == "Normal":
            texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        elif name in ("AOMasks", "ReflectionMap"):
            texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
        else:
            texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
        if not unreal.EditorAssetLibrary.save_loaded_asset(texture):
            raise RuntimeError(f"Could not save texture {texture.get_path_name()}")
        results.append({
            "source": relative,
            "sha256": plan["files_sha256"][relative],
            "asset": texture.get_path_name(),
            "validation_color_space": color_spaces[name],
            "srgb": texture.get_editor_property("srgb"),
            "flip_green_channel": texture.get_editor_property("flip_green_channel"),
            "compression_settings": str(texture.get_editor_property("compression_settings")),
        })
    return results


def matrix_rotation(matrix):
    """Converts a rigid 3x3 rotation to an Unreal rotator without changing basis."""
    trace = sum(matrix[index][index] for index in range(3))
    if trace > 0:
        scale = math.sqrt(trace + 1.0) * 2
        values = [
            (matrix[2][1] - matrix[1][2]) / scale,
            (matrix[0][2] - matrix[2][0]) / scale,
            (matrix[1][0] - matrix[0][1]) / scale,
            scale / 4,
        ]
    else:
        index = max(range(3), key=lambda value: matrix[value][value])
        following, last = (index + 1) % 3, (index + 2) % 3
        scale = math.sqrt(1 + matrix[index][index] - matrix[following][following] - matrix[last][last]) * 2
        values = [0.0] * 4
        values[index] = scale / 4
        values[following] = (matrix[index][following] + matrix[following][index]) / scale
        values[last] = (matrix[index][last] + matrix[last][index]) / scale
        values[3] = (matrix[last][following] - matrix[following][last]) / scale
    return unreal.Quat(*values).rotator()


def assemble_meshes(assembly, meshes):
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    level_path = "/Game/Smoke/AssemblySmoke"
    if not levels.new_level(level_path):
        raise RuntimeError(f"Could not create {level_path}")
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    gameplay = unreal.get_default_object(unreal.GameplayStatics)
    spawned = {}
    results = []
    pending = dict(assembly["static_meshes"])
    while pending:
        ready = [name for name, specification in pending.items()
                 if specification["parent"] is None or specification["parent"] in spawned]
        if not ready:
            raise RuntimeError(f"assembly.json parent cycle among {sorted(pending)}")
        for name in ready:
            specification = pending.pop(name)
            matrix = specification["relative_transform_cm"]
            rotation = matrix_rotation(matrix)
            location = unreal.Vector(*(matrix[index][3] for index in range(3)))
            mesh = meshes[specification["file"]]
            transform = unreal.Transform(location=location, rotation=rotation, scale=unreal.Vector(1, 1, 1))
            actor = gameplay.call_method(
                "BeginDeferredActorSpawnFromClass",
                args=(world, unreal.StaticMeshActor.static_class(), transform,
                      unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN, None,
                      unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT),
            )
            if actor is None:
                raise RuntimeError(f"Could not begin spawning {name}")
            component = actor.get_editor_property("static_mesh_component")
            if not component.set_static_mesh(mesh):
                raise RuntimeError(f"Could not assign mesh to {name}")
            actor = gameplay.call_method(
                "FinishSpawningActor",
                args=(actor, transform, unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT),
            )
            if actor is None:
                raise RuntimeError(f"Could not finish spawning {name}")
            actor.set_actor_label(name)
            parent = specification["parent"]
            if parent is not None and not actor.attach_to_actor(
                spawned[parent], "",
                unreal.AttachmentRule.KEEP_RELATIVE,
                unreal.AttachmentRule.KEEP_RELATIVE,
                unreal.AttachmentRule.KEEP_RELATIVE, False,
            ):
                raise RuntimeError(f"Could not attach {name} to {parent}")
            relative_rotation = component.get_editor_property("relative_rotation")
            sockets_world = []
            for socket in mesh.get_sockets_by_tag(""):
                socket_name = socket.get_editor_property("socket_name")
                socket_rotation = component.get_socket_rotation(socket_name)
                sockets_world.append({
                    "name": str(socket_name),
                    "location_cm": vector(component.get_socket_location(socket_name)),
                    "rotation_degrees_pitch_yaw_roll": [socket_rotation.pitch, socket_rotation.yaw, socket_rotation.roll],
                })
            attached_parent = actor.get_attach_parent_actor()
            results.append({
                "name": name,
                "parent": attached_parent.get_actor_label() if attached_parent else None,
                "actor": actor.get_path_name(),
                "mesh": component.get_editor_property("static_mesh").get_path_name(),
                "expected_relative_matrix_cm": matrix,
                "relative_location_cm": vector(component.get_editor_property("relative_location")),
                "relative_rotation_degrees_pitch_yaw_roll": [
                    relative_rotation.pitch, relative_rotation.yaw, relative_rotation.roll,
                ],
                "relative_scale": vector(component.get_editor_property("relative_scale3d")),
                "world_pivot_cm": vector(actor.get_actor_location()),
                "world_axes_forward_right_up": [
                    vector(actor.get_actor_forward_vector()),
                    vector(actor.get_actor_right_vector()),
                    vector(actor.get_actor_up_vector()),
                ],
                "sockets_world": sockets_world,
            })
            spawned[name] = actor
    if not levels.save_current_level():
        raise RuntimeError(f"Could not save {level_path}")
    return {"level": level_path, "parts": results}


def unreal_main():
    global unreal
    import unreal

    report_path = Path(os.environ["EP_UNREAL_REPORT"]).resolve()
    plan = plan_from_environment()
    report = {
        "scope": plan["scope"],
        "engine_version": unreal.SystemLibrary.get_engine_version(),
        "project_file": unreal.Paths.get_project_file_path(),
        "importer": "legacy FbxFactory with FbxImportUI",
        "verified_files_sha256": plan["files_sha256"],
        "imports": [],
    }
    if plan["scope"] == FINAL_SCOPE:
        report.update({
            "package": str(plan["directory"]),
            "completion_sha256": plan["completion_sha256"],
            "generic_blender_bake_validation": plan["generic_blender_bake_validation"],
            "renders_skipped": plan["renders_skipped"],
        })
    imported = {}
    for relative in plan["mesh_files"]:
        mesh = import_mesh(mesh_source(plan, relative))
        imported[relative] = mesh
        report["imports"].append({"source": relative, "sha256": plan["files_sha256"][relative],
                                  "mesh": inspect_mesh(mesh)})
    if plan["scope"] == FINAL_SCOPE:
        report["textures"] = import_textures(plan)
        report["assembly"] = assemble_meshes(plan["assembly"], imported)
    after = plan_from_environment()
    if after["files_sha256"] != plan["files_sha256"]:
        raise DeliveryError("Package files changed during import")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print("EP_UNREAL_IMPORT_REPORT " + json.dumps(report))


def preflight():
    """Verifies the selected inputs on the host and returns a process exit status."""
    try:
        plan = plan_from_environment()
    except DeliveryError as error:
        print(f"EP_UNREAL_DELIVERY_REFUSED {error}", file=sys.stderr)
        return 2
    summary = {key: plan[key] for key in ("scope", "files_sha256")}
    if plan["scope"] == FINAL_SCOPE:
        summary["renders_skipped"] = plan["renders_skipped"]
    print("EP_UNREAL_DELIVERY_VERIFIED " + json.dumps(summary))
    return 0


if "unreal" in sys.modules or importlib.util.find_spec("unreal") is not None:
    unreal_main()
else:
    sys.exit(preflight())
