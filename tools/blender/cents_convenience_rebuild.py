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
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    size = options.texture_size
    # New palette and room proportions: 12 x 9 m, not the previous 16 x 12 layout.
    wall = make_material("CENTS warm plaster", "plaster", (0.76, 0.72, 0.63), 0.9, size=size)
    floor = make_material("CENTS warm terrazzo", "concrete", (0.48, 0.48, 0.43), 0.76, size=size)
    dark = make_material("CENTS deep evergreen", "painted", (0.035, 0.13, 0.105), 0.42, size=size)
    trim = make_material("CENTS graphite metal", "metal", (0.10, 0.13, 0.13), 0.36, 0.55, size)
    brass = make_material("CENTS warm brass", "metal", (0.62, 0.39, 0.16), 0.32, 0.72, size)
    glass = make_glass("CENTS storefront glazing", (0.25, 0.37, 0.39), 0.10, 0.04, 0.26)
    ceiling = make_material("CENTS ceiling ivory", "painted", (0.86, 0.83, 0.75), 0.72, size=size)
    glow = make_emissive("CENTS warm LED", (1.0, 0.79, 0.52))
    parts = []

    def add(*a, **kw):
        o = cube(*a, **kw)
        parts.append(o)
        return o

    # Shell: compact neighborhood convenience store with a clear sightline.
    add("New store floor slab", (0, 0, -0.12), (12, 9, 0.24), floor, 0.035)
    add("Rear wall", (0, 4.38, 2.15), (12, 0.24, 4.3), wall, 0.045)
    add("Left wall", (-5.88, 0, 2.15), (0.24, 9, 4.3), wall, 0.045)
    add("Right wall", (5.88, 0, 2.15), (0.24, 9, 4.3), wall, 0.045)
    add("Front left pier", (-5.2, -4.38, 2.0), (1.6, 0.24, 4.0), wall, 0.035)
    add("Front right pier", (5.2, -4.38, 2.0), (1.6, 0.24, 4.0), wall, 0.035)
    add("Front sign canopy", (0, -4.52, 3.78), (9.0, 0.48, 0.55), dark, 0.055)
    add("Front glazing left", (-3.2, -4.50, 1.9), (2.3, 0.055, 3.45), glass, 0.012)
    add("Front glazing right", (3.2, -4.50, 1.9), (2.3, 0.055, 3.45), glass, 0.012)
    add("Entry left glass leaf", (-0.56, -4.56, 1.78), (1.02, 0.065, 3.12), glass, 0.012)
    add("Entry right glass leaf", (0.56, -4.56, 1.78), (1.02, 0.065, 3.12), glass, 0.012)
    for x in (-4.38, -2.02, -1.14, 0, 1.14, 2.02, 4.38):
        add("Storefront mullion", (x, -4.59, 1.9), (0.065, 0.10, 3.56), trim, 0.01)
    add("Entry threshold", (0, -4.5, 0.035), (2.2, 0.36, 0.07), brass, 0.018)
    add("Sign inset", (0, -4.79, 3.78), (6.8, 0.035, 0.38), dark, 0.025)
    add_word("CENTS", (0, -4.82, 3.78), 0.43, glow)
    ceiling_obj = add("Ceiling", (0, 0, 4.24), (12, 9, 0.20), ceiling, 0.025)
    # Keep the roof as its own export node so preview renders can hide it without
    # hiding the entire shell or blocking all interior lighting.
    parts.remove(ceiling_obj)
    # Restrained wall bands and baseboards give the room a finished retail fit-out.
    add("Rear wall baseboard", (0, 4.22, 0.14), (11.7, 0.06, 0.20), dark, 0.01)
    add("Rear wall brand band", (0, 4.22, 2.72), (11.7, 0.06, 0.16), dark, 0.01)
    light_trim = make_material("Recessed light satin aluminum", "metal", (0.31, 0.35, 0.33), 0.29, 0.62, size)
    light_reveal = make_material("Recessed light dark reveal", "painted", (0.045, 0.055, 0.052), 0.68, size=size)
    for x in (-3.8, 0.0, 3.8):
        for y in (-2.0, 1.65):
            add("LED troffer recessed housing", (x, y, 4.035), (2.08, 0.34, 0.085), light_reveal, 0.055)
            add("LED troffer perimeter bezel", (x, y, 3.984), (1.98, 0.29, 0.035), light_trim, 0.038)
            add("LED opal diffuser lens", (x, y, 3.960), (1.84, 0.245, 0.018), glow, 0.028)
            for end_x in (-0.96, 0.96):
                add("LED troffer end cap", (x + end_x, y, 3.963), (0.035, 0.25, 0.028), light_trim, 0.010)

    # Keep only the two established custom products. The scanned-brand catalogue is not used.
    product_objects, chilled = build_merchandise(size, minimal=True)
    keep = list(product_objects)
    if len(keep) != 2:
        raise RuntimeError("Minimal merchandise mode must produce exactly Ember Cola and Deli Fresh Pasta Salad")

    # Import CC0 stocked steel gondola modules; their grocery stock is unbranded.
    shelf_path = os.path.join(options.fixtures_dir, "grocery-shelf-run.glb")
    shelf_positions = [(-1.55, -0.05, math.pi / 2), (1.55, -0.05, math.pi / 2)]
    for i, (x, y, yaw) in enumerate(shelf_positions, 1):
        place_fixture(shelf_path, "CC0 grocery gondola " + str(i), (x, y, 0), yaw, target_height=1.82)

    # Proper checkout lane is a separate premade CC0 asset, replacing the old block-built desk.
    checkout_path = os.path.join(options.fixtures_dir, "checkout-counter.glb")
    place_fixture(checkout_path, "CC0 staffed checkout", (4.15, -2.45, 0), math.pi / 2, target_height=1.72)

    # The retained four-bay cooler design is kept, with separately animatable glass doors.

    # Retained products sit as distinct, real objects at the deli end of the counter.
    # Their original meshes and materials remain untouched.
    keep[0].location = (3.15, -1.35, 1.22)
    keep[1].location = (3.48, -1.35, 1.22)

    # Checkout queue stanchions and impulse display define customer flow without blocking aisles.
    for x in (2.55, 3.35):
        add("Queue post weighted base", (x, -3.65, 0.08), (0.28, 0.28, 0.16), trim, 0.05)
        add("Queue post upright", (x, -3.65, 0.54), (0.055, 0.055, 0.82), brass, 0.02)
    add("Queue rail", (2.95, -3.65, 0.91), (0.82, 0.035, 0.035), brass, 0.015)

    # Coffee/hot drinks are a small wall station, not a kitchen counter.
    coffee = make_material("Coffee station enamel", "metal", (0.10, 0.13, 0.13), 0.30, 0.55, size)
    wood = make_material("Coffee station walnut", "wood", (0.30, 0.18, 0.11), 0.52, size=size)
    add("Coffee station base cabinet", (-4.65, 1.90, 0.52), (1.65, 0.68, 1.04), coffee, 0.05)
    add("Coffee station counter", (-4.65, 1.90, 1.08), (1.78, 0.78, 0.12), wood, 0.035)
    for x in (-5.15, -4.65, -4.15):
        add("Commercial coffee brewer", (x, 1.82, 1.47), (0.38, 0.42, 0.66), coffee, 0.04)
        add("Coffee brewer drip tray", (x, 1.58, 1.18), (0.32, 0.16, 0.035), brass, 0.01)
    add("Coffee station header", (-4.65, 2.30, 2.05), (1.78, 0.12, 0.30), dark, 0.025)

    # Store department signs: restrained and legible, not a supermarket-sized aisle system.
    add("Cold drinks wall sign", (-2.9, 4.20, 3.15), (3.0, 0.08, 0.32), dark, 0.025)
    add_word("COLD DRINKS", (-2.9, 4.14, 3.15), 0.16, glow)
    add("Snacks and pantry sign", (0, 4.20, 3.45), (3.1, 0.08, 0.30), dark, 0.025)
    add_word("SNACKS  •  PANTRY", (0, 4.14, 3.45), 0.15, glow)

    # Keep the room modules separate; only the static shell is joined by material.
    join_by_material(parts, "CENTS_RedesignedShell")
    build_detailed_cooler_bank(size)
    bpy.ops.object.select_all(action="SELECT")
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.export_scene.gltf(
        filepath=os.path.abspath(options.output), export_format="GLB",
        export_apply=True, export_texcoords=True, export_normals=True,
        export_materials="EXPORT", export_image_format="AUTO", export_yup=True
    )
    print("CENTS redesigned convenience store exported:", os.path.abspath(options.output))

    # Keep the roof in the exported GLB but hide it for the two interior review renders.
    ceiling_obj.hide_render = True
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 12
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 825
    scene.render.resolution_percentage = 70
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 0.25
    world = bpy.data.worlds.new("CENTS retail preview world") if not scene.world else scene.world
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.22, 0.26, 0.27, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.75
    target = Vector((0, 0, 1.2))
    for name, loc, energy, radius in (
        ("Store key", (0, -7, 10), 2600, 8),
        ("Store fill", (-7, 1, 7), 1800, 7),
        ("Store rear", (5, 6, 8), 2100, 6),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = radius
        light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()

    # Review renders must expose the interior rather than photograph the opaque roof.
    # First view: standing just inside the entrance, looking down the shopping floor.
    bpy.ops.object.camera_add(location=(0.0, -3.65, 2.05))
    interior_cam = bpy.context.object
    interior_cam.name = "CENTS interior aisle review camera"
    interior_target = Vector((0.0, 2.65, 1.25))
    interior_cam.rotation_euler = (interior_target - interior_cam.location).to_track_quat("-Z", "Y").to_euler()
    interior_cam.data.lens = 30
    scene.camera = interior_cam
    scene.render.filepath = os.path.abspath(options.preview)
    bpy.ops.render.render(write_still=True)

    # Second view: clean overhead layout review with the roof hidden.
    bpy.ops.object.camera_add(location=(0.0, 0.0, 15.5))
    plan_cam = bpy.context.object
    plan_cam.name = "CENTS overhead layout review camera"
    plan_cam.rotation_euler = (Vector((0.0, 0.0, 0.0)) - plan_cam.location).to_track_quat("-Z", "Y").to_euler()
    plan_cam.data.type = "ORTHO"
    plan_cam.data.ortho_scale = 14.5
    scene.camera = plan_cam
    scene.render.filepath = os.path.abspath(options.preview).replace(".png", "-entrance.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    build(args())
