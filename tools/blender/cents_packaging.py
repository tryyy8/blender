"""Authored convenience-store packaging: custom meshes plus UV-mapped package artwork."""
import math
import bpy
import numpy as np


FONT = {
    "A": ("01110","10001","10001","11111","10001","10001","10001"),
    "B": ("11110","10001","10001","11110","10001","10001","11110"),
    "C": ("01111","10000","10000","10000","10000","10000","01111"),
    "D": ("11110","10001","10001","10001","10001","10001","11110"),
    "E": ("11111","10000","10000","11110","10000","10000","11111"),
    "F": ("11111","10000","10000","11110","10000","10000","10000"),
    "G": ("01111","10000","10000","10111","10001","10001","01111"),
    "H": ("10001","10001","10001","11111","10001","10001","10001"),
    "I": ("11111","00100","00100","00100","00100","00100","11111"),
    "J": ("00111","00010","00010","00010","10010","10010","01100"),
    "K": ("10001","10010","10100","11000","10100","10010","10001"),
    "L": ("10000","10000","10000","10000","10000","10000","11111"),
    "M": ("10001","11011","10101","10101","10001","10001","10001"),
    "N": ("10001","11001","10101","10011","10001","10001","10001"),
    "O": ("01110","10001","10001","10001","10001","10001","01110"),
    "P": ("11110","10001","10001","11110","10000","10000","10000"),
    "Q": ("01110","10001","10001","10001","10101","10010","01101"),
    "R": ("11110","10001","10001","11110","10100","10010","10001"),
    "S": ("01111","10000","10000","01110","00001","00001","11110"),
    "T": ("11111","00100","00100","00100","00100","00100","00100"),
    "U": ("10001","10001","10001","10001","10001","10001","01110"),
    "V": ("10001","10001","10001","10001","10001","01010","00100"),
    "W": ("10001","10001","10001","10101","10101","10101","01010"),
    "X": ("10001","10001","01010","00100","01010","10001","10001"),
    "Y": ("10001","10001","01010","00100","00100","00100","00100"),
    "Z": ("11111","00001","00010","00100","01000","10000","11111"),
    "0": ("01110","10001","10011","10101","11001","10001","01110"),
    "1": ("00100","01100","00100","00100","00100","00100","01110"),
    "2": ("01110","10001","00001","00010","00100","01000","11111"),
    "3": ("11110","00001","00001","01110","00001","00001","11110"),
    "4": ("00010","00110","01010","10010","11111","00010","00010"),
    "5": ("11111","10000","10000","11110","00001","00001","11110"),
    "6": ("01110","10000","10000","11110","10001","10001","01110"),
    "7": ("11111","00001","00010","00100","01000","01000","01000"),
    "8": ("01110","10001","10001","01110","10001","10001","01110"),
    "9": ("01110","10001","10001","01111","00001","00001","01110"),
    "-": ("00000","00000","00000","11111","00000","00000","00000"),
    ".": ("00000","00000","00000","00000","00000","00110","00110"),
    "'": ("00100","00100","00010","00000","00000","00000","00000"),
    "&": ("01100","10010","10100","01000","10101","10010","01101"),
    " ": ("00000","00000","00000","00000","00000","00000","00000"),
}


def _rect(image, x, y, width, height, color):
    h, w, _ = image.shape
    x0, x1 = max(0, int(x)), min(w, int(x + width))
    y0, y1 = max(0, int(y)), min(h, int(y + height))
    if x1 > x0 and y1 > y0:
        image[y0:y1, x0:x1] = color


def _circle(image, cx, cy, radius, color, outline=None, thickness=1):
    h, w, _ = image.shape
    x0, x1 = max(0, int(cx - radius - thickness)), min(w, int(cx + radius + thickness + 1))
    y0, y1 = max(0, int(cy - radius - thickness)), min(h, int(cy + radius + thickness + 1))
    yy, xx = np.ogrid[y0:y1, x0:x1]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    if outline is None:
        mask = dist <= radius
        image[y0:y1, x0:x1][mask] = color
    else:
        mask = (dist <= radius) & (dist >= radius - thickness)
        image[y0:y1, x0:x1][mask] = outline


