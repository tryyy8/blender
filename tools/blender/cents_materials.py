"""Shared deterministic, material-specific texture generation for CENTS assets.

Material maps are generated as tileable images and packed into export-ready GLB
files. Each family has its own pattern logic; no universal noise recipe is used.
"""
import bpy
import numpy as np

def fract(value):
    return value - np.floor(value)


def periodic_value_noise(size, cells, seed):
    """Tileable bilinear value noise. Each material chooses its own scales."""
    rng = np.random.default_rng(seed)
    grid = rng.random((cells, cells), dtype=np.float32)
    axis = np.arange(size, dtype=np.float32) / size * cells
    ix = np.floor(axis).astype(np.int32)
    fx = axis - ix
    smooth = fx * fx * (3.0 - 2.0 * fx)
    x0 = ix % cells
    x1 = (x0 + 1) % cells
    y0 = x0
    y1 = x1
    a = grid[np.ix_(y0, x0)]
    b = grid[np.ix_(y0, x1)]
    c = grid[np.ix_(y1, x0)]
    d = grid[np.ix_(y1, x1)]
    sx = smooth[None, :]
    sy = smooth[:, None]
    return ((a * (1 - sx) + b * sx) * (1 - sy) +
            (c * (1 - sx) + d * sx) * sy)


def make_uv(size):
    axis = np.arange(size, dtype=np.float32) / size
    return np.meshgrid(axis, axis)


def clamp01(value):
    return np.clip(value, 0.0, 1.0)


def stone_surface(size, seed, base):
    """Blocky mineral stratification, recessed joints, and weather-softened edges."""
    u, v = make_uv(size)
    count = 8
    x, y = u * count, v * count
    ix, iy = np.floor(x), np.floor(y)
    nearest = np.full((size, size), 10.0, dtype=np.float32)
    second = np.full_like(nearest, 10.0)
    nearest_x = np.zeros_like(nearest)
    nearest_y = np.zeros_like(nearest)

    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            cx, cy = ix + ox, iy + oy
            hx = fract(np.sin(cx * 127.1 + cy * 311.7 + seed * 0.13) * 43758.5453)
            hy = fract(np.sin(cx * 269.5 + cy * 183.3 + seed * 0.37) * 24634.6345)
            px = cx + 0.5 + (hx - 0.5) * 0.40
            py = cy + 0.5 + (hy - 0.5) * 0.34
            dx, dy = x - px, y - py
            dx -= np.round(dx / count) * count
            dy -= np.round(dy / count) * count
            dist = np.sqrt(dx * dx + dy * dy)
            replace = dist < nearest
            second = np.where(replace, nearest, np.minimum(second, dist))
            nearest = np.minimum(nearest, dist)
            nearest_x = np.where(replace, cx, nearest_x)
            nearest_y = np.where(replace, cy, nearest_y)

    cell_tone = fract(np.sin(nearest_x * 91.7 + nearest_y * 43.3 + seed * 0.71) * 15731.743)
    boundary = 1.0 - clamp01((second - nearest - 0.018) / 0.075)
    mineral = periodic_value_noise(size, 27, seed + 1) - 0.5
    grain = periodic_value_noise(size, 91, seed + 2) - 0.5
    strata = np.sin((v * 2.0 + 0.035 * np.sin(u * 2 * np.pi * 5)) * 2 * np.pi * 13)
    variation = 0.87 + cell_tone * 0.22 + mineral * 0.13 + grain * 0.045
    seam = 1.0 - 0.42 * boundary
    color = np.stack([base[i] * variation * seam for i in range(3)], axis=-1)
    color += (strata * 0.012 + mineral * 0.018)[..., None]
    height = 0.025 * (1.0 - boundary) + mineral * 0.020 + grain * 0.006 + strata * 0.002
    rough = clamp01(0.79 + mineral * 0.16 + grain * 0.07 + boundary * 0.06)
    return clamp01(color), rough, height


