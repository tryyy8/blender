"""Generate a reusable, modular small-retail interior kit for CENTS asset studies.

This is generic Blender tooling. Store-specific branding, product identity, and game
configuration belong in the private CENTS repository.

Run:
  blender --background --python tools/blender/retail_store_kit.py -- --output /tmp/retail-store-kit.glb
"""
import argparse
import math
import os
import sys
import bpy
from mathutils import Matrix, Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from cents_materials import material_family
from cents_packaging import build_merchandise


def arguments():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--texture-size", type=int, default=256)
    parser.add_argument("--preview", default=None)
    return parser.parse_args(argv)


def make_material(name, family, color, roughness, metallic=0.0, size=256):
    seed = sum((i + 1) * ord(ch) for i, ch in enumerate(name)) % 2147483647
    return material_family(name, family, color, roughness, metallic, size=size, seed=seed)


def make_glass(name, color=(0.22, 0.31, 0.32), roughness=0.11, metallic=0.12, opacity=1.0):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, opacity)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Alpha"].default_value = opacity
    return material


def make_emissive(name, color):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.28
    emission_input = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
    if emission_input:
        emission_input.default_value = (*color, 1.0)
    strength_input = bsdf.inputs.get("Emission Strength")
    if strength_input:
        strength_input.default_value = 1.0
    return material


