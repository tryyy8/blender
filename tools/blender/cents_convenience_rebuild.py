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


def build_new_store_shell(size):
    """Create a fresh compact neighborhood-store shell; none of the rejected room survives."""
    floor = make_material("CENTS new store warm terrazzo floor", "concrete", (0.56, 0.55, 0.49), 0.78, size=size)
    wall = make_material("CENTS new store warm ivory plaster", "plaster", (0.79, 0.75, 0.66), 0.88, size=size)
    accent = make_material("CENTS new store deep evergreen trim", "painted", (0.10, 0.24, 0.21), 0.55, size=size)
    dark = make_material("CENTS new store charcoal metal", "metal", (0.075, 0.095, 0.09), 0.34, 0.55, size)
    wood = make_material("CENTS new store warm oak trim", "wood", (0.38, 0.24, 0.14), 0.56, size=size)
    glass = make_glass("CENTS new storefront clear glass", (0.40, 0.58, 0.61), 0.12, 0.04, 0.24)
    light = make_emissive("CENTS new ceiling diffuser", (0.92, 0.86, 0.70))

    # Fresh 10 m x 9 m interior. This is new architecture, not reused old-store geometry.
    cube("CENTS NEW STORE floor slab", (0, 0, -0.13), (10.0, 9.0, 0.26), floor, 0.025)
    cube("CENTS NEW STORE rear wall", (0, 4.42, 1.82), (10.0, 0.22, 3.64), wall, 0.025)
    cube("CENTS NEW STORE left wall", (-4.90, 0, 1.82), (0.20, 8.65, 3.64), wall, 0.025)
    cube("CENTS NEW STORE right wall", (4.90, 0, 1.82), (0.20, 8.65, 3.64), wall, 0.025)
    cube("CENTS NEW STORE ceiling", (0, 0, 3.68), (10.0, 9.0, 0.20), wall, 0.02)

    # Front shopfront: two glazed display windows and a central double-width entry.
    for x in (-3.55, 3.55):
        cube("CENTS NEW STORE front pier", (x, -4.42, 1.82), (2.90, 0.22, 3.64), wall, 0.02)
    cube("CENTS NEW STORE front header", (0, -4.42, 3.34), (4.25, 0.22, 0.60), accent, 0.025)
    for x in (-2.35, 2.35):
        cube("CENTS NEW STORE storefront glazing", (x, -4.30, 1.82), (2.10, 0.055, 2.72), glass, 0.008)
        for edge in (-1, 1):
            cube("CENTS NEW STORE storefront mullion", (x + edge * 1.05, -4.36, 1.82), (0.055, 0.10, 2.82), dark, 0.008)
        cube("CENTS NEW STORE window sill", (x, -4.39, 0.43), (2.18, 0.16, 0.09), wood, 0.012)
        cube("CENTS NEW STORE window head", (x, -4.39, 3.21), (2.18, 0.16, 0.09), dark, 0.012)
    cube("CENTS NEW STORE entry glass", (0, -4.30, 1.48), (1.46, 0.055, 2.90), glass, 0.008)
    for x in (-0.76, 0.76):
        cube("CENTS NEW STORE entry jamb", (x, -4.38, 1.50), (0.075, 0.13, 3.02), dark, 0.012)
    cube("CENTS NEW STORE entry transom", (0, -4.38, 3.02), (1.56, 0.13, 0.07), dark, 0.010)
    for x in (-0.54, 0.54):
        cube("CENTS NEW STORE door pull", (x, -4.42, 1.48), (0.035, 0.07, 0.62), wood, 0.012)

    # A restrained continuous wall band and timber kick plate make the new room feel finished.
    cube("CENTS NEW STORE rear green wall band", (0, 4.29, 3.12), (9.72, 0.035, 0.22), accent, 0.008)
    cube("CENTS NEW STORE left timber kick", (-4.78, 0, 0.18), (0.035, 8.55, 0.22), wood, 0.008)
    cube("CENTS NEW STORE right timber kick", (4.78, 0, 0.18), (0.035, 8.55, 0.22), wood, 0.008)
    for x in (-2.6, 0.0, 2.6):
        cube("CENTS NEW STORE ceiling light housing", (x, 0.15, 3.53), (1.35, 0.34, 0.07), dark, 0.025)
        cube("CENTS NEW STORE ceiling light diffuser", (x, 0.15, 3.485), (1.20, 0.25, 0.025), light, 0.012)

    sign = make_material("CENTS new store sign lettering", "painted", (0.96, 0.87, 0.66), 0.42, size=size)
    add_word("CENTS", (0, -4.285, 3.34), 0.34, sign, rotation=(-math.pi / 2, 0, 0))
    return {"floor": floor, "wall": wall, "accent": accent, "dark": dark, "wood": wood, "glass": glass}