def plaster_surface(size, seed, base):
    """Broad trowel movement, soft mineral clouding, and a fine chalky tooth."""
    u, v = make_uv(size)
    broad_a = periodic_value_noise(size, 5, seed + 10)
    broad_b = periodic_value_noise(size, 11, seed + 11)
    fine = periodic_value_noise(size, 74, seed + 12)
    chalk = periodic_value_noise(size, 166, seed + 13)
    sweep = np.sin(2 * np.pi * (v * 3.4 + 0.12 * np.sin(u * 2 * np.pi * 2.0)))
    trowel = np.sin(2 * np.pi * (u * 1.3 + v * 0.75 + broad_a * 0.20))
    value = (broad_a - 0.5) * 0.16 + (broad_b - 0.5) * 0.075
    value += sweep * 0.024 + trowel * 0.012 + (fine - 0.5) * 0.045 + (chalk - 0.5) * 0.018
    color = np.stack([base[i] * (1 + value) for i in range(3)], axis=-1)
    height = (broad_a - 0.5) * 0.020 + sweep * 0.003 + (fine - 0.5) * 0.006
    rough = clamp01(0.91 + (fine - 0.5) * 0.08 + (broad_b - 0.5) * 0.05)
    return clamp01(color), rough, height


def wood_surface(size, seed, base):
    """Longitudinal growth grain, slow tonal ribbons, and localized knots."""
    u, v = make_uv(size)
    warp = 0.75 * np.sin(2 * np.pi * (u * 3.0 + v * 1.6))
    warp += 0.30 * (periodic_value_noise(size, 9, seed + 20) - 0.5)
    phase = 2 * np.pi * (v * 47.0 + warp)
    tight_grain = np.sin(phase)
    broad_grain = np.sin(2 * np.pi * (v * 12.0 + 0.16 * np.sin(u * 2 * np.pi * 4)))
    pores = periodic_value_noise(size, 118, seed + 21) - 0.5
    knot_field = np.zeros((size, size), dtype=np.float32)
    knot_height = np.zeros_like(knot_field)
    for ku, kv, radius in ((0.28, 0.34, 0.075), (0.72, 0.68, 0.060)):
        du = u - ku
        dv = v - kv
        du -= np.round(du)
        dv -= np.round(dv)
        radius_field = np.sqrt((du * 0.72) ** 2 + dv ** 2)
        ring = np.sin(radius_field * 2 * np.pi * 30 + warp * 2)
        influence = np.exp(-((radius_field / radius) ** 2) * 2.2)
        knot_field += ring * influence
        knot_height += np.cos(radius_field * 2 * np.pi * 24) * influence
    value = broad_grain * 0.065 + tight_grain * 0.025 + pores * 0.035 - knot_field * 0.040
    color = np.stack([base[i] * (1 + value) for i in range(3)], axis=-1)
    height = tight_grain * 0.003 + broad_grain * 0.004 + pores * 0.003 + knot_height * 0.006
    rough = clamp01(0.60 + np.abs(tight_grain) * 0.10 + pores * 0.08 + knot_field * 0.035)
    return clamp01(color), rough, height


def metal_surface(size, seed, base):
    """Directional machining marks, fine scratches, and restrained patina."""
    u, v = make_uv(size)
    broad = periodic_value_noise(size, 7, seed + 30)
    patina = periodic_value_noise(size, 19, seed + 31)
    fine = periodic_value_noise(size, 154, seed + 32)
    direction = np.sin(2 * np.pi * (v * 210.0 + broad * 0.32 + patina * 0.08))
    hairline = np.sin(2 * np.pi * (v * 510.0 + u * 3.0 + fine * 0.20))
    scratch_mask = np.clip((fine - 0.76) * 4.0, 0, 1)
    patina_mask = np.clip((patina - 0.66) * 2.0, 0, 0.30)
    value = direction * 0.018 + hairline * 0.006 + (broad - 0.5) * 0.045
    color = np.stack([base[i] * (1 + value) for i in range(3)], axis=-1)
    color[..., 1] += patina_mask * 0.020
    color[..., 2] += patina_mask * 0.012
    color += scratch_mask[..., None] * 0.018
    height = direction * 0.0015 + scratch_mask * 0.002
    rough = clamp01(0.32 + (fine - 0.5) * 0.10 + np.abs(direction) * 0.045 + patina_mask * 0.15)
    return clamp01(color), rough, height