def cube(name, location, dimensions, material, bevel=0.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel > 0:
        mod = obj.modifiers.new("Designed edge transitions", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
    return obj


def cylinder(name, location, radius, depth, material, vertices=16, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    if rotation:
        obj.rotation_euler = rotation
    obj.data.materials.append(material)
    return obj


def join_by_material(objects, label):
    groups = {}
    for obj in objects:
        if obj.type != "MESH" or not obj.data.materials:
            continue
        groups.setdefault(obj.data.materials[0].name, []).append(obj)
    joined = []
    for material_name, members in groups.items():
        bpy.ops.object.select_all(action="DESELECT")
        for obj in members:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = members[0]
        bpy.ops.object.join()
        members[0].name = label + "__" + material_name.replace(" ", "_")
        joined.append(members[0])
    return joined


def build_store_kit(size, output, preview):
    mats = {
        "plaster": make_material("Retail warm plaster", "plaster", (0.72, 0.66, 0.55), 0.88, size=size),
        "paint": make_material("Retail painted accent", "painted", (0.13, 0.31, 0.29), 0.72, size=size),
        "wood": make_material("Retail warm timber", "wood", (0.34, 0.21, 0.12), 0.62, size=size),
        "metal": make_material("Retail powder coated metal", "metal", (0.12, 0.15, 0.15), 0.38, 0.52, size),
        "concrete": make_material("Retail concrete floor", "concrete", (0.43, 0.42, 0.38), 0.90, size=size),
        "glass": make_glass("Retail refrigerator and storefront glass"),
        "light": make_material("Retail warm ceiling finish", "painted", (0.91, 0.83, 0.66), 0.58, size=size),
        "packaging_a": make_material("Packaging coral", "painted", (0.73, 0.25, 0.16), 0.66, size=size),
        "packaging_b": make_material("Packaging ochre", "painted", (0.82, 0.59, 0.20), 0.66, size=size),
        "packaging_c": make_material("Packaging teal", "painted", (0.16, 0.39, 0.37), 0.66, size=size),
    }
    parts = []
    def add(*args, **kwargs):
        obj = cube(*args, **kwargs)
        parts.append(obj)
        return obj

    def flush(label):
        nonlocal parts
        join_by_material(parts, label)
        parts = []

    # Architectural shell: 16 x 12 m, 4.2 m clear interior height.
    add("Retail floor slab", (0, 0, -0.12), (16, 12, 0.24), mats["concrete"], 0.035)
    add("Rear wall", (0, 5.88, 2.1), (16, 0.24, 4.2), mats["plaster"], 0.045)
    add("Left wall", (-7.88, 0, 2.1), (0.24, 12, 4.2), mats["plaster"], 0.045)
    add("Right wall", (7.88, 0, 2.1), (0.24, 12, 4.2), mats["plaster"], 0.045)
    add("Front left pier", (-6.5, -5.88, 2.1), (2.75, 0.24, 4.2), mats["plaster"], 0.045)
    add("Front right pier", (6.5, -5.88, 2.1), (2.75, 0.24, 4.2), mats["plaster"], 0.045)
    add("Front fascia", (0, -5.88, 3.82), (10.25, 0.24, 0.76), mats["paint"], 0.035)
    # A real ceiling closes the room and makes the interior read as a store, not a cutaway.
    add("Interior ceiling roof", (0, 0, 4.16), (16, 12, 0.22), mats["light"], 0.035)
    add("Entrance header", (0, -5.88, 0.18), (3.2, 0.24, 0.36), mats["metal"], 0.018)
    # Storefront glazing and a pair of framed entry leaves.
    for x in (-4.55, -2.55, 2.55, 4.55):
        add("Storefront glass panel", (x, -5.94, 2.0), (1.75, 0.055, 3.45), mats["glass"], 0.012)
        add("Storefront mullion", (x - 0.91, -5.99, 2.0), (0.075, 0.12, 3.58), mats["metal"], 0.012)
    for x in (-0.76, 0.76):
        add("Double entry door leaf", (x, -5.96, 1.78), (0.70, 0.075, 3.18), mats["glass"], 0.012)
        add("Door stile", (x + (0.31 if x < 0 else -0.31), -6.02, 1.78), (0.055, 0.10, 3.22), mats["metal"], 0.008)
        add("Door pull", (x + (0.22 if x < 0 else -0.22), -6.10, 1.75), (0.035, 0.05, 0.46), mats["light"], 0.012)
    # Continuous sign band and a shallow canopy profile.
    add("Exterior sign backing", (0, -6.18, 4.08), (7.2, 0.32, 0.48), mats["wood"], 0.035)
    add("Sign face", (0, -6.37, 4.08), (6.7, 0.035, 0.31), mats["light"], 0.012)
    add("Storefront canopy", (0, -6.38, 3.45), (8.8, 1.15, 0.16), mats["paint"], 0.045)
    for x in (-4.1, 4.1):
        add("Canopy bracket", (x, -6.02, 3.13), (0.10, 0.74, 0.62), mats["metal"], 0.025)
    flush("StoreShell")

    # Commercial wall shelving: powder-coated uprights, slotted standards,
    # adjustable cantilever brackets, formed steel decks and ticket channels.
    slot_mat = make_material("Retail shelf perforated steel", "metal", (0.24, 0.28, 0.27), 0.42, 0.62, size)
    shelf_deck = make_material("Retail shelf satin galvanized steel", "metal", (0.48, 0.52, 0.49), 0.34, 0.72, size)
    shelf_edge = make_material("Retail shelf dark polymer price channel", "painted", (0.075, 0.095, 0.09), 0.42, size=size)
    shelf_tag = make_material("Retail shelf ticket stock", "painted", (0.91, 0.86, 0.72), 0.76, size=size)

    # Wall runs are genuine single-sided retail wall bays, with upright standards
    # and folded steel shelves rather than timber planks.
    for side in (-1, 1):
        x = side * 6.55
        if side < 0:
            shelf_center_y, shelf_length, end_y = -0.35, 7.35, 3.325
        else:
            shelf_center_y, shelf_length, end_y = 0.0, 8.6, 4.0
        for y in (-4.0, end_y):
            add("Wall bay structural upright", (x, y, 1.55), (0.075, 0.095, 3.05), mats["metal"], 0.018)
            for slot_z in range(14):
                add("Wall standard punched slot", (x - side * 0.041, y, 0.48 + slot_z * 0.16),
                    (0.012, 0.035, 0.075), shelf_edge, 0.005)
        for z in (0.40, 1.12, 1.84, 2.56):
            add("Wall bay formed steel shelf deck", (x, shelf_center_y, z),
                (0.88, shelf_length, 0.075), shelf_deck, 0.018)
            add("Wall bay folded shelf front lip", (x - side * 0.425, shelf_center_y, z + 0.047),
                (0.055, shelf_length - 0.04, 0.085), shelf_edge, 0.012)
            add("Wall bay continuous price ticket channel", (x - side * 0.462, shelf_center_y, z + 0.025),
                (0.018, shelf_length - 0.10, 0.060), mats["metal"], 0.006)
            for tag in range(12):
                ty = shelf_center_y - shelf_length * 0.46 + tag * shelf_length * 0.083
                add("Wall shelf individual price ticket", (x - side * 0.476, ty, z + 0.027),
                    (0.012, 0.24, 0.043), shelf_tag, 0.003)
            for bracket_y in (-shelf_length * 0.42, 0, shelf_length * 0.42):
                add("Wall shelf cantilever bracket", (x - side * 0.27, shelf_center_y + bracket_y, z - 0.075),
                    (0.42, 0.045, 0.045), mats["metal"], 0.010)
        # A continuous perforated back panel makes the fixture read as a retail bay.
        add("Wall bay perforated merchandising back", (x + side * 0.025, shelf_center_y, 1.60),
            (0.045, shelf_length - 0.10, 2.82), slot_mat, 0.012)
        for y in (-4.0, end_y):
            add("Wall bay molded end cap", (x - side * 0.05, y, 1.52),
                (0.12, 0.12, 3.08), mats["paint"], 0.025)
        add("Wall bay bottom kick plate", (x - side * 0.10, shelf_center_y, 0.20),
            (0.10, shelf_length, 0.28), mats["metal"], 0.025)
    flush("PerimeterShelving")

    # Double-sided gondola shelving: two commercial retail runs with a central
    # perforated spine, structural end frames, adjustable brackets, formed decks,
    # front price rails and branded top sign rails.
    for gondola_index, gx in enumerate((-2.35, 2.35), start=1):
        run_y0, run_y1 = -2.85, 3.75
        run_length = run_y1 - run_y0
        run_mid = (run_y0 + run_y1) * 0.5
        add("Gondola structural base plinth", (gx, run_mid, 0.18),
            (1.12, run_length + 0.16, 0.34), mats["metal"], 0.055)
        add("Gondola central perforated spine", (gx, run_mid, 1.68),
            (0.055, run_length, 2.88), slot_mat, 0.012)
        for end_y in (run_y0, run_y1):
            for face in (-1, 1):
                add("Gondola end frame upright", (gx + face * 0.49, end_y, 1.62),
                    (0.075, 0.10, 2.92), mats["metal"], 0.020)
                for slot_z in range(16):
                    add("Gondola upright adjustment slot", (gx + face * 0.45, end_y - 0.055, 0.48 + slot_z * 0.15),
                        (0.012, 0.012, 0.060), shelf_edge, 0.004)
        for z in (0.56, 1.25, 1.94, 2.63):
            for face in (-1, 1):
                add("Gondola formed steel shelf deck", (gx + face * 0.285, run_mid, z),
                    (0.53, run_length - 0.20, 0.075), shelf_deck, 0.018)
                add("Gondola folded front shelf lip", (gx + face * 0.545, run_mid, z + 0.047),
                    (0.045, run_length - 0.22, 0.095), shelf_edge, 0.012)
                add("Gondola continuous price ticket rail", (gx + face * 0.574, run_mid, z + 0.018),
                    (0.018, run_length - 0.24, 0.064), mats["metal"], 0.006)
                for tag in range(10):
                    ty = run_y0 + 0.38 + tag * 0.61
                    add("Gondola shelf price label", (gx + face * 0.588, ty, z + 0.020),
                        (0.012, 0.24, 0.044), shelf_tag, 0.003)
                for bracket_y in (run_y0 + 0.35, run_mid, run_y1 - 0.35):
                    add("Gondola cantilever shelf bracket", (gx + face * 0.12, bracket_y, z - 0.075),
                        (0.33, 0.045, 0.045), mats["metal"], 0.010)
        add("Gondola upper sign frame", (gx, run_mid, 3.16),
            (1.10, run_length + 0.10, 0.16), mats["paint"], 0.025)
        for face in (-1, 1):
            add("Gondola sign face insert", (gx + face * 0.56, run_mid, 3.16),
                (0.018, 2.05, 0.105), shelf_tag, 0.008)
        flush("Gondola" + str(gondola_index))

    # Two full-width commercial reach-in merchandisers, each with paired
    # insulated glass doors. The double-door format and refrigeration plinth,
    # grille, mullions, header, gaskets and interior shelving establish a real
    # convenience-store beverage cooler silhouette.
    fridge_interior = make_material("Cooler interior enamel", "painted", (0.30, 0.39, 0.37), 0.48, size=size)
    fridge_trim = make_material("Cooler brushed stainless trim", "metal", (0.39, 0.44, 0.42), 0.30, 0.68, size)
    fridge_gasket = make_material("Cooler charcoal door gasket", "painted", (0.035, 0.052, 0.050), 0.78, size=size)
    fridge_glass = make_glass("Cooler low-iron insulated clear door glass", (0.78, 0.91, 0.91), 0.045, 0.01, 0.10)
    fridge_led = make_emissive("Cooler cool-white interior LED", (0.72, 0.88, 0.96))
    fridge_dark = make_material("Cooler refrigeration vent dark", "painted", (0.025, 0.035, 0.034), 0.68, size=size)
    fridge_header = make_material("Cooler illuminated header enamel", "painted", (0.075, 0.22, 0.20), 0.32, size=size)
    for cabinet_index, cx in enumerate((-5.20, -3.32), start=1):
        cabinet_width = 1.78
        front_y, rear_y = 3.93, 5.30
        center_y = 4.66
        # Insulated shell with a true recessed cavity.
        add("Merchandiser insulated left cheek", (cx - cabinet_width/2 + 0.055, center_y, 1.67),
            (0.11, 1.38, 3.08), mats["metal"], 0.045)
        add("Merchandiser insulated right cheek", (cx + cabinet_width/2 - 0.055, center_y, 1.67),
            (0.11, 1.38, 3.08), mats["metal"], 0.045)
        add("Merchandiser insulated roof", (cx, center_y, 3.19), (cabinet_width, 1.38, 0.16), mats["metal"], 0.045)
        add("Merchandiser insulated floor", (cx, center_y, 0.14), (cabinet_width, 1.38, 0.24), mats["metal"], 0.045)
        add("Merchandiser rear liner", (cx, rear_y - 0.055, 1.70), (cabinet_width - 0.22, 0.10, 2.92),
            fridge_interior, 0.018)
        # Recessed kick grille and service access panel.
        add("Merchandiser lower service fascia", (cx, front_y + 0.12, 0.32),
            (cabinet_width - 0.10, 0.22, 0.43), fridge_dark, 0.025)
        for vent in range(19):
            vx = cx - 0.78 + vent * 0.087
            add("Merchandiser condenser ventilation louvre", (vx, front_y - 0.002, 0.34),
                (0.012, 0.018, 0.27), fridge_trim, 0.004)
        add("Merchandiser illuminated top header housing", (cx, front_y + 0.01, 3.10),
            (cabinet_width - 0.06, 0.16, 0.30), fridge_header, 0.035)
        add("Merchandiser header luminous diffuser", (cx, front_y - 0.078, 3.11),
            (cabinet_width - 0.20, 0.018, 0.17), fridge_led, 0.015)
        # A center mullion divides the two independent insulated glass doors.
        add("Merchandiser central structural mullion", (cx, front_y - 0.015, 1.78),
            (0.075, 0.12, 2.70), fridge_trim, 0.018)
        for door_index, dx in enumerate((-0.435, 0.435)):
            door_x = cx + dx
            door_width = 0.82
            add("Merchandiser continuous magnetic gasket", (door_x, front_y - 0.035, 1.78),
                (door_width, 0.075, 2.67), fridge_gasket, 0.035)
            add("Merchandiser insulated low-iron glass door", (door_x, front_y - 0.082, 1.78),
                (door_width - 0.055, 0.018, 2.57), fridge_glass, 0.018)
            for edge_x in (-door_width/2, door_width/2):
                add("Merchandiser aluminum door extrusion", (door_x + edge_x, front_y - 0.10, 1.78),
                    (0.045, 0.075, 2.68), fridge_trim, 0.014)
            for edge_z in (0.445, 3.115):
                add("Merchandiser horizontal door extrusion", (door_x, front_y - 0.10, edge_z),
                    (door_width, 0.075, 0.052), fridge_trim, 0.014)
            # Long recessed pull and three heavy-duty hinge barrels.
            handle_x = door_x + (0.315 if door_index == 0 else -0.315)
            add("Merchandiser full-height recessed pull handle", (handle_x, front_y - 0.145, 1.82),
                (0.035, 0.075, 1.42), mats["light"], 0.016)
            hinge_x = door_x + (-0.39 if door_index == 0 else 0.39)
            for hz in (0.68, 1.78, 2.86):
                add("Merchandiser heavy hinge barrel", (hinge_x, front_y - 0.10, hz),
                    (0.075, 0.11, 0.17), fridge_trim, 0.022)
        # Interior vertical standards, shelf support rails and four full-width decks.
        for sx in (-0.78, 0.0, 0.78):
            add("Merchandiser interior slotted shelf standard", (cx + sx, 4.82, 1.80),
                (0.025, 0.035, 2.48), fridge_trim, 0.008)
            for slot in range(15):
                add("Merchandiser shelf standard slot", (cx + sx, 4.795, 0.66 + slot * 0.16),
                    (0.012, 0.012, 0.065), fridge_dark, 0.003)
        for shelf_z in (0.70, 1.34, 1.98, 2.62):
            add("Merchandiser formed interior shelf deck", (cx, 4.57, shelf_z),
                (cabinet_width - 0.25, 0.64, 0.035), fridge_trim, 0.010)
            add("Merchandiser interior shelf front rail", (cx, 4.245, shelf_z + 0.035),
                (cabinet_width - 0.28, 0.035, 0.065), mats["light"], 0.010)
            for support_x in (-0.73, 0.73):
                add("Merchandiser shelf support arm", (cx + support_x, 4.57, shelf_z - 0.055),
                    (0.045, 0.60, 0.045), fridge_trim, 0.008)
        # Vertical light channels are mounted behind the door opening, not in front of products.
        for light_x in (-0.82, 0.82):
            add("Merchandiser vertical LED channel", (cx + light_x, 4.06, 1.82),
                (0.028, 0.035, 2.38), fridge_led, 0.012)
        # Bottom kickplate and top cap unify the two doors into one commercial cabinet.
        add("Merchandiser stainless toe kick", (cx, front_y - 0.035, 0.16),
            (cabinet_width, 0.13, 0.20), fridge_trim, 0.025)
    flush("Chillers")

    # Checkout island: customer side faces the entrance (-Y), cashier controls face
    # the operator side (+Y). The fixture has a layered counter, belt, scan well,
    # cash drawer, payment hardware and a separate bagging wing.
    counter_top = make_material("Checkout warm quartz laminate", "concrete", (0.70, 0.62, 0.49), 0.30, size=size)
    rubber = make_material("Checkout conveyor belt rubber", "painted", (0.035, 0.045, 0.043), 0.88, size=size)
    checkout_accent = make_material("Checkout deep evergreen enamel", "painted", (0.075, 0.22, 0.19), 0.42, size=size)
    screen = make_glass("Checkout display glass", (0.055, 0.105, 0.11), 0.18, 0.18, 0.96)
    add("Checkout sculpted cabinet", (5.55, -3.72, 0.58), (3.35, 1.30, 1.16), mats["wood"], 0.095)
    add("Checkout toe plinth", (5.55, -3.72, 0.105), (3.18, 1.18, 0.16), mats["metal"], 0.045)
    add("Checkout worktop slab", (5.55, -3.72, 1.205), (3.62, 1.48, 0.15), counter_top, 0.060)
    add("Checkout customer fascia", (5.55, -4.445, 0.58), (3.05, 0.055, 0.72), checkout_accent, 0.035)
    add("Checkout fascia brass reveal", (5.55, -4.482, 0.91), (2.84, 0.025, 0.035), mats["light"], 0.012)
    add("Checkout fascia inset timber panel", (5.55, -4.482, 0.55), (1.65, 0.026, 0.30), mats["wood"], 0.022)
    for side_x in (4.00, 7.10):
        add("Checkout end cap accent", (side_x, -3.72, 0.61), (0.055, 1.08, 0.82), checkout_accent, 0.022)
    add("Checkout cashier-side drawer face", (5.70, -3.075, 0.78), (1.15, 0.045, 0.25), fridge_trim, 0.022)
    add("Checkout drawer pull", (5.70, -3.045, 0.79), (0.32, 0.035, 0.055), mats["metal"], 0.018)
    cylinder("Checkout drawer lock", (6.22, -3.025, 0.79), 0.028, 0.018, mats["light"], vertices=24, rotation=(math.pi/2,0,0))
    # Conveyor belt with exposed roller grooves and raised side rails.
    add("Checkout conveyor belt", (5.00, -3.72, 1.292), (1.16, 0.94, 0.025), rubber, 0.018)
    for roller_y in (-4.12,-3.98,-3.84,-3.70,-3.56,-3.42,-3.28):
        add("Conveyor roller highlight", (5.00, roller_y, 1.308), (1.04, 0.012, 0.008), fridge_trim, 0.004)
    for x in (4.40, 5.60):
        add("Conveyor end stop", (x, -3.72, 1.325), (0.045, 0.98, 0.055), fridge_trim, 0.012)
    # Recessed scanner glass with a machined surround and visible scan window.
    add("Barcode scanner surround", (6.02, -3.72, 1.292), (0.44, 0.46, 0.055), mats["metal"], 0.025)
    add("Barcode scanner glass", (6.02, -3.72, 1.322), (0.32, 0.34, 0.012), screen, 0.012)
    # Main till display with a sculpted stand and a framed operator-facing screen.
    add("POS swivel pedestal", (4.55, -3.66, 1.40), (0.20, 0.22, 0.20), mats["metal"], 0.035)
    add("POS neck", (4.55, -3.66, 1.54), (0.09, 0.10, 0.22), mats["metal"], 0.025)
    add("POS monitor housing", (4.55, -3.61, 1.72), (0.52, 0.13, 0.40), mats["metal"], 0.045)
    add("POS active display", (4.55, -3.535, 1.73), (0.43, 0.018, 0.30), screen, 0.022)
    add("POS lower bezel", (4.55, -3.52, 1.515), (0.52, 0.035, 0.045), mats["metal"], 0.012)
    add("POS monitor rear cover seam", (4.55, -3.685, 1.72), (0.40, 0.018, 0.27), checkout_accent, 0.018)
    # Customer-facing keypad/card reader, angled toward the queue.
    add("POS keypad body", (4.95, -3.98, 1.39), (0.32, 0.27, 0.075), mats["metal"], 0.025)
    for row in range(3):
        for col in range(3):
            add("POS tactile key", (4.84 + col * 0.105, -4.06 + row * 0.075, 1.435),
                (0.065, 0.045, 0.018), mats["light"] if (row + col) % 3 else checkout_accent, 0.009)
    add("Contactless card reader", (6.65, -4.00, 1.40), (0.30, 0.24, 0.12), mats["metal"], 0.025)
    add("Card reader screen", (6.65, -3.93, 1.47), (0.20, 0.012, 0.065), screen, 0.008)
    add("Receipt printer housing", (4.95, -3.28, 1.36), (0.34, 0.26, 0.12), fridge_trim, 0.025)
    add("Receipt output slot", (4.95, -3.14, 1.39), (0.19, 0.012, 0.018), rubber, 0.004)
    # A separate bagging wing with a raised guard and bag-holder rail.
    add("Bagging platform", (6.60, -4.05, 1.30), (0.70, 0.58, 0.055), counter_top, 0.025)
    add("Bagging guard", (6.60, -3.75, 1.40), (0.68, 0.035, 0.18), checkout_accent, 0.014)
    add("Bag-holder upright", (6.85, -3.88, 1.53), (0.035, 0.035, 0.38), mats["metal"], 0.010)
    add("Bag-holder crossbar", (6.75, -3.88, 1.70), (0.42, 0.035, 0.035), mats["metal"], 0.010)
    add("Impulse display base", (6.90, -3.52, 1.31), (0.42, 0.48, 0.08), mats["metal"], 0.020)
    flush("Checkout")

    # Compact backroom partition and stock shelving behind the service zone.
    add("Stockroom partition", (0, 5.0, 2.05), (4.4, 0.18, 4.1), mats["plaster"], 0.025)
    add("Stockroom opening lintel", (0, 4.84, 3.65), (1.65, 0.20, 0.28), mats["paint"], 0.018)
    for z in (0.48, 1.35, 2.22, 3.09):
        add("Stockroom shelf", (-1.7, 5.42, z), (2.6, 0.70, 0.09), mats["wood"], 0.018)
    # Keep the initial backroom clear until inventory cartons are authored as
    # their own UV-mapped asset family; no coloured placeholder cubes are emitted.

    flush("Stockroom")

    # Product families use their own custom meshes and full-wrap authored artwork.
    # Print is UV-mapped onto package surfaces rather than mounted as separate label plates.
    product_objects, chilled_objects = build_merchandise(size)
    parts.extend(product_objects)
    flush("ProductDisplays")
    parts.extend(chilled_objects)
    flush("ChillerMerchandise")

    # Distributed recessed LED panels: visible luminous diffusers, shallow housings,
    # satin bezels and serviceable end caps. All hardware clears the ceiling underside.
    light_trim = make_material("Recessed light satin aluminum", "metal", (0.43, 0.48, 0.44), 0.24, 0.72, size)
    light_reveal = make_material("Recessed light dark reveal", "painted", (0.035, 0.045, 0.043), 0.72, size=size)
    light_emitter = make_emissive("CENTS warm white LED diffuser emission", (1.0, 0.82, 0.58))
    for x in (-4.8, 0.0, 4.8):
        for y in (-2.65, 1.75):
            add("LED troffer recessed housing", (x, y, 4.005), (2.18, 0.72, 0.075), light_reveal, 0.055)
            add("LED troffer perimeter bezel", (x, y, 3.957), (2.10, 0.65, 0.035), light_trim, 0.045)
            add("LED troffer luminous opal diffuser", (x, y, 3.932), (1.94, 0.49, 0.018), light_emitter, 0.045)
            for end_x in (-1.02, 1.02):
                add("LED troffer end cap", (x + end_x, y, 3.936), (0.035, 0.58, 0.028), light_trim, 0.010)
            for fastener_x in (-0.91, 0.91):
                for fastener_y in (-0.25, 0.25):
                    cylinder("LED troffer captive fastener", (x + fastener_x, y + fastener_y, 3.914),
                        0.009, 0.006, mats["metal"], vertices=12)
    flush("Lighting")

    # Modules remain separate for visibility culling and future interaction. Within each
    # module, geometry is joined by material to keep its draw-call count bounded.
    bpy.ops.object.select_all(action="SELECT")
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(output),
        export_format="GLB", export_apply=True, export_texcoords=True,
        export_normals=True, export_materials="EXPORT", export_image_format="AUTO",
        export_yup=True)
    print("Retail store kit exported:", os.path.abspath(output))

    if preview:
        scene = bpy.context.scene
        scene.render.engine = "CYCLES"
        scene.cycles.device = "CPU"
        scene.cycles.samples = 32
        scene.cycles.use_denoising = False
        scene.render.resolution_x = 1000
        scene.render.resolution_y = 750
        scene.render.resolution_percentage = 65
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = os.path.abspath(preview)
        scene.view_settings.view_transform = "Standard"
        world = bpy.data.worlds.new("Retail kit preview world") if not scene.world else scene.world
        scene.world = world
        world.use_nodes = True
        world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.24, 0.29, 0.30, 1)
        world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.55

        bpy.ops.object.camera_add(location=(15.5, -22.0, 16.0))
        camera = bpy.context.object
        camera.name = "Retail kit preview camera"
        target = Vector((0.0, 0.0, 1.55))
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.lens = 48
        scene.camera = camera

        for name, location, energy, size_value in (
            ("Large soft key", (1.0, -8.0, 15.0), 2600, 10.0),
            ("Cool fill", (-10.0, -1.0, 9.0), 1500, 8.0),
            ("Back rim", (3.0, 9.0, 12.0), 1900, 7.0)
        ):
            bpy.ops.object.light_add(type="AREA", location=location)
            light = bpy.context.object
            light.name = name
            light.data.energy = energy
            light.data.shape = "DISK"
            light.data.size = size_value
            light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()

        bpy.ops.render.render(write_still=True)
        print("Retail store kit preview rendered:", os.path.abspath(preview))


def main():
    options = arguments()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    build_store_kit(options.texture_size, options.output, options.preview)


if __name__ == "__main__":
    main()
