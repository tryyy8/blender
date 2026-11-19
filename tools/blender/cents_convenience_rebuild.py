"""CENTS convenience-store rebuild: a compact retail layout built around CC0 fixtures.

The previous store generator is intentionally not reused for its room, gondolas,
checkout, or product assortment. Only the established Ember Cola, Deli Fresh Pasta
Salad, and the existing empty commercial cooler construction are retained.
"""
import argparse
import math
import os
import sys
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from retail_store_kit import (
    make_material, make_glass, make_emissive, cube,
    build_empty_commercial_cooler, join_by_material
)
from cents_packaging import build_merchandise


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    p.add_argument("--fixtures-dir", required=True)
    p.add_argument("--preview", required=True)
    p.add_argument("--texture-size", type=int, default=256)
    return p.parse_args(argv)


def bounds(objects):
    pts = []
    for obj in objects:
        if obj.type != "MESH":
            continue
        pts.extend(obj.matrix_world @ Vector(c) for c in obj.bound_box)
    if not pts:
        raise RuntimeError("Fixture has no mesh geometry")
    return Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))), Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))


def import_fixture(path, label, target_height=None):
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    created = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in created if o.type == "MESH"]
    if not meshes:
        raise RuntimeError("No meshes imported from " + path)
    root = bpy.data.objects.new(label + " root", None)
    bpy.context.scene.collection.objects.link(root)
    for obj in created:
        world = obj.matrix_world.copy()
        obj.parent = root
        obj.matrix_world = world
    root.location = (0, 0, 0)
    bpy.context.view_layer.update()
    lo, hi = bounds(meshes)
    if target_height:
        factor = target_height / max(0.001, hi.z - lo.z)
        root.scale = (factor, factor, factor)
        bpy.context.view_layer.update()
        lo, hi = bounds(meshes)
    return root, created, meshes, lo, hi


def place_fixture(path, label, center, yaw=0.0, target_height=None):
    root, created, meshes, lo, hi = import_fixture(path, label, target_height)
    root.rotation_euler.z = yaw
    bpy.context.view_layer.update()
    lo, hi = bounds(meshes)
    current = (lo + hi) * 0.5
    root.location.x += center[0] - current.x
    root.location.y += center[1] - current.y
    root.location.z += center[2] - lo.z
    bpy.context.view_layer.update()
    # CENTS currently reads node-local transforms rather than parent matrices.
    # Bake the placed fixture hierarchy into world-space object transforms.
    for obj in created:
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
    bpy.data.objects.remove(root, do_unlink=True)
    bpy.context.view_layer.update()
    lo, hi = bounds(meshes)
    print("FIXTURE", label, "bounds", tuple(round(v, 3) for v in (hi - lo)), "meshes", len(meshes))
    return None, created, meshes


def add_word(text, location, size, material, rotation=(math.pi / 2, 0, 0)):
    bpy.ops.object.text_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = "CENTS sign lettering " + text
    obj.data.body = text
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.004
    obj.data.bevel_depth = 0.001
    obj.data.materials.append(material)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    return bpy.context.object