def concrete_surface(size, seed, base):
    """Visible fine aggregate, casting pores, and broad cured-concrete variation."""
    u, v = make_uv(size)
    cloud = periodic_value_noise(size, 8, seed + 40)
    aggregate = periodic_value_noise(size, 31, seed + 41)
    grit = periodic_value_noise(size, 104, seed + 42)
    pores = periodic_value_noise(size, 188, seed + 43)
    aggregate_mask = np.clip((aggregate - 0.67) * 3.0, 0, 1)
    pore_mask = np.clip((0.24 - pores) * 3.8, 0, 0.55)
    value = (cloud - 0.5) * 0.13 + (aggregate - 0.5) * 0.10 + (grit - 0.5) * 0.075
    color = np.stack([base[i] * (1 + value) for i in range(3)], axis=-1)
    color *= (1.0 - aggregate_mask[..., None] * 0.12)
    color *= (1.0 - pore_mask[..., None] * 0.07)
    height = (cloud - 0.5) * 0.010 + aggregate_mask * 0.012 - pore_mask * 0.010 + (grit - 0.5) * 0.004
    rough = clamp01(0.88 + (grit - 0.5) * 0.10 + aggregate_mask * 0.05 + pore_mask * 0.05)
    return clamp01(color), rough, height


def asphalt_surface(size, seed, base):
    """Dense mineral aggregate with embedded binder and broad repair-like patches."""
    u, v = make_uv(size)
    binder = periodic_value_noise(size, 9, seed + 50)
    aggregate = periodic_value_noise(size, 57, seed + 51)
    grit = periodic_value_noise(size, 162, seed + 52)
    patch = periodic_value_noise(size, 4, seed + 53)
    stones = np.clip((aggregate - 0.60) * 2.8, 0, 1)
    flecks = np.clip((grit - 0.70) * 3.2, 0, 1)
    value = (binder - 0.5) * 0.14 + (aggregate - 0.5) * 0.10 + (patch - 0.5) * 0.07
    color = np.stack([base[i] * (1 + value) for i in range(3)], axis=-1)
    color += stones[..., None] * np.array([0.035, 0.034, 0.030], dtype=np.float32)
    color += flecks[..., None] * np.array([0.030, 0.030, 0.028], dtype=np.float32)
    height = (binder - 0.5) * 0.008 + stones * 0.010 + flecks * 0.004
    rough = clamp01(0.94 + (grit - 0.5) * 0.08 + stones * 0.025)
    return clamp01(color), rough, height




def fabric_surface(size, seed, base):
    """Woven warp/weft structure with soft dye variation and raised fiber crossings."""
    u, v = make_uv(size)
    warp = np.cos(2 * np.pi * (u * 72.0 + 0.18 * np.sin(v * 2 * np.pi * 3.0)))
    weft = np.cos(2 * np.pi * (v * 72.0 + 0.16 * np.sin(u * 2 * np.pi * 4.0)))
    dye = periodic_value_noise(size, 9, seed + 60)
    fiber = periodic_value_noise(size, 145, seed + 61)
    weave = (warp + weft) * 0.012 + warp * weft * 0.012
    value = (dye - 0.5) * 0.11 + (fiber - 0.5) * 0.035 + weave
    color = np.stack([base[i] * (1 + value) for i in range(3)], axis=-1)
    height = warp * 0.0018 + weft * 0.0018 + (dye - 0.5) * 0.004
    rough = clamp01(0.91 + (fiber - 0.5) * 0.06 + np.abs(weave) * 0.22)
    return clamp01(color), rough, height


