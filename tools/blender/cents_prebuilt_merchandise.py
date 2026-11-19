"""Import curated, prebuilt convenience-store product GLBs and replace package branding.

Models are downloaded separately into assets/merchandise/models after source/licence review.
The manifest controls placement and fictional CENTS SKU labels. Original scanned textures
are deliberately not retained: the source logos/brand artwork are stripped on import.
"""
import json
import os
import bpy
from mathutils import Vector


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_MANIFEST = os.path.join(ROOT, "assets", "merchandise", "manifest.json")


def _bounds(objects):
    points = []
    for obj in objects:
        if obj.type != "MESH":
            continue
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not points:
        raise RuntimeError("Imported merchandise model has no mesh bounds")
    return (
        Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points))),
        Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points))),
    )


def _fictional_material(name, color, metallic=0.0):
    material = bpy.data.materials.new("CENTS fictional package - " + name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = 0.42
    shader.inputs["Metallic"].default_value = metallic
    return material


def _label_material(name, primary, accent):
    material = bpy.data.materials.new("CENTS fictional label - " + name)
    material.diffuse_color = (*primary, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*primary, 1.0)
    shader.inputs["Roughness"].default_value = 0.55
    return material


def _add_fictional_label(name, display_name, center, width, height, material, accent_material, yaw=0.0):
    # A small front-facing label replaces the original scanned brand panel.
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=center)
    label = bpy.context.object
    label.name = "CENTS fictional label - " + name
    label.rotation_euler = (1.57079632679, 0.0, yaw)  # faces the correct aisle
    label.dimensions = (width, height, 0.002)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    label.data.materials.append(material)
    # A narrow top stripe and raised fictional SKU name replace the source logo.
    front_sign = 1.0 if abs(yaw) > 1.5707963 else -1.0
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(center[0], center[1] + front_sign * 0.002, center[2] + height * 0.36))
    stripe = bpy.context.object
    stripe.name = "CENTS label accent stripe - " + name
    stripe.dimensions = (width * 0.92, 0.008, max(0.004, height * 0.07))
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    stripe.data.materials.append(accent_material)
    bpy.ops.object.text_add(location=(center[0], center[1] + front_sign * 0.006, center[2]), rotation=(1.57079632679, 0.0, yaw))
    lettering = bpy.context.object
    lettering.name = "CENTS fictional product name - " + name
    lettering.data.body = display_name.upper()
    lettering.data.align_x = "CENTER"
    lettering.data.align_y = "CENTER"
    lettering.data.size = max(0.018, min(height * 0.22, width * 0.10))
    lettering.data.extrude = 0.0005
    lettering.data.materials.append(accent_material)
    bpy.ops.object.select_all(action="DESELECT")
    lettering.select_set(True)
    bpy.context.view_layer.objects.active = lettering
    bpy.ops.object.convert(target="MESH")
    lettering = bpy.context.object
    return [label, stripe, lettering]


def import_prebuilt_merchandise(manifest_path=DEFAULT_MANIFEST):
    """Return (objects, chilled_objects); returns None when no curated models are staged."""
    if not os.path.isfile(manifest_path):
        return None
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    entries = manifest.get("products", [])
    if not entries:
        return None

    imported_objects = []
    chilled_objects = []
    prototype_cache = {}
    palettes = (
        ((0.12, 0.28, 0.25), (0.92, 0.58, 0.22)),
        ((0.18, 0.31, 0.42), (0.93, 0.80, 0.48)),
        ((0.46, 0.19, 0.13), (0.96, 0.71, 0.35)),
        ((0.31, 0.35, 0.20), (0.90, 0.82, 0.58)),
        ((0.28, 0.22, 0.38), (0.90, 0.63, 0.39)),
    )

    for entry in entries:
        source = os.path.join(os.path.dirname(manifest_path), "models", entry["file"])
        if not os.path.isfile(source):
            raise FileNotFoundError("Curated merchandise model missing: " + source)
        # Import each unique scan once. The shelf manifest intentionally reuses
        # a small curated product library; re-importing the same GLB for every
        # facing multiplies Blender object creation and render cost needlessly.
        if entry["file"] not in prototype_cache:
            before = set(bpy.data.objects)
            bpy.ops.import_scene.gltf(filepath=source)
            imported = [obj for obj in bpy.data.objects if obj not in before]
            source_meshes = [obj for obj in imported if obj.type == "MESH"]
            if not source_meshes:
                raise RuntimeError("No mesh objects imported for " + entry["sku"])
            prototypes = [
                (obj.data.copy(), obj.matrix_world.copy(), obj.name)
                for obj in source_meshes
            ]
            for obj in imported:
                bpy.data.objects.remove(obj, do_unlink=True)
            prototype_cache[entry["file"]] = prototypes

        created = []
        meshes = []
        for mesh_data, world_matrix, source_name in prototype_cache[entry["file"]]:
            obj = bpy.data.objects.new(source_name + " - CENTS instance", mesh_data.copy())
            bpy.context.scene.collection.objects.link(obj)
            obj.matrix_world = world_matrix.copy()
            created.append(obj)
            meshes.append(obj)

        # Strip all source material textures so scanned third-party logos and packaging
        # artwork cannot survive into CENTS. Keep the real product geometry.
        primary, accent = palettes[int(entry.get("palette", 0)) % len(palettes)]
        shell = _fictional_material(entry["sku"], primary, 0.12 if entry.get("metallic") else 0.0)
        for obj in meshes:
            obj.data.materials.clear()
            obj.data.materials.append(shell)

        low, high = _bounds(meshes)
        source_height = max(0.001, high.z - low.z)
        target_height = float(entry.get("height", 0.30))
        scale = target_height / source_height
        for obj in created:
            obj.scale = tuple(component * scale for component in obj.scale)
        bpy.context.view_layer.update()
        low, high = _bounds(meshes)
        center_x, center_y, base_z = entry["position"]
        for obj in created:
            obj.location.x += center_x - (low.x + high.x) * 0.5
            obj.location.y += center_y - (low.y + high.y) * 0.5
            obj.location.z += base_z - low.z
            if entry.get("yaw"):
                obj.rotation_euler.z += float(entry["yaw"])
        bpy.context.view_layer.update()
        low, high = _bounds(meshes)
        label_width = min((high.x - low.x) * 0.76, float(entry.get("label_width", 0.18)))
        label_height = min((high.z - low.z) * 0.34, float(entry.get("label_height", 0.075)))
        yaw = float(entry.get("yaw", 0.0))
        front_y = high.y + 0.004 if abs(yaw) > 1.5707963 else low.y - 0.004
        label_center = ((low.x + high.x) * 0.5, front_y, low.z + (high.z - low.z) * 0.55)
        label_mat = _label_material(entry["sku"], primary, accent)
        accent_mat = _fictional_material(entry["sku"] + " accent", accent)
        labels = _add_fictional_label(entry["sku"], entry.get("label", entry["sku"]), label_center, label_width, label_height, label_mat, accent_mat, yaw)
        imported_objects.extend(created + labels)
        if entry.get("department") == "cold-drinks":
            chilled_objects.extend(created + labels)

    return imported_objects, chilled_objects