def build_detailed_cooler_bank(size):
    """Retain the authored four-bay cooler style; each glass door has its own hinge pivot."""
    interior = make_material("Cooler interior enamel", "painted", (0.30, 0.39, 0.37), 0.48, size=size)
    stainless = make_material("Cooler brushed stainless trim", "metal", (0.39, 0.44, 0.42), 0.30, 0.68, size)
    gasket = make_material("Cooler charcoal door gasket", "painted", (0.035, 0.052, 0.050), 0.78, size=size)
    glass = make_glass("Cooler blue-green insulated door glass", (0.34, 0.49, 0.48), 0.20, 0.04)
    body = make_material("Cooler graphite enamel", "metal", (0.12, 0.15, 0.15), 0.28, 0.48, size)
    liner = make_material("Cooler pale interior liner", "painted", (0.30, 0.39, 0.37), 0.48, size=size)
    led = make_emissive("Cooler cold-white LED", (0.72, 0.88, 1.0))

    def part(name, loc, dims, material, bevel=0.02):
        return cube(name, loc, dims, material, bevel)

    centers = (-4.30, -3.36, -2.42, -1.48)
    front_y = 2.78
    for index, x in enumerate(centers, 1):
        prefix = "Cooler " + str(index) + " - "
        part(prefix + "insulated carcass", (x, front_y + 0.63, 1.56), (0.88, 1.26, 3.08), body, 0.075)
        part(prefix + "toe kick", (x, front_y + 0.07, 0.18), (0.82, 0.16, 0.28), gasket, 0.035)
        part(prefix + "crown cap", (x, front_y + 0.68, 3.15), (0.91, 1.30, 0.13), stainless, 0.035)
        part(prefix + "inner liner", (x, front_y + 0.055, 1.68), (0.73, 0.055, 2.54), liner, 0.012)
        part(prefix + "rear insulation panel", (x, front_y + 1.30, 1.65), (0.76, 0.07, 2.78), interior, 0.018)
        for shelf_z in (0.66, 1.30, 1.94, 2.58):
            part(prefix + "interior shelf", (x, front_y + 0.535, shelf_z), (0.69, 0.58, 0.035), stainless, 0.010)
            part(prefix + "shelf front lip", (x, front_y + 0.24, shelf_z + 0.025), (0.69, 0.035, 0.055), body, 0.012)
            for support_x in (-0.33, 0.33):
                part(prefix + "shelf support", (x + support_x, front_y + 0.525, shelf_z - 0.045), (0.025, 0.58, 0.07), stainless, 0.008)
        for light_x in (-0.335, 0.335):
            part(prefix + "LED channel", (x + light_x, front_y + 0.09, 1.70), (0.022, 0.035, 2.40), led, 0.010)

        door_parts = []
        door_parts.append(part(prefix + "magnetic door gasket", (x, front_y - 0.045, 1.66), (0.80, 0.075, 2.76), gasket, 0.045))
        door_parts.append(part(prefix + "glass door", (x, front_y - 0.097, 1.66), (0.735, 0.035, 2.68), glass, 0.028))
        for edge_x in (-0.382, 0.382):
            door_parts.append(part(prefix + "door stile", (x + edge_x, front_y - 0.127, 1.66), (0.045, 0.075, 2.75), stainless, 0.018))
        for edge_z in (0.285, 3.035):
            door_parts.append(part(prefix + "door rail", (x, front_y - 0.127, edge_z), (0.78, 0.075, 0.055), stainless, 0.018))
        door_parts.append(part(prefix + "vertical pull handle", (x + 0.285, front_y - 0.177, 1.72), (0.045, 0.075, 1.62), stainless, 0.020))
        for hinge_z in (0.52, 1.62, 2.76):
            part(prefix + "hinge barrel", (x - 0.385, front_y - 0.06, hinge_z), (0.07, 0.10, 0.19), stainless, 0.025)
        part(prefix + "top identity plaque", (x, front_y - 0.13, 2.94), (0.36, 0.018, 0.10), body, 0.018)

        bpy.ops.object.select_all(action="DESELECT")
        for obj in door_parts:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = door_parts[0]
        bpy.ops.object.join()
        door = bpy.context.object
        door.name = prefix + "HINGED GLASS DOOR ASSEMBLY"
        hinge = (x - 0.40, front_y - 0.097, 1.66)
        bpy.context.scene.cursor.location = hinge
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        door["cents_interaction"] = "cooler_door"
        door["cents_hinge_origin"] = list(hinge)
        door["cents_open_angle_degrees"] = 105.0
        door["cents_door_id"] = "cooler-door-" + str(index)
        print("COOLER", index, "hinged door mesh", len(door.data.polygons))


def build(options):
    """Assemble the CENTS sales floor from retained premade merchandising only.

    The former generated room shell, ceiling, architectural lighting, queue rails,
    coffee station, signage and supermarket-style checkout are deliberately not
    emitted. They were the rejected previous store, not reusable store assets.
    """
    bpy.ops.object.select_all(action="SELECT)
    bpy.ops.object.delete(use_global=False)
    size = options.texture_size

    # Only the two approved authored SKUs survive the rebuild.
    product_objects, chilled = build_merchandise(size, minimal=True)
    keep = list(product_objects)
    if len(keep) != 2:
        raise RuntimeError("Minimal merchandise mode must produce exactly Ember Cola and Deli Fresh Pasta Salad")

    # Preserve the premade grocery shelving the user approved. No new shelf
    # geometry or invented shelf stock is generated here.
    shelf_path = os.path.join(options.fixtures_dir, "grocery-shelf-run.glb")
    shelf_positions = [
        (-1.55, -1.05, math.pi / 2),
        (-1.55, 1.05, math.pi / 2),
        (1.55, -1.05, math.pi / 2),
        (1.55, 1.05, math.pi / 2),
    ]
    for i, (x, y, yaw) in enumerate(shelf_positions, 1):
        place_fixture(shelf_path, "Approved premade grocery shelving " + str(i), (x, y, 0), yaw, target_height=1.82)
    place_fixture(shelf_path, "Approved premade perimeter shelving", (4.65, 0.85, 0), 0.0, target_height=1.82)

    # Keep the approved products as separate objects for their existing game
    # interactions; do not add the rejected generic catalogue.
    keep[0].location = (3.15, -1.35, 1.22)
    keep[1].location = (3.48, -1.35, 1.22)

    # Retain the existing cooler interaction assemblies, but do not recreate
    # the previous room, floor, ceiling, lights, wall treatment or checkout.
    build_detailed_cooler_bank(size)

    bpy.ops.object.select_all(action="SELECT")
    selected = bpy.context.selected_objects
    if selected:
        bpy.context.view_layer.objects.active = selected[0]
    bpy.ops.export_scene.gltf(
        filepath=os.path.abspath(options.output), export_format="GLB",
        export_apply=True, export_texcoords=True, export_normals=True,
        export_materials="EXPORT", export_image_format="AUTO", export_yup=True
    )
    print("CENTS stripped-back merchandising scene exported:", os.path.abspath(options.output))

    # Keep the review output useful without reintroducing any room geometry.
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 825
    scene.render.resolution_percentage = 70
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"
    bpy.ops.object.camera_add(location=(8.0, -10.0, 8.0))
    camera = bpy.context.object
    camera.name = "CENTS merchandising review camera"
    camera.rotation_euler = (Vector((0.0, 0.0, 1.0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 42
    scene.camera = camera
    scene.render.filepath = os.path.abspath(options.preview)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    build(args())
