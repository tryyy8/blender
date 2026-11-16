"""Generate a grounded stylized-realism commercial building for CENTS District 01.

Run:
  blender --background --python tools/blender/district01_commercial_building.py -- --output /tmp/district01-building.glb
"""
import argparse
import math
import os
import sys
import bpy
from mathutils import Vector
from cents_materials import material_family


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    return p.parse_args(argv)


def flat_material(name, color, rough=0.75, metal=0.0):
    """Use a restrained, low-noise PBR response for clean glazing."""
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return material


def mat(name, color, rough=0.75, metal=0.0):
    """Build a surface using its own tileable material-family maps."""
    lowered = name.lower()
    if "glass" in lowered or "glazing" in lowered:
        return flat_material(name, color, rough, metal)
    if "plaster" in lowered or "lime render" in lowered:
        family = "plaster"
    elif "stone" in lowered or "sandstone" in lowered or "limestone" in lowered:
        family = "stone"
    elif "bronze" in lowered or "metal" in lowered:
        family = "metal"
    elif "hardwood" in lowered or "timber" in lowered or "wood" in lowered:
        family = "wood"
    elif "concrete" in lowered:
        family = "concrete"
    elif "canvas" in lowered or "fabric" in lowered:
        family = "fabric"
    else:
        family = "painted"

    seed = sum((index + 1) * ord(char) for index, char in enumerate(name)) % 2147483647
    return material_family(name, family, color, rough, metal, size=384, seed=seed)

def cube(name, loc, dims, material, bevel=0.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    if bevel:
        b = o.modifiers.new("Softened arrises", "BEVEL")
        b.width = bevel
        b.segments = 2
        o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return o


def cylinder_between(name, a, b, radius, material, vertices=10):
    direction = Vector(b) - Vector(a)
    midpoint = (Vector(a) + Vector(b)) * 0.5
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
        depth=direction.length, location=midpoint)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = direction.to_track_quat("Z", "Y")
    o.data.materials.append(material)
    return o


