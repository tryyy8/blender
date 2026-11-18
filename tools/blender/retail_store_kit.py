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

    # Wall-mounted shelving stops before the rear-left refrigeration bank.
    # The former full-length left run overlapped the refrigerator cabinets.
    for side in (-1, 1):
        x = side * 6.55
        if side < 0:
            shelf_center_y, shelf_length, end_y = -0.35, 7.35, 3.325
        else:
            shelf_center_y, shelf_length, end_y = 0.0, 8.6, 4.0
        for z in (0.42, 1.18, 1.94, 2.70):
            add("Perimeter shelf", (x, shelf_center_y, z), (0.92, shelf_length, 0.10), mats["wood"], 0.022)
            add("Perimeter shelf front nosing", (x, shelf_center_y - shelf_length * 0.5, z + 0.015),
                (0.96, 0.055, 0.13), mats["paint"], 0.018)
        for y in (-4.0, end_y):
            add("Shelf end panel", (x, y, 1.50), (0.16, 0.16, 3.0), mats["paint"], 0.025)
        for z in (0.55, 1.31, 2.07, 2.83):
            add("Shelf upright bracket", (x - side * 0.36, shelf_center_y, z),
                (0.12, shelf_length - 0.20, 0.045), mats["metal"], 0.012)

    flush("PerimeterShelving")

    # Two double-sided gondolas preserve a generous central customer aisle.
    for gondola_index, x in enumerate((-2.35, 2.35), start=1):
        add("Gondola plinth", (x, 0.45, 0.18), (1.05, 6.8, 0.34), mats["metal"], 0.055)
        for z in (0.56, 1.25, 1.94, 2.63):
            add("Gondola shelf", (x, 0.45, z), (1.02, 6.55, 0.095), mats["wood"], 0.018)
            for face in (-1, 1):
                add("Shelf price rail", (x + face * 0.505, 0.45, z + 0.065), (0.035, 6.48, 0.075), mats["metal"], 0.012)
                for tag in range(9):
                    tag_y = -2.55 + tag * 0.72
                    add("Shelf price ticket", (x + face * 0.527, tag_y, z + 0.065), (0.012, 0.25, 0.052), mats["light"], 0.004)
        for y in (-2.85, 3.75):
            add("Gondola upright", (x, y, 1.58), (1.08, 0.10, 2.95), mats["metal"], 0.025)
        add("Gondola header rail", (x, 0.45, 3.12), (1.10, 6.65, 0.13), mats["paint"], 0.025)
        flush("Gondola" + str(gondola_index))

    # Four authored upright beverage coolers. Each cabinet has a layered carcass,
    # recessed lit interior, gasketed door frame, hardware and formed shelf supports.
    fridge_interior = make_material("Cooler interior enamel", "painted", (0.30, 0.39, 0.37), 0.48, size=size)
    fridge_trim = make_material("Cooler brushed stainless trim", "metal", (0.39, 0.44, 0.42), 0.30, 0.68, size)
    fridge_gasket = make_material("Cooler charcoal door gasket", "painted", (0.035, 0.052, 0.050), 0.78, size=size)
    fridge_glass = make_glass("Cooler low-iron insulated clear door glass", (0.72, 0.88, 0.87), 0.075, 0.02, 0.14)
    fridge_led = make_emissive("Cooler cool-white interior LED", (0.70, 0.86, 0.92))
    for i in range(4):
        x = -5.70 + i * 0.94
        # Hollow insulated cabinet: side walls, crown, toe deck and rear liner.
        # The old full-volume carcass and front inner-liner occluded the merchandise.
        add("Cooler insulated left side wall", (x - 0.395, 4.68, 1.56), (0.09, 1.24, 3.00), mats["metal"], 0.045)
        add("Cooler insulated right side wall", (x + 0.395, 4.68, 1.56), (0.09, 1.24, 3.00), mats["metal"], 0.045)
        add("Cooler top insulation deck", (x, 4.68, 3.045), (0.88, 1.24, 0.11), mats["metal"], 0.035)
        add("Cooler lower insulation deck", (x, 4.68, 0.075), (0.88, 1.24, 0.15), mats["metal"], 0.035)
        add("Cooler toe kick", (x, 4.015, 0.18), (0.82, 0.16, 0.28), fridge_gasket, 0.035)
        add("Cooler crown cap", (x, 4.66, 3.15), (0.91, 1.30, 0.13), fridge_trim, 0.035)
        add("Cooler rear insulation panel", (x, 5.255, 1.65), (0.76, 0.07, 2.78), fridge_interior, 0.018)
        # Bright internal liner rails define a clean display cavity without blocking it.
        for liner_x in (-0.335, 0.335):
            add("Cooler interior liner rail", (x + liner_x, 4.62, 1.66), (0.025, 1.12, 2.52), fridge_interior, 0.010)
        add("Cooler magnetic door gasket", (x, 3.997, 1.66), (0.80, 0.075, 2.76), fridge_gasket, 0.045)
        add("Cooler glass door", (x, 3.945, 1.66), (0.735, 0.035, 2.68), fridge_glass, 0.028)
        for edge_x in (-0.382, 0.382):
            add("Cooler door stile", (x + edge_x, 3.915, 1.66), (0.045, 0.075, 2.75), fridge_trim, 0.018)
        for edge_z in (0.285, 3.035):
            add("Cooler door rail", (x, 3.915, edge_z), (0.78, 0.075, 0.055), fridge_trim, 0.018)
        # Full-height pull handle, hinge barrels and subtle brand plaque.
        add("Cooler vertical pull handle", (x + 0.285, 3.865, 1.72), (0.045, 0.075, 1.62), mats["light"], 0.020)
        for hinge_z in (0.52, 1.62, 2.76):
            add("Cooler hinge barrel", (x - 0.385, 3.96, hinge_z), (0.07, 0.10, 0.19), fridge_trim, 0.025)
        add("Cooler top identity plaque", (x, 3.902, 2.94), (0.36, 0.018, 0.10), mats["paint"], 0.018)
        # Shelves sit inside the cabinet, with front lips and side support pins.
        for shelf_z in (0.66, 1.30, 1.94, 2.58):
            add("Cooler interior shelf", (x, 4.48, shelf_z), (0.69, 0.58, 0.035), fridge_trim, 0.010)
            add("Cooler shelf front lip", (x, 4.185, shelf_z + 0.025), (0.69, 0.035, 0.055), mats["light"], 0.012)
            for support_x in (-0.33, 0.33):
                add("Cooler shelf support", (x + support_x, 4.47, shelf_z - 0.045), (0.025, 0.58, 0.07), fridge_trim, 0.008)
        # Vertical cold-white light channels inside each door reveal.
        for light_x in (-0.335, 0.335):
            add("Cooler luminous vertical LED channel", (x + light_x, 4.035, 1.70), (0.022, 0.035, 2.40), fridge_led, 0.010)
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
