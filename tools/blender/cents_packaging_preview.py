"""Studio render for inspecting CENTS' authored retail packaging at product scale."""
import argparse
import math
import os
import sys
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from cents_packaging import (
    _solid, _artwork, _can, _soda_bottle, _ketchup, _carton,
    _pillow_pack, _deli_tub, _bevel_box
)


def arguments():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def main():
    options = arguments()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    metal = _solid("Studio brushed aluminum", (0.53, 0.56, 0.53), 0.24, 0.82)
    dark_metal = _solid("Studio dark metal", (0.07, 0.09, 0.09), 0.3, 0.6)
    plastic = _solid("Studio PET plastic", (0.2, 0.28, 0.26), 0.24)
    red_cap = _solid("Studio ketchup red cap", (0.52, 0.04, 0.025), 0.28)
    orange_cap = _solid("Studio citrus orange cap", (0.95, 0.32, 0.035), 0.3)
    carton_side = _solid("Studio carton board", (0.88, 0.83, 0.70), 0.7)
    foil = _solid("Studio foil seams", (0.65, 0.61, 0.52), 0.3, 0.2)
    deli_lid = _solid("Studio deli lid", (0.88, 0.84, 0.73), 0.28)
    deli_cup = _solid("Studio deli cup", (0.91, 0.86, 0.74), 0.42)

    art = {
        "can": _artwork("EMBER COLA", "EMBER", "COLA  /  ORIGINAL", ((139,39,29),(45,24,22),(247,215,167),(226,111,42))),
        "soda": _artwork("SUNBURST", "CITRUS", "REAL FRUIT  /  FIZZ", ((228,135,32),(88,48,20),(255,235,184),(193,65,26))),
        "ketchup": _artwork("RED LABEL", "TOMATO", "SLOW SIMMERED", ((162,35,32),(65,22,20),(250,218,184),(224,153,50))),
        "milk": _artwork("MEADOW HOUSE", "WHOLE MILK", "FARM FRESH  /  1 QT", ((42,93,105),(18,48,55),(246,235,204),(207,160,84))),
        "chips": _artwork("CRISP CLUB", "KETTLE", "SEA SALT  /  POTATO", ((186,119,42),(66,45,24),(255,225,162),(151,53,31))),
        "bar": _artwork("NOCTURNE", "DARK BAR", "COCOA  /  72 PERCENT", ((57,43,48),(24,23,29),(240,208,151),(174,105,64))),
        "deli": _artwork("DELI FRESH", "PASTA SALAD", "PREPARED TODAY", ((80,111,78),(31,54,37),(247,231,198),(200,138,63))),
    }

    # A continuous, warm timber display ledge gives the products a neutral retail context.
    shelf = _solid("Studio warm oak shelf", (0.23,0.12,0.065), 0.52)
    backdrop = _solid("Studio deep evergreen backdrop", (0.055,0.105,0.095), 0.8)
    _bevel_box("Display ledge", (0.42,6.5,0.22), (0,0,-0.14), shelf, 0.0, 1.0, [], 0.035)
    bpy.ops.mesh.primitive_plane_add(size=20, location=(-0.65,0,0.0))
    wall = bpy.context.object
    wall.name = "Studio backdrop"
    wall.rotation_euler[1] = math.pi / 2
    wall.data.materials.append(backdrop)

    scale = 2.0
    positions = [-2.25,-1.50,-0.75,0.0,0.75,1.50,2.25]
    parts = []
    _can((0,positions[0],0.0),0.0,scale,art["can"],metal,dark_metal,parts)
    _soda_bottle((0,positions[1],0.0),0.0,scale,art["soda"],orange_cap,plastic,parts)
    _ketchup((0,positions[2],0.0),0.0,scale,art["ketchup"],red_cap,plastic,parts)
    _carton((0,positions[3],0.0),0.0,scale,art["milk"],carton_side,orange_cap,parts)
    _pillow_pack((0,positions[4],0.0),0.0,scale,art["chips"],foil,parts,height=0.34,width=0.19,depth=0.055,name="Kettle chip stand pouch")
    _pillow_pack((0,positions[5],0.0),0.0,scale,art["bar"],foil,parts,height=0.15,width=0.22,depth=0.035,name="Chocolate foil pillow pack")
    _deli_tub((0,positions[6],0.0),0.0,scale,art["deli"],deli_lid,deli_cup,parts)

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 36
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = os.path.abspath(options.output)
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"

    world = bpy.data.worlds.new("CENTS packaging studio") if not scene.world else scene.world
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.16,0.19,0.17,1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35

    target = (0,0,0.46)
    bpy.ops.object.camera_add(location=(5.2,-0.10,2.15))
    camera = bpy.context.object
    camera.name = "Packaging hero camera"
    camera.rotation_euler = (mathutils.Vector(target) - camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.lens = 54
    scene.camera = camera

    for name, location, energy, size in (
        ("Large warm key", (4.2,-3.5,5.2), 950, 4.0),
        ("Soft frontal fill", (3.4,4.0,3.0), 650, 3.2),
        ("Amber rim", (-1.2,0.0,4.2), 800, 3.0),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.rotation_euler = (mathutils.Vector(target) - light.location).to_track_quat("-Z","Y").to_euler()

    bpy.ops.render.render(write_still=True)
    print("CENTS packaging studio render:", os.path.abspath(options.output))


if __name__ == "__main__":
    import mathutils
    main()
