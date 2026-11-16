"""Generate a controlled CENTS material-identity study as an export-ready GLB.

Each sample uses the exact same UV-sphere mesh. Only its material family changes.
Texture maps are generated from distinct material-specific algorithms (not one
shared noise graph), packed into the GLB, and ready for PlayCanvas/glTF PBR.

Run:
  blender --background --python tools/blender/cents_material_identity_study.py -- --output /tmp/cents-material-study.glb
"""
import argparse
import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)


def arguments():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--size", type=int, default=384)
    parser.add_argument("--seed", type=int, default=4107)
    return parser.parse_args(argv)


from cents_materials import material_family


def add_label(text, x, y, material):
    curve = bpy.data.curves.new("CENTS material label", type="FONT")
    curve.body = text
    curve.align_x = "CENTER"
    curve.size = 0.25
    curve.extrude = 0.003
    obj = bpy.data.objects.new("Label · " + text, curve)
    bpy.context.collection.objects.link(obj)
    obj.location = (x, y, 0.035)
    obj.rotation_euler = (math.radians(90), 0, 0)
    curve.materials.append(material)
    return obj


def main():
    args = arguments()
    size = max(128, min(1024, args.size))
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    label_material = bpy.data.materials.new("CENTS · label ink")
    label_material.diffuse_color = (0.10, 0.11, 0.11, 1)
    label_material.use_nodes = True
    label_material.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.10, 0.11, 0.11, 1)
    label_material.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value = 0.8

    pedestal_material = bpy.data.materials.new("CENTS · neutral sample plinth")
    pedestal_material.diffuse_color = (0.23, 0.24, 0.23, 1)
    pedestal_material.use_nodes = True
    pedestal_bsdf = pedestal_material.node_tree.nodes.get("Principled BSDF")
    pedestal_bsdf.inputs["Base Color"].default_value = (0.23, 0.24, 0.23, 1)
    pedestal_bsdf.inputs["Roughness"].default_value = 0.72

    samples = [
        ("STONE", "stone", (0.48, 0.405, 0.315), 0.88, 0.0),
        ("LIME PLASTER", "plaster", (0.67, 0.565, 0.445), 0.92, 0.0),
        ("TIMBER", "wood", (0.31, 0.165, 0.072), 0.64, 0.0),
        ("BRUSHED METAL", "metal", (0.25, 0.285, 0.285), 0.34, 0.72),
        ("CONCRETE", "concrete", (0.47, 0.475, 0.445), 0.91, 0.0),
        ("ASPHALT", "asphalt", (0.125, 0.145, 0.15), 0.96, 0.0),
    ]

    for index, (label, family, base, roughness, metallic) in enumerate(samples):
        row, col = divmod(index, 3)
        x = (col - 1) * 4.7
        y = (0.5 - row) * 4.3
        material = material_family(label, family, base, roughness, metallic, size, args.seed + index * 17)

        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=40, radius=1.18, location=(x, y, 1.58))
        sphere = bpy.context.object
        sphere.name = "Identical sample sphere · " + label
        sphere.data.materials.append(material)
        for polygon in sphere.data.polygons:
            polygon.use_smooth = True

        bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=1.42, depth=0.36, location=(x, y, 0.18))
        plinth = bpy.context.object
        plinth.name = "Neutral plinth · " + label
        plinth.data.materials.append(pedestal_material)
        bevel = plinth.modifiers.new("Plinth edge softness", "BEVEL")
        bevel.width = 0.045
        bevel.segments = 3
        plinth.modifiers.new("Plinth weighted normals", "WEIGHTED_NORMAL")

        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y - 1.38, 0.10))
        plaque = bpy.context.object
        plaque.name = "Material name plate · " + label
        plaque.dimensions = (2.45, 0.16, 0.28)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        plaque.data.materials.append(pedestal_material)
        add_label(label, x, y - 1.475, label_material)

    # Export only the generated study. All image textures are packed, so the GLB
    # is self-contained and does not depend on loose files or Blender node graphs.
    bpy.ops.object.select_all(action="SELECT")
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=os.path.abspath(args.output),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
    )
    print("CENTS_MATERIAL_IDENTITY_STUDY_OK", args.output, "materials=", len(samples), "texture_size=", size)


if __name__ == "__main__":
    main()