def build(options):
    """Build a compact convenience store from fresh architecture and premade fixtures."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    size = options.texture_size
    os.makedirs(os.path.dirname(os.path.abspath(options.output)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(options.preview)), exist_ok=True)

    build_new_store_shell(size)

    # Keep only the two approved authored products, as independent game objects.
    products, chilled = build_merchandise(size, minimal=True)
    if len(products) != 2 or chilled:
        raise RuntimeError("Minimal merchandise mode must produce only Ember Cola and Deli Fresh Pasta Salad")

    # Reuse the premade shelf model the user approved. Do not generate replacement shelving.
    shelf_path = os.path.join(options.fixtures_dir, "grocery-shelf-run.glb")
    shelf_positions = [
        (-1.48, -0.95, math.pi / 2),
        (-1.48, 1.18, math.pi / 2),
        (1.38, -0.95, math.pi / 2),
        (1.38, 1.18, math.pi / 2),
    ]
    for index, (x, y, yaw) in enumerate(shelf_positions, 1):
        place_fixture(shelf_path, "Premade approved grocery shelf run " + str(index), (x, y, 0), yaw, target_height=1.82)
    place_fixture(shelf_path, "Premade approved perimeter grocery shelving", (3.75, 1.05, 0), 0.0, target_height=1.82)

    # Commercial CC0 two-door beverage coolers, imported intact rather than rebuilt from primitives.
    cooler_path = os.path.join(options.fixtures_dir, "double-glass-door-beverage-cooler.glb")
    for index, x in enumerate((-2.75, -1.40, -0.05), 1):
        cooler_label = "Premade CC0 beverage cooler " + str(index)
        _, _, cooler_meshes = place_fixture(cooler_path, cooler_label, (x, 4.00, 0), 0.0, target_height=2.0)
        # The cooler is static scenery; merge same-material parts to reduce mobile draw calls.
        join_by_material(cooler_meshes, cooler_label + " consolidated")

    # Compact CC0 checkout fixture with integrated POS; no belt or supermarket bagging lane.
    checkout_path = os.path.join(options.fixtures_dir, "shop-service-counter-with-till.glb")
    place_fixture(checkout_path, "Premade compact cash-wrap counter with integrated till and POS", (3.45, -2.75, 0), 0.0, target_height=1.22)

    # Place the two retained authored products on the transaction surface as the store's initial stock.
    products[0].location = (3.05, -2.75, 0.90)
    products[1].location = (3.34, -2.75, 0.90)

    # Export the production scene without cameras/lights or any rejected old-store objects.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=os.path.abspath(options.output), export_format="GLB",
        export_apply=True, export_texcoords=True, export_normals=True,
        export_materials="EXPORT", export_image_format="AUTO", export_yup=True
    )
    print("CENTS NEW CONVENIENCE STORE exported:", os.path.abspath(options.output))

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 75
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"
    scene.render.film_transparent = False
    # Preview-only lighting is added after the GLB export; the game renderer owns runtime lighting.
    scene.world.color = (0.22, 0.22, 0.22)
    bpy.ops.object.light_add(type="AREA", location=(0.0, 0.0, 3.25))
    key_light = bpy.context.object
    key_light.name = "Preview-only overhead store key"
    key_light.data.energy = 1800
    key_light.data.shape = "DISK"
    key_light.data.size = 7.5
    bpy.ops.object.light_add(type="AREA", location=(0.0, -2.7, 3.0))
    fill_light = bpy.context.object
    fill_light.name = "Preview-only entrance fill"
    fill_light.data.energy = 1100
    fill_light.data.shape = "DISK"
    fill_light.data.size = 5.0

    # The primary review camera is at player eye height just inside the entrance,
    # looking down the aisle toward the coolers and the compact checkout.
    bpy.ops.object.camera_add(location=(0.0, -3.35, 1.68))
    camera = bpy.context.object
    camera.name = "CENTS first-person store overview review camera"
    camera.rotation_euler = (Vector((0.0, 3.8, 1.55)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 42
    camera.data.clip_end = 40
    scene.camera = camera
    scene.render.filepath = os.path.abspath(options.preview)
    bpy.ops.render.render(write_still=True)

    # Secondary eye-level view checks the cash-wrap counter, POS and customer side.
    bpy.ops.object.camera_add(location=(0.0, -2.5, 1.68))
    checkout_camera = bpy.context.object
    checkout_camera.name = "CENTS checkout review camera"
    checkout_camera.rotation_euler = (Vector((3.35, -2.75, 0.95)) - checkout_camera.location).to_track_quat("-Z", "Y").to_euler()
    checkout_camera.data.lens = 42
    checkout_camera.data.clip_end = 40
    scene.camera = checkout_camera
    scene.render.filepath = os.path.abspath(options.preview).replace(".png", "-entrance.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    build(args())