def main():
    out = args().output
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    plaster = mat("Warm aged lime render", (0.66, 0.59, 0.49), 0.88)
    stone = mat("Weathered sandstone", (0.48, 0.43, 0.35), 0.92)
    pale_stone = mat("Pale limestone trim", (0.72, 0.66, 0.55), 0.82)
    dark = mat("Dark bronze anodized metal", (0.075, 0.095, 0.092), 0.34, 0.68)
    glass = mat("Smoky reflective glazing", (0.055, 0.12, 0.145), 0.16, 0.32)
    glass_lit = mat("Interior warm glass", (0.25, 0.22, 0.16), 0.28, 0.12)
    wood = mat("Oiled hardwood", (0.25, 0.15, 0.075), 0.58)
    concrete = mat("Roof concrete", (0.39, 0.38, 0.34), 0.93)
    canvas = mat("Muted olive awning fabric", (0.29, 0.32, 0.24), 0.94)
    signmat = mat("Deep charcoal shop fascia", (0.09, 0.105, 0.10), 0.7)

    # Building mass: 18 m wide, 13 m deep, four occupied levels plus roof.
    cube("Main masonry volume", (0, 0, 8.2), (18, 13, 16.4), plaster, 0.09)
    cube("Ground-floor sandstone base", (0, -6.58, 1.55), (18.08, 0.22, 3.1), stone, 0.035)
    cube("First-floor string course", (0, -6.62, 3.32), (18.2, 0.28, 0.22), pale_stone, 0.035)
    cube("Upper cornice lower moulding", (0, -6.60, 15.45), (18.45, 0.36, 0.24), pale_stone, 0.045)
    cube("Upper cornice shadow line", (0, -6.60, 15.72), (18.55, 0.30, 0.10), stone, 0.025)
    cube("Parapet coping", (0, -6.60, 16.35), (18.45, 0.32, 0.18), pale_stone, 0.035)
    cube("Roof parapet front", (0, -6.35, 16.05), (18.0, 0.30, 0.62), plaster, 0.035)

    # Pilasters and recessed vertical bays create a coherent facade composition.
    for x in (-8.55, -4.35, 0, 4.35, 8.55):
        cube("Facade vertical pilaster", (x, -6.62, 9.2), (0.30, 0.28, 11.9), pale_stone, 0.035)
        cube("Pilaster capital", (x, -6.68, 15.15), (0.52, 0.40, 0.22), pale_stone, 0.035)
        cube("Pilaster base", (x, -6.68, 3.52), (0.48, 0.38, 0.25), pale_stone, 0.03)

    # Three upper storeys, varied window proportions and deep stone reveals.
    levels = (5.35, 8.55, 11.75)
    xs = (-6.35, -2.15, 2.15, 6.35)
    for level_i, z in enumerate(levels):
        for j, x in enumerate(xs):
            width = 1.72 if (j + level_i) % 3 else 1.9
            height = 2.18 if level_i != 1 else 2.32
            cube("Window recessed shadow", (x, -6.60, z), (width + 0.34, 0.12, height + 0.36), stone, 0.025)
            cube("Window glazing", (x, -6.69, z), (width, 0.055, height), glass if (j + level_i) % 4 else glass_lit, 0.012)
            for side in (-1, 1):
                cube("Window bronze jamb", (x + side * (width / 2 + 0.055), -6.77, z), (0.075, 0.10, height + 0.10), dark, 0.012)
            cube("Window head", (x, -6.78, z + height / 2 + 0.07), (width + 0.20, 0.25, 0.14), pale_stone, 0.025)
            cube("Projecting stone sill", (x, -6.82, z - height / 2 - 0.10), (width + 0.34, 0.42, 0.16), pale_stone, 0.025)
            cube("Window centre mullion", (x, -6.78, z), (0.055, 0.08, height), dark, 0.008)
            cube("Window transom", (x, -6.78, z + 0.18), (width, 0.08, 0.055), dark, 0.008)
            # Selected bays have shallow balconies with actual metal balustrades.
            if (j + level_i) % 3 == 1 and level_i > 0:
                balcony_z = z - height / 2 - 0.28
                cube("Balcony stone slab", (x, -7.05, balcony_z), (width + 0.65, 0.92, 0.16), pale_stone, 0.035)
                cylinder_between("Balcony top rail", (x - width/2 - 0.28, -7.50, balcony_z + 0.82),
                                 (x + width/2 + 0.28, -7.50, balcony_z + 0.82), 0.035, dark)
                for k in range(7):
                    px = x - width/2 - 0.22 + k * (width + 0.44) / 6
                    cylinder_between("Balcony baluster", (px, -7.50, balcony_z + 0.12),
                                     (px, -7.50, balcony_z + 0.78), 0.018, dark, 8)

    # Shopfront: recessed glazing, stone portal, doors and timber soffit.
    cube("Shopfront deep recess", (0, -6.62, 1.78), (12.7, 0.18, 2.75), dark, 0.025)
    cube("Shopfront glazing", (0, -6.76, 1.78), (11.9, 0.06, 2.52), glass, 0.012)
    for x in (-5.85, -3.9, -1.95, 0, 1.95, 3.9, 5.85):
        cube("Shopfront mullion", (x, -6.83, 1.78), (0.065, 0.10, 2.55), dark, 0.01)
    # Offset entrance and pull handles give the shopfront a human scale.
    cube("Entrance door", (4.85, -6.88, 1.52), (1.25, 0.07, 2.15), glass_lit, 0.018)
    cube("Door pull handle", (5.30, -6.96, 1.55), (0.045, 0.06, 0.62), dark, 0.012)
    cube("Shop fascia", (0, -6.78, 3.12), (13.0, 0.34, 0.62), signmat, 0.025)
    cube("Timber canopy soffit", (0, -7.30, 2.76), (13.3, 1.25, 0.12), wood, 0.025)
    cube("Awning valance", (0, -7.90, 3.03), (13.3, 0.12, 0.32), canvas, 0.025)
    for x in (-6.4, -3.2, 0, 3.2, 6.4):
        cube("Awning support bracket", (x, -7.32, 2.98), (0.07, 0.85, 0.07), dark, 0.012)

    # Rainwater goods, service conduit, rooftop equipment and restrained grime-catching ledges.
    for x in (-8.72, 8.72):
        cylinder_between("Rainwater downpipe", (x, -6.83, 0.35), (x, -6.83, 15.4), 0.075, dark, 12)
        for z in (1.0, 5.0, 9.0, 13.0):
            cube("Downpipe fixing strap", (x, -6.90, z), (0.22, 0.10, 0.07), dark, 0.01)
    cube("Roof service plinth", (5.8, 1.8, 16.65), (3.4, 3.0, 0.45), concrete, 0.06)
    cube("Rooftop HVAC unit", (5.8, 1.8, 17.35), (2.5, 1.8, 1.0), concrete, 0.08)
    for x in (4.85, 5.45, 6.05, 6.65):
        cylinder_between("HVAC grille", (x, 0.86, 17.1), (x, 0.86, 17.85), 0.045, dark, 10)

    # Side elevation articulation, so the asset does not read as a flat billboard.
    for z in (3.5, 7.0, 10.3, 13.5):
        cube("Side elevation string course", (9.06, 0.0, z), (0.18, 12.8, 0.12), pale_stone, 0.02)
    for y in (-3.8, 0.0, 3.8):
        for z in (5.4, 8.7, 12.0):
            cube("Side elevation window reveal", (9.08, y, z), (0.12, 1.5, 2.0), stone, 0.02)
            cube("Side elevation glazing", (9.16, y, z), (0.05, 1.2, 1.7), glass, 0.012)

    # Apply bevel/normal modifiers, then merge geometry by material.
    # This turns hundreds of tiny Blender objects into a handful of draw calls,
    # which matters on mobile GPUs when several buildings share the scene.
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    for obj in mesh_objects:
        bpy.context.view_layer.objects.active = obj
        for modifier in list(obj.modifiers):
            bpy.ops.object.modifier_apply(modifier=modifier.name)

    for material in list(bpy.data.materials):
        group = [obj for obj in bpy.context.scene.objects
                 if obj.type == "MESH" and any(slot.name == material.name for slot in obj.data.materials)]
        if len(group) > 1:
            bpy.ops.object.select_all(action="DESELECT")
            for obj in group:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = group[0]
            bpy.ops.object.join()
            group[0].name = "Merged geometry - " + material.name

    # Origin at ground centre for predictable placement in PlayCanvas.
    bpy.ops.object.select_all(action="SELECT")
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    for obj in bpy.context.selected_objects:
        obj.select_set(True)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(out), export_format="GLB",
                              use_selection=True, export_apply=True)
    print("CENTS_DISTRICT01_BUILDING_OK", out)


if __name__ == "__main__":
    main()