def _polygon(image, points, color):
    h, w, _ = image.shape
    min_x = max(0, int(min(p[0] for p in points)))
    max_x = min(w, int(max(p[0] for p in points)) + 1)
    min_y = max(0, int(min(p[1] for p in points)))
    max_y = min(h, int(max(p[1] for p in points)) + 1)
    if max_x <= min_x or max_y <= min_y:
        return
    yy, xx = np.mgrid[min_y:max_y, min_x:max_x]
    inside = np.zeros(xx.shape, dtype=bool)
    j = len(points) - 1
    for i in range(len(points)):
        xi, yi = points[i]
        xj, yj = points[j]
        crosses = ((yi > yy) != (yj > yy)) & (
            xx < (xj - xi) * (yy - yi) / ((yj - yi) + 1e-9) + xi
        )
        inside ^= crosses
        j = i
    image[min_y:max_y, min_x:max_x][inside] = color


def _text(image, x, y, value, scale, color):
    cursor = int(x)
    for char in value.upper():
        glyph = FONT.get(char, FONT[" "])
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit == "1":
                    _rect(image, cursor + col * scale, y + row * scale, scale, scale, color)
        cursor += 6 * scale


def _artwork(name, title, subtitle, palette):
    size = 512
    base, dark, light, accent = palette
    yy, xx = np.mgrid[0:size, 0:size]
    gradient = 0.90 + 0.10 * (1.0 - yy / size) + 0.025 * np.sin(xx / 19.0 + yy / 31.0)
    image = np.empty((size, size, 3), dtype=np.uint8)
    for channel in range(3):
        image[..., channel] = np.clip(base[channel] * gradient, 0, 255).astype(np.uint8)

    # A clean hierarchy with restrained side rails keeps every product name readable.
    _rect(image, 0, 0, size, 42, dark)
    _rect(image, 0, 470, size, 42, dark)
    _rect(image, 25, 60, 462, 390, light)
    _rect(image, 25, 60, 462, 13, accent)
    _rect(image, 25, 437, 462, 13, accent)
    _rect(image, 25, 73, 9, 364, accent)
    _rect(image, 478, 73, 9, 364, dark)

    # A compact seal sits in the left margin instead of colliding with the wordmark.
    _circle(image, 64, 160, 24, accent)
    _circle(image, 64, 160, 18, light)
    _circle(image, 64, 160, 12, accent)
    if "SUNBURST" in name:
        for spoke in range(8):
            theta = spoke * math.pi / 4
            x0 = 64 + int(math.cos(theta) * 15)
            y0 = 160 + int(math.sin(theta) * 15)
            x1 = 64 + int(math.cos(theta) * 21)
            y1 = 160 + int(math.sin(theta) * 21)
            _rect(image, min(x0,x1), min(y0,y1), max(2,abs(x1-x0)+1), max(2,abs(y1-y0)+1), dark)
    elif "MEADOW" in name:
        _polygon(image, [(43,169),(56,148),(68,165),(78,151),(88,169)], dark)
        _rect(image, 43, 170, 45, 3, accent)
    elif "RED LABEL" in name:
        _polygon(image, [(54,143),(61,133),(64,147),(74,134),(75,146),(85,142),(77,154),(59,154)], dark)
    elif "DELI" in name:
        _polygon(image, [(48,174),(57,151),(68,160),(82,145),(78,171),(64,182)], dark)
        _rect(image, 64, 159, 2, 21, light)
    elif "NOCTURNE" in name:
        _polygon(image, [(49,160),(57,143),(74,140),(83,157),(75,176),(58,178)], dark)
        _rect(image, 64, 145, 2, 31, light)
    elif "CRISP" in name:
        for dot in ((57,151),(70,153),(61,166),(74,168)):
            _circle(image, dot[0], dot[1], 2, dark)
    else:
        _polygon(image, [(51,174),(54,157),(64,140),(73,153),(77,168),(65,181)], dark)

    brand = name.upper()
    brand_scale = 3 if len(brand) > 9 else 4
    _text(image, (size - len(brand) * 6 * brand_scale) // 2, 94, brand, brand_scale, dark)

    title_scale = 6 if len(title) <= 8 else 5
    title_width = len(title) * 6 * title_scale
    _text(image, (size - title_width) // 2, 194, title, title_scale, dark)
    sub_scale = 4
    _text(image, (size - len(subtitle) * 6 * sub_scale) // 2, 266, subtitle, sub_scale, accent)

    # Fine rules and small-print details finish the printed panel without obscuring its name.
    _rect(image, 112, 326, 288, 3, dark)
    _rect(image, 132, 342, 248, 2, accent)
    _text(image, 118, 365, "SMALL BATCH  QUALITY GOODS", 2, dark)
    _text(image, 152, 484, "CENTS  /  MARKET GOODS", 2, light)
    for offset in range(4):
        _rect(image, 48, 292 + offset * 8, 22 + offset * 5, 2, dark)
        _rect(image, 435, 145 + offset * 8, 22 + offset * 5, 2, accent)
    image = image[::-1].copy()  # Blender image pixels are stored bottom row first.

    datablock = bpy.data.images.new("CENTS Package Art - " + name, width=size, height=size, alpha=False)
    rgba = np.empty((size, size, 4), dtype=np.float32)
    rgba[..., :3] = image.astype(np.float32) / 255.0
    rgba[..., 3] = 1.0
    datablock.pixels.foreach_set(rgba.reshape(-1))
    datablock.pack()

    material = bpy.data.materials.new("CENTS Printed Packaging - " + name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.32 if "CAN" in name else 0.48
    bsdf.inputs["Metallic"].default_value = 0.38 if "CAN" in name else (0.16 if "FOIL" in name else 0.0)
    texture = nodes.new("ShaderNodeTexImage")
    texture.name = "Full-wrap authored package artwork"
    texture.image = datablock
    texture.interpolation = "Linear"
    texture.extension = "REPEAT"
    links.new(texture.outputs["Color"], bsdf.inputs["Base Color"])
    return material


def _solid(name, color, roughness=0.5, metallic=0.0):
    material = bpy.data.materials.new("CENTS " + name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return material


def _consolidate_product(parts, start, label):
    """Join every modeled component of one SKU into a single export object."""
    members = [obj for obj in parts[start:] if obj and obj.name in bpy.data.objects]
    if not members:
        raise RuntimeError("Product generator emitted no geometry: " + label)
    if len(members) > 1:
        bpy.ops.object.select_all(action="DESELECT")
        for obj in members:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = members[0]
        bpy.ops.object.join()
    product = bpy.context.view_layer.objects.active
    product.name = "CENTS SKU - " + label
    product.data.name = product.name + " mesh"
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts[start:] = [product]
    return product


def _emit_product(parts, builder, label, *args, **kwargs):
    start = len(parts)
    builder(*args, parts=parts, **kwargs)
    return _consolidate_product(parts, start, label)


def _finish(obj, origin, angle, scale, parts):
    obj.location = origin
    obj.rotation_euler[2] = angle
    obj.scale = (scale, scale, scale)
    parts.append(obj)
    return obj


def _mesh_object(name, vertices, faces, material, uv_by_vertex=None, smooth=False):
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if uv_by_vertex is not None:
        layer = mesh.uv_layers.new(name="Package UV")
        for polygon in mesh.polygons:
            polygon.use_smooth = smooth
            for loop_index, vertex_index in zip(polygon.loop_indices, polygon.vertices):
                layer.data[loop_index].uv = uv_by_vertex[vertex_index]
    elif smooth:
        for polygon in mesh.polygons:
            polygon.use_smooth = True
    return obj


def _lathe(name, profile, material, origin, angle, scale, parts, sides=40):
    vertices, faces, uvs = [], [], []
    max_z = max(p[0] for p in profile)
    for z, rx, ry in profile:
        for side in range(sides + 1):
            u = side / sides
            theta = 2.0 * math.pi * (u - 0.5)
            vertices.append((rx * math.cos(theta), ry * math.sin(theta), z))
            uvs.append((u, z / max_z if max_z else 0.0))
    for ring in range(len(profile) - 1):
        for side in range(sides):
            a = ring * (sides + 1) + side
            b = a + 1
            c = b + sides + 1
            d = a + sides + 1
            faces.append((a, b, c, d))
    side_face_count = len(faces)
    faces.append(tuple(range(sides - 1, -1, -1)))
    top_start = (len(profile) - 1) * (sides + 1)
    faces.append(tuple(top_start + side for side in range(sides)))
    obj = _mesh_object(name, vertices, faces, material, uvs, smooth=True)
    for polygon in obj.data.polygons:
        polygon.use_smooth = polygon.index < side_face_count
    return _finish(obj, origin, angle, scale, parts)


def _cylinder(name, radius, depth, material, z, origin, angle, scale, parts, sides=32, bevel=0.0):
    profile = ((z - depth / 2, radius, radius), (z + depth / 2, radius, radius))
    obj = _lathe(name, profile, material, origin, angle, scale, parts, sides=sides)
    if bevel > 0:
        modifier = obj.modifiers.new("Machined edge radius", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
        obj.modifiers.new("Weighted face normals", "WEIGHTED_NORMAL")
    # Close both ends with the same finish; top discs are modeled as separate shallow caps.
    return obj


def _torus(name, major, minor, z, material, origin, angle, scale, parts, major_steps=40, minor_steps=10):
    vertices, faces = [], []
    for a in range(major_steps):
        theta = 2.0 * math.pi * a / major_steps
        for b in range(minor_steps):
            phi = 2.0 * math.pi * b / minor_steps
            r = major + minor * math.cos(phi)
            vertices.append((r * math.cos(theta), r * math.sin(theta), z + minor * math.sin(phi)))
    for a in range(major_steps):
        for b in range(minor_steps):
            a0 = a * minor_steps + b
            a1 = a * minor_steps + (b + 1) % minor_steps
            b0 = ((a + 1) % major_steps) * minor_steps + b
            b1 = ((a + 1) % major_steps) * minor_steps + (b + 1) % minor_steps
            faces.append((a0, b0, b1, a1))
    obj = _mesh_object(name, vertices, faces, material, smooth=True)
    return _finish(obj, origin, angle, scale, parts)


def _bevel_box(
    name, dimensions, location, material, angle, scale, parts,
    bevel=0.008, product_origin=(0.0, 0.0, 0.0)
):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    mod = obj.modifiers.new("Soft folded package edge", "BEVEL")
    mod.width = bevel
    mod.segments = 3
    obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")

    # These coordinates describe details in the product's local frame. Convert
    # their position through the same yaw and scale as the main package body.
    local_x, local_y, local_z = location
    ox, oy, oz = product_origin
    c, s = math.cos(angle), math.sin(angle)
    world_location = (
        ox + scale * (local_x * c - local_y * s),
        oy + scale * (local_x * s + local_y * c),
        oz + scale * local_z
    )
    return _finish(obj, world_location, angle, scale, parts)


def _can(origin, angle, scale, art, metal, ink, parts):
    profile = (
        (0.008, 0.057, 0.057), (0.014, 0.064, 0.064),
        (0.024, 0.067, 0.067), (0.275, 0.067, 0.067),
        (0.288, 0.063, 0.063), (0.296, 0.057, 0.057)
    )
    _lathe("330 ml formed aluminum can", profile, art, origin, angle, scale, parts, 48)
    _cylinder("Can recessed base", 0.067, 0.010, metal, 0.006, origin, angle, scale, parts, 48, 0.002)
    _torus("Can lower rolled seam", 0.062, 0.004, 0.018, metal, origin, angle, scale, parts)
    _cylinder("Can lid", 0.057, 0.006, metal, 0.298, origin, angle, scale, parts, 40)
    _torus("Can top rolled rim", 0.057, 0.004, 0.296, metal, origin, angle, scale, parts)
    _torus("Can top countersink ring", 0.039, 0.0018, 0.302, ink, origin, angle, scale, parts)
    _bevel_box("Embossed pull tab", (0.022, 0.038, 0.003), (0.008, -0.004, 0.306), metal, angle, scale, parts, 0.006, product_origin=origin)
    _cylinder("Pull tab rivet", 0.005, 0.003, ink, 0.307, origin, angle, scale, parts, 16)


def _soda_bottle(origin, angle, scale, art, cap, plastic, parts):
    profile = (
        (0.006, 0.045, 0.052), (0.018, 0.060, 0.067),
        (0.050, 0.067, 0.074), (0.205, 0.067, 0.074),
        (0.245, 0.063, 0.070), (0.275, 0.047, 0.055),
        (0.294, 0.033, 0.039), (0.337, 0.033, 0.039),
        (0.345, 0.030, 0.036)
    )
    _lathe("PET bottle with sloped shoulder", profile, art, origin, angle, scale, parts, 48)
    _cylinder("Bottle molded bottom closure", 0.058, 0.012, plastic, 0.008, origin, angle, scale, parts, 48, 0.003)
    _torus("Bottle heel bead", 0.047, 0.003, 0.018, plastic, origin, angle, scale, parts)
    _torus("Bottle neck support ring", 0.034, 0.003, 0.333, plastic, origin, angle, scale, parts)
    _cylinder("Bottle tamper band", 0.034, 0.016, cap, 0.344, origin, angle, scale, parts, 32, 0.002)
    _cylinder("Ribbed screw cap", 0.035, 0.034, cap, 0.365, origin, angle, scale, parts, 32, 0.003)
    _torus("Cap top lip", 0.032, 0.003, 0.382, cap, origin, angle, scale, parts)


def _ketchup(origin, angle, scale, art, cap, plastic, parts):
    # Inverted squeeze bottle: molded heel and broad shoulders taper into the base closure.
    profile = (
        (0.025, 0.036, 0.040), (0.050, 0.040, 0.044),
        (0.073, 0.060, 0.066), (0.115, 0.071, 0.078),
        (0.255, 0.073, 0.080), (0.292, 0.066, 0.073),
        (0.322, 0.047, 0.056), (0.345, 0.020, 0.027),
        (0.350, 0.006, 0.008)
    )
    _lathe("Tomato sauce contoured squeeze bottle", profile, art, origin, angle, scale, parts, 44)
    _torus("Bottle shoulder molded bead", 0.064, 0.0025, 0.287, plastic, origin, angle, scale, parts)
    _cylinder("Flip-top cap collar", 0.041, 0.025, cap, 0.014, origin, angle, scale, parts, 32, 0.003)
    _cylinder("Flip-top base", 0.046, 0.018, cap, 0.006, origin, angle, scale, parts, 32, 0.003)
    for rib in range(18):
        theta = 2.0 * math.pi * rib / 18
        point = (0.041 * math.cos(theta), 0.041 * math.sin(theta), 0.015)
        _bevel_box("Flip cap grip flute", (0.004, 0.007, 0.020), point, plastic, angle, scale, parts, 0.0015, product_origin=origin)
    _bevel_box("Flip cap hinge", (0.022, 0.018, 0.008), (0.0, -0.036, 0.015), cap, angle, scale, parts, 0.003, product_origin=origin)


def _carton(origin, angle, scale, art, side_mat, cap, parts):
    depth, width, base_z, shoulder_z, peak_z = 0.148, 0.158, 0.012, 0.252, 0.330
    front = [
        (depth / 2, -width / 2, base_z),
        (depth / 2, width / 2, base_z),
        (depth / 2, width / 2, shoulder_z),
        (depth / 2, 0.0, peak_z),
        (depth / 2, -width / 2, shoulder_z)
    ]
    back = [(-depth / 2, y, z) for _, y, z in front]
    for name, points, reverse in (("Carton printed front panel", front, False), ("Carton printed rear panel", back, True)):
        face = tuple(reversed(range(len(points)))) if reverse else tuple(range(len(points)))
        uvs = [(i, (y / width) + 0.5) for i, (_, y, _) in enumerate(points)]
        # The front artwork's horizontal coordinate follows package width; vertical follows height.
        uv_map = {}
        for i, (_, y, z) in enumerate(points):
            uv_map[i] = ((y / width) + 0.5, (z - base_z) / (peak_z - base_z))
        obj = _mesh_object(name, points, [face], art, uv_map, smooth=False)
        _finish(obj, origin, angle, scale, parts)

    # Side walls and the two folded gable roof planes are real shell geometry.
    side_vertices = [
        (-depth/2, -width/2, base_z), (depth/2, -width/2, base_z),
        (depth/2, -width/2, shoulder_z), (0, -width/2, peak_z),
        (-depth/2, -width/2, shoulder_z),
        (-depth/2, width/2, base_z), (depth/2, width/2, base_z),
        (depth/2, width/2, shoulder_z), (0, width/2, peak_z),
        (-depth/2, width/2, shoulder_z)
    ]
    side_faces = [(0,1,2,3,4), (5,9,8,7,6)]
    # The front and rear printed panels are separate UV meshes; only the folded
    # roof planes belong to this side-board mesh, avoiding coplanar overlap.
    side_faces += [(2,7,8,3), (4,3,8,9)]
    side_obj = _mesh_object("Carton folded side walls and gable", side_vertices, side_faces, side_mat, smooth=False)
    _finish(side_obj, origin, angle, scale, parts)
    _bevel_box("Gable fold seam", (0.152, 0.006, 0.007), (0, 0, 0.322), side_mat, angle, scale, parts, 0.002, product_origin=origin)
    _cylinder("Carton screw neck", 0.020, 0.018, cap, 0.320, origin, angle, scale, parts, 24, 0.002)
    _cylinder("Carton screw closure", 0.023, 0.025, cap, 0.337, origin, angle, scale, parts, 28, 0.003)
    _torus("Carton tamper ring", 0.021, 0.002, 0.326, side_mat, origin, angle, scale, parts)


def _pillow_pack(origin, angle, scale, art, foil, parts, height=0.34, width=0.19, depth=0.050, name="Stand-up snack pouch"):
    # Front and rear film panels bulge and wrinkle; the artwork is mapped directly to each surface.
    vertices, faces, uvs = [], [], []
    nx, nz = 12, 12
    for side in (1, -1):
        start = len(vertices)
        for iz in range(nz + 1):
            v = iz / nz
            for ix in range(nx + 1):
                u = ix / nx
                across = (u - 0.5) * width
                vertical = 0.022 + v * height
                shoulder = 1.0 - 0.18 * abs(2 * v - 1) ** 5
                edge_taper = 0.84 + 0.16 * math.sin(math.pi * u)
                wrinkles = 0.003 * math.sin(u * math.pi * 8 + v * 2.8) * math.sin(v * math.pi)
                bulge = depth * (0.28 + 0.72 * math.sin(math.pi * u) * math.sin(math.pi * v))
                x = side * (bulge + wrinkles)
                vertices.append((x, across * edge_taper, vertical * shoulder))
                uvs.append((u, v))
        for iz in range(nz):
            for ix in range(nx):
                a = start + iz * (nx + 1) + ix
                b = a + 1
                c = b + nx + 1
                d = a + nx + 1
                faces.append((a,b,c,d) if side == 1 else (d,c,b,a))
    # Close the two printed faces with real perimeter film instead of leaving
    # independent paper-thin sheets. Each edge is stitched into a continuous bag.
    front_start, back_start = 0, (nz + 1) * (nx + 1)
    for ix in range(nx):
        a, b = front_start + ix, front_start + ix + 1
        c, d = back_start + ix + 1, back_start + ix
        faces.append((a, b, c, d))
        a = front_start + nz * (nx + 1) + ix
        b = a + 1
        c = back_start + nz * (nx + 1) + ix + 1
        d = c - 1
        faces.append((d, c, b, a))
    for iz in range(nz):
        a = front_start + iz * (nx + 1)
        b = a + nx + 1
        c = back_start + (iz + 1) * (nx + 1)
        d = back_start + iz * (nx + 1)
        faces.append((a, b, c, d))
        a = front_start + iz * (nx + 1) + nx
        b = a + nx + 1
        c = back_start + (iz + 1) * (nx + 1) + nx
        d = back_start + iz * (nx + 1) + nx
        faces.append((d, c, b, a))
    obj = _mesh_object(name + " sealed printed film shell", vertices, faces, art, uvs, smooth=True)
    _finish(obj, origin, angle, scale, parts)

    # Heat-sealed crimp jaws follow the actual tapered shell boundary. The former
    # top seal sat above the pouch shoulder and the side welds sat outside the film,
    # which made the package look like disconnected floating strips.
    bottom_seal_z = 0.022 * 0.82
    top_seal_z = (0.022 + height) * 0.82
    for side in (-1, 1):
        seal_x = side * depth * 0.28
        for z in (bottom_seal_z, top_seal_z):
            _bevel_box(name + " ribbed heat seal", (0.018, width * 0.88, 0.022),
                       (seal_x, 0, z), foil, angle, scale, parts, 0.004, product_origin=origin)
            for rib in range(7):
                y = -width * 0.35 + rib * width * 0.116
                _bevel_box(name + " seal impression", (0.003, 0.003, 0.014),
                           (seal_x + side * 0.010, y, z), art, angle, scale, parts, 0.001, product_origin=origin)
    for side in (-1, 1):
        _bevel_box(name + " vertical fin seal", (0.014, 0.022, height * 0.80),
                   (0, side * width * 0.42, 0.022 + height * 0.50), foil, angle, scale, parts, 0.003, product_origin=origin)
    _bevel_box(name + " base gusset", (depth * 0.95, width * 0.84, 0.012),
               (0, 0, 0.018), foil, angle, scale, parts, 0.004, product_origin=origin)


def _deli_tub(origin, angle, scale, art, lid, cup, parts):
    profile = (
        (0.010, 0.052, 0.052), (0.018, 0.057, 0.057),
        (0.045, 0.061, 0.061), (0.175, 0.077, 0.077),
        (0.191, 0.079, 0.079)
    )
    _lathe("Tapered chilled deli cup with printed wrap", profile, art, origin, angle, scale, parts, 48)
    _cylinder("Deli cup sealed bottom", 0.055, 0.012, cup, 0.012, origin, angle, scale, parts, 48, 0.002)
    _torus("Cup foot bead", 0.054, 0.003, 0.018, cup, origin, angle, scale, parts)
    _torus("Snap lid lower locking lip", 0.078, 0.004, 0.191, lid, origin, angle, scale, parts)
    _cylinder("Deli cup snap lid", 0.078, 0.012, lid, 0.199, origin, angle, scale, parts, 40, 0.003)
    _torus("Deli lid raised rim", 0.071, 0.003, 0.207, lid, origin, angle, scale, parts)
    _bevel_box("Deli lid pull tab", (0.024, 0.020, 0.006), (0.055, 0, 0.210), lid, angle, scale, parts, 0.004, product_origin=origin)


def build_merchandise(size=256):
    metal = _solid("Brushed aluminum and closure metal", (0.48, 0.51, 0.49), 0.27, 0.78)
    dark_metal = _solid("Dark printed metal", (0.075, 0.095, 0.095), 0.32, 0.55)
    plastic = _solid("Molded PET and bottle plastic", (0.18, 0.27, 0.24), 0.24, 0.0)
    red_cap = _solid("Deep red molded cap", (0.48, 0.045, 0.035), 0.31, 0.0)
    orange_cap = _solid("Citrus orange closure", (0.93, 0.31, 0.045), 0.32, 0.0)
    carton_side = _solid("Milk carton board", (0.86, 0.81, 0.67), 0.72, 0.0)
    foil = _solid("Heat-sealed foil edge", (0.55, 0.53, 0.47), 0.34, 0.24)
    deli_lid = _solid("Deli tub lid polymer", (0.84, 0.80, 0.69), 0.30, 0.0)
    deli_cup = _solid("Deli tub molded base", (0.90, 0.85, 0.72), 0.46, 0.0)

    art = {
        "can": _artwork("EMBER COLA", "EMBER", "COLA  /  ORIGINAL", ((139, 39, 29), (45, 24, 22), (247, 215, 167), (226, 111, 42))),
        "soda": _artwork("SUNBURST", "CITRUS", "REAL FRUIT  /  FIZZ", ((228, 135, 32), (88, 48, 20), (255, 235, 184), (193, 65, 26))),
        "ketchup": _artwork("RED LABEL", "TOMATO", "SLOW SIMMERED", ((162, 35, 32), (65, 22, 20), (250, 218, 184), (224, 153, 50))),
        "milk": _artwork("MEADOW HOUSE", "WHOLE MILK", "FARM FRESH  /  1 QT", ((42, 93, 105), (18, 48, 55), (246, 235, 204), (207, 160, 84))),
        "chips": _artwork("CRISP CLUB", "KETTLE", "SEA SALT  /  POTATO", ((186, 119, 42), (66, 45, 24), (255, 225, 162), (151, 53, 31))),
        "bar": _artwork("NOCTURNE", "DARK BAR", "COCOA  /  72 PERCENT", ((57, 43, 48), (24, 23, 29), (240, 208, 151), (174, 105, 64))),
        "deli": _artwork("DELI FRESH", "PASTA SALAD", "PREPARED TODAY", ((80, 111, 78), (31, 54, 37), (247, 231, 198), (200, 138, 63))),
    }

    parts = []
    gondolas = (-2.35, 2.35)
    # Product bases sit just above the actual gondola shelf tops (0.4575, 0.9475, 1.4375).
    shelves = (0.462, 0.952, 1.442)
    for gondola_index, gx in enumerate(gondolas):
        for row, shelf_z in enumerate(shelves):
            for face in (-1, 1):
                for item in range(9):
                    y = -2.55 + item * 0.64
                    x = gx + face * 0.34
                    angle = 0.0 if face > 0 else math.pi
                    scale = (0.94, 1.0, 0.97, 1.03)[(item + row) % 4]
                    kind = (item + row * 2 + gondola_index * 3) % 7
                    origin = (x, y, shelf_z)
                    if kind == 0:
                        _emit_product(parts, _can, "EMBER COLA CAN", origin, angle, scale, art["can"], metal, dark_metal)
                    elif kind == 1:
                        _emit_product(parts, _soda_bottle, "SUNBURST PET BOTTLE", origin, angle, scale, art["soda"], orange_cap, plastic)
                    elif kind == 2:
                        _emit_product(parts, _ketchup, "RED LABEL SQUEEZE BOTTLE", origin, angle, scale, art["ketchup"], red_cap, plastic)
                    elif kind == 3:
                        _emit_product(parts, _carton, "MEADOW HOUSE CARTON", origin, angle, scale, art["milk"], carton_side, orange_cap)
                    elif kind == 4:
                        _emit_product(parts, _pillow_pack, "CRISP CLUB POTATO CHIPS", origin, angle, scale, art["chips"], foil, height=0.34, width=0.19, depth=0.055, name="Kettle chip stand pouch")
                    elif kind == 5:
                        _emit_product(parts, _pillow_pack, "NOCTURNE CHOCOLATE BAR", origin, angle, scale, art["bar"], foil, height=0.15, width=0.22, depth=0.035, name="Chocolate foil pillow pack")
                    else:
                        _emit_product(parts, _deli_tub, "DELI FRESH PASTA CUP", origin, angle, scale, art["deli"], deli_lid, deli_cup)

    # Compact impulse merchandise is modeled as real wrapped packages rather than
    # the former colored placeholder blocks on the checkout display.
    for index, artwork in enumerate((art["bar"], art["chips"], art["deli"])):
        _emit_product(
            parts, _pillow_pack, "CHECKOUT IMPULSE SNACK " + str(index + 1),
            (6.76 + index * 0.14, -3.52, 1.365), 0.0, 0.58,
            artwork, foil, height=0.17, width=0.12, depth=0.035,
            name="Checkout impulse wrapped snack"
        )

    # Two double-door merchandisers, two bays per cabinet, four adjustable shelves.
    # Every item is centered inside its own door bay and rests just above the deck.
    chilled = []
    cabinet_centers = (-5.20, -3.32)
    shelf_levels = (0.475, 0.875, 1.275, 1.655)
    for cabinet, cabinet_x in enumerate(cabinet_centers):
        for door, door_offset in enumerate((-0.435, 0.435)):
            bay_center = cabinet_x + door_offset
            for shelf_index, shelf_z in enumerate(shelf_levels):
                for item in range(4):
                    x = bay_center - 0.27 + item * 0.18
                    origin = (x, 4.42, shelf_z)
                    angle = -math.pi / 2
                    scale = 0.90
                    if (cabinet + door + shelf_index + item) % 2 == 0:
                        _emit_product(chilled, _can, "CHILLED EMBER COLA CAN", origin, angle, scale, art["can"], metal, dark_metal)
                    else:
                        _emit_product(chilled, _soda_bottle, "CHILLED SUNBURST PET BOTTLE", origin, angle, scale, art["soda"], orange_cap, plastic)
    return parts, chilled