def painted_surface(size, seed, base):
    """Layered painted finish with roller stipple, broad pigment variation and fine wear."""
    u, v = make_uv(size)
    broad = periodic_value_noise(size, 6, seed + 70)
    roller = periodic_value_noise(size, 26, seed + 71)
    stipple = periodic_value_noise(size, 132, seed + 72)
    scratches = periodic_value_noise(size, 190, seed + 73)
    roller_ridges = np.sin(2 * np.pi * (v * 18.0 + 0.11 * np.sin(u * 2 * np.pi * 2.0)))
    wear = np.clip((scratches - 0.83) * 4.0, 0, 0.22)
    value = (broad - 0.5) * 0.075 + (roller - 0.5) * 0.055 + (stipple - 0.5) * 0.035
    color = np.stack([base[i] * (1 + value) for i in range(3)], axis=-1)
    color *= (1.0 - wear[..., None] * 0.28)
    height = (roller - 0.5) * 0.005 + roller_ridges * 0.0018 + (stipple - 0.5) * 0.002
    rough = clamp01(0.72 + (stipple - 0.5) * 0.09 + wear * 0.45)
    return clamp01(color), rough, height


GENERATORS = {
    "stone": stone_surface,
    "plaster": plaster_surface,
    "wood": wood_surface,
    "metal": metal_surface,
    "concrete": concrete_surface,
    "asphalt": asphalt_surface,
}


def make_image(name, pixels, non_color=False):
    height, width = pixels.shape[:2]
    rgba = np.empty((height, width, 4), dtype=np.float32)
    rgba[..., :3] = pixels
    rgba[..., 3] = 1.0
    image = bpy.data.images.new(name, width=width, height=height, alpha=False, float_buffer=False)
    image.pixels.foreach_set(rgba.reshape(-1))
    if non_color:
        image.colorspace_settings.name = "Non-Color"
    image.pack()
    return image


def material_family(name, family, base, roughness, metallic, size, seed):
    color, rough_map, height_map = GENERATORS[family](size, seed, np.array(base, dtype=np.float32))
    gy, gx = np.gradient(height_map)
    nx = -gx * 8.0
    ny = -gy * 8.0
    nz = np.ones_like(nx)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    normal = np.stack([nx / length, ny / length, nz / length], axis=-1) * 0.5 + 0.5
    rough_pixels = np.repeat(rough_map[..., None], 3, axis=-1)

    color_image = make_image("CENTS " + family + " base color", color)
    rough_image = make_image("CENTS " + family + " roughness", rough_pixels, True)
    normal_image = make_image("CENTS " + family + " tangent normal", normal, True)

    material = bpy.data.materials.new("CENTS · " + name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic

    base_tex = nodes.new("ShaderNodeTexImage")
    base_tex.name = family + " authored color map"
    base_tex.image = color_image
    base_tex.interpolation = "Linear"
    base_tex.extension = "REPEAT"
    links.new(base_tex.outputs["Color"], bsdf.inputs["Base Color"])

    rough_tex = nodes.new("ShaderNodeTexImage")
    rough_tex.name = family + " authored roughness map"
    rough_tex.image = rough_image
    rough_tex.interpolation = "Linear"
    rough_tex.extension = "REPEAT"
    links.new(rough_tex.outputs["Color"], bsdf.inputs["Roughness"])

    normal_tex = nodes.new("ShaderNodeTexImage")
    normal_tex.name = family + " authored normal map"
    normal_tex.image = normal_image
    normal_tex.interpolation = "Linear"
    normal_tex.extension = "REPEAT"
    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.inputs["Strength"].default_value = 0.42 if family in ("stone", "concrete", "asphalt") else 0.28
    links.new(normal_tex.outputs["Color"], normal_map.inputs["Color"])
    links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])
    return material


