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
from mathutils import Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from cents_materials import material_family


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


def make_glass(name, color=(0.10, 0.20, 0.23), roughness=0.18, metallic=0.18):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
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

    # Wall-mounted gondola and backwall shelves, with a restrained warm timber trim.
    for side in (-1, 1):
        x = side * 6.55
        for z in (0.42, 1.18, 1.94, 2.70):
            add("Perimeter shelf", (x, 0.0, z), (0.92, 8.6, 0.10), mats["wood"], 0.022)
        for y in (-4.0, 4.0):
            add("Shelf end panel", (x, y, 1.50), (0.16, 0.16, 3.0), mats["paint"], 0.025)

    flush("PerimeterShelving")

    # Two double-sided gondolas preserve a generous central customer aisle.
    for gondola_index, x in enumerate((-2.35, 2.35), start=1):
        add("Gondola plinth", (x, 0.45, 0.18), (1.05, 6.8, 0.34), mats["metal"], 0.055)
        for z in (0.56, 1.25, 1.94, 2.63):
            add("Gondola shelf", (x, 0.45, z), (1.02, 6.55, 0.095), mats["wood"], 0.018)
        for y in (-2.85, 3.75):
            add("Gondola upright", (x, y, 1.58), (1.08, 0.10, 2.95), mats["metal"], 0.025)
        add("Gondola header rail", (x, 0.45, 3.12), (1.10, 6.65, 0.13), mats["paint"], 0.025)
        flush("Gondola" + str(gondola_index))

    # Chilled display: dark cabinet bodies, glass doors, shelves and handles.
    for i in range(4):
        x = -5.85 + i * 0.92
        add("Chiller cabinet", (x, 4.65, 1.55), (0.86, 1.25, 3.05), mats["metal"], 0.055)
        add("Chiller glass door", (x, 3.99, 1.65), (0.72, 0.055, 2.65), mats["glass"], 0.018)
        add("Chiller door handle", (x + 0.28, 3.94, 1.65), (0.035, 0.045, 2.15), mats["light"], 0.012)
        for z in (0.68, 1.34, 2.0, 2.66):
            add("Chiller shelf", (x, 4.50, z), (0.72, 0.60, 0.045), mats["light"], 0.008)
    flush("Chillers")

    # Checkout counter, staff-side worktop and POS hardware.
    add("Checkout cabinet", (5.55, -3.72, 0.58), (3.35, 1.30, 1.16), mats["wood"], 0.065)
    add("Checkout worktop", (5.55, -3.72, 1.20), (3.55, 1.42, 0.12), mats["light"], 0.035)
    add("Checkout accent fascia", (5.55, -3.04, 0.57), (3.10, 0.045, 0.70), mats["paint"], 0.025)
    add("POS terminal base", (4.55, -3.68, 1.32), (0.42, 0.34, 0.18), mats["metal"], 0.025)
    add("POS display", (4.55, -3.55, 1.53), (0.38, 0.06, 0.25), mats["glass"], 0.012)
    add("Impulse display base", (6.85, -4.0, 1.30), (0.55, 0.55, 0.10), mats["metal"], 0.018)
    flush("Checkout")

    # Compact backroom partition and stock shelving behind the service zone.
    add("Stockroom partition", (0, 5.0, 2.05), (4.4, 0.18, 4.1), mats["plaster"], 0.025)
    add("Stockroom opening lintel", (0, 4.84, 3.65), (1.65, 0.20, 0.28), mats["paint"], 0.018)
    for z in (0.48, 1.35, 2.22, 3.09):
        add("Stockroom shelf", (-1.7, 5.42, z), (2.6, 0.70, 0.09), mats["wood"], 0.018)
    for i in range(6):
        x = -2.65 + (i % 3) * 0.78
        z = 0.78 + (i // 3) * 0.92
        add("Stock carton", (x, 5.18, z), (0.62, 0.58, 0.62), mats["packaging_a" if i % 3 == 0 else "packaging_b" if i % 3 == 1 else "packaging_c"], 0.025)

    flush("Stockroom")

    # Product silhouettes: deliberately varied packaging families, not text labels.
    package_mats = (mats["packaging_a"], mats["packaging_b"], mats["packaging_c"])
    for row, z in enumerate((0.76, 1.45, 2.14)):
        for shelf_y in (-2.0, 0.45, 2.90):
            for item in range(9):
                x = -2.80 + item * 0.34
                material = package_mats[(item + row + int(shelf_y * 10)) % 3]
                if item % 3 == 0:
                    obj = cylinder("Bottle silhouette", (x, shelf_y, z + 0.18), 0.105, 0.36, material, 12)
                    parts.append(obj)
                    add("Bottle neck", (x, shelf_y, z + 0.39), (0.09, 0.09, 0.10), material, 0.018)
                elif item % 3 == 1:
                    add("Carton silhouette", (x, shelf_y, z + 0.16), (0.22, 0.22, 0.32), material, 0.025)
                else:
                    add("Snack pouch silhouette", (x, shelf_y, z + 0.13), (0.24, 0.14, 0.26), material, 0.035)

    flush("ProductDisplays")

    # Ceiling is intentionally omitted in the kit preview; lighting fixtures establish scale.
    for x in (-4.5, 0.0, 4.5):
        add("Linear ceiling light housing", (x, 0.4, 4.05), (2.2, 0.24, 0.10), mats["metal"], 0.025)
        add("Linear ceiling diffuser", (x, 0.4, 3.985), (2.0, 0.19, 0.035), mats["light"], 0.018)
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
        scene.cycles.samples = 16
        scene.cycles.use_denoising = True
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
