"""Generate a disposable architectural GLB to verify the remote Blender pipeline.

This is infrastructure validation, not the approved visual style or a production asset.
The first successful run proves Blender can execute remotely and export GLB.
Run with:
  blender --background --python tools/blender/pipeline_smoke_test.py -- --output /tmp/cents-test.glb
"""
import argparse
import os
import sys

import bpy
from mathutils import Vector


def arguments():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def material(name, color, roughness=0.72, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def cube(name, location, scale, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new("Small edge radii", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
        obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
    return obj


def main():
    args = arguments()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    plaster = material("Warm mineral plaster", (0.66, 0.58, 0.46))
    concrete = material("Pale concrete", (0.39, 0.40, 0.38))
    glass = material("Shopfront glass", (0.075, 0.16, 0.19), 0.18, 0.25)
    dark_metal = material("Dark bronze metal", (0.075, 0.085, 0.08), 0.34, 0.72)
    wood = material("Timber soffit", (0.30, 0.17, 0.085), 0.55)

    # Two-storey commercial test facade. Dimensions are deliberately compact.
    cube("Main building mass", (0, 0, 3.2), (10, 7, 6.4), plaster, 0.08)
    cube("Ground-floor plinth", (0, -3.56, 0.48), (10.05, 0.18, 0.96), concrete, 0.025)
    cube("Upper-floor band", (0, -3.60, 3.45), (10.15, 0.22, 0.22), concrete, 0.025)
    cube("Parapet coping", (0, -3.58, 6.38), (10.2, 0.24, 0.16), concrete, 0.025)

    # Shopfront glazing, divided by metal mullions.
    cube("Recessed shopfront", (0, -3.54, 1.72), (7.0, 0.08, 2.35), glass, 0.015)
    for x in (-3.55, -1.8, 0, 1.8, 3.55):
        cube("Shopfront mullion", (x, -3.62, 1.72), (0.055, 0.10, 2.42), dark_metal, 0.012)
    cube("Shopfront transom", (0, -3.62, 2.48), (7.1, 0.10, 0.055), dark_metal, 0.012)

    # Repeated upper-floor windows with deep reveals and projecting sills.
    for x in (-3.55, -1.2, 1.2, 3.55):
        cube("Upper window dark reveal", (x, -3.57, 4.85), (1.48, 0.10, 1.42), dark_metal, 0.025)
        cube("Upper window glazing", (x, -3.64, 4.85), (1.28, 0.035, 1.20), glass, 0.012)
        cube("Window sill", (x, -3.72, 4.10), (1.62, 0.30, 0.10), concrete, 0.025)
        cube("Window head", (x, -3.68, 5.60), (1.62, 0.18, 0.10), concrete, 0.02)

    # Entrance portal and shallow canopy with a timber underside.
    cube("Entrance shadow recess", (0, -3.59, 1.55), (1.5, 0.09, 2.45), dark_metal, 0.02)
    cube("Entrance door glass", (0, -3.66, 1.55), (1.22, 0.04, 2.20), glass, 0.015)
    cube("Canopy fascia", (0, -4.05, 2.92), (2.5, 0.95, 0.16), dark_metal, 0.035)
    cube("Canopy timber underside", (0, -4.05, 2.825), (2.38, 0.82, 0.035), wood, 0.01)

    # Simple roof equipment to ensure the export includes varied geometry.
    cube("Roof plant enclosure", (3.2, 0.8, 6.72), (1.6, 1.2, 0.55), concrete, 0.04)
    cube("Roof equipment cap", (3.2, 0.8, 7.02), (1.72, 1.3, 0.08), dark_metal, 0.02)

    # Export with Y-up conversion handled by glTF exporter.
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(args.output), export_format="GLB", use_selection=True)
    print("CENTS_BLENDER_SMOKE_TEST_OK", args.output)


if __name__ == "__main__":
    main()

# Public-runner pipeline verification trigger.
