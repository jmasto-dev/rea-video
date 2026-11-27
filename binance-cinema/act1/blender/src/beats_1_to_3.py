import bpy
import math
from mathutils import Vector
from scene_utils import (
    reset_scene, add_volume_cube, make_principled_mat, make_textured_mat,
    add_camera, add_area_light, add_spot_light, add_point_light,
    add_text_3d, add_bevel
)


def build_beat01():
    scene = reset_scene()
    add_volume_cube(size=50.0, location=(0, 0, 5), density=0.018, anisotropy=0.45, color=(0.55, 0.64, 0.76, 1.0))

    # Materials: procedural noise bump/roughness on monolith & floor
    mat_obsidian = make_textured_mat("Obsidian", base_color=(0.014, 0.016, 0.021, 1.0),
                                     rough_min=0.72, rough_max=0.90, noise_scale=8.0, bump_strength=0.14)
    mat_nameplate = make_textured_mat("Nameplate", base_color=(0.008, 0.009, 0.012, 1.0),
                                      rough_min=0.76, rough_max=0.88, noise_scale=14.0, bump_strength=0.06)
    mat_floor = make_textured_mat("ObsidianFloor", base_color=(0.011, 0.013, 0.018, 1.0),
                                  rough_min=0.68, rough_max=0.86, noise_scale=6.0, bump_strength=0.08)
    mat_brass_text = make_principled_mat("CarvedBrass", base_color=(0.86, 0.64, 0.25, 1.0), metallic=0.92, roughness=0.26)
    mat_amber_emit = make_principled_mat("AmberCore", base_color=(1.0, 0.48, 0.08, 1.0),
                                         emission_color=(1.0, 0.45, 0.06, 1.0), emission_strength=9.5)
    mat_stream_amber = make_principled_mat("StreamAmber", base_color=(1.0, 0.58, 0.14, 1.0),
                                           emission_color=(1.0, 0.48, 0.08, 1.0), emission_strength=7.0)
    mat_stream_cyan = make_principled_mat("StreamCyan", base_color=(0.18, 0.78, 1.0, 1.0),
                                          emission_color=(0.12, 0.72, 1.0, 1.0), emission_strength=6.0)

    # Floor
    bpy.ops.mesh.primitive_plane_add(size=40.0, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(mat_floor)

    # Monolith built from 6 separated beveled blocks
    blocks = [
        (-0.62, 0.0, 1.1, 1.16, 1.4, 2.16),
        (0.62, 0.0, 1.1, 1.16, 1.4, 2.16),
        (-0.62, 0.0, 3.32, 1.16, 1.4, 2.16),
        (0.62, 0.0, 3.32, 1.16, 1.4, 2.16),
        (-0.62, 0.0, 5.54, 1.16, 1.4, 2.16),
        (0.62, 0.0, 5.54, 1.16, 1.4, 2.16),
    ]
    for i, (x, y, z, sx, sy, sz) in enumerate(blocks):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z))
        b = bpy.context.active_object
        b.name = f"MonolithBlock_{i}"
        b.scale = (sx, sy, sz)
        bpy.ops.object.transform_apply(scale=True)
        add_bevel(b, width=0.025, segments=2)
        b.data.materials.append(mat_obsidian)

    # Glowing amber core inside the seams
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 3.2))
    core = bpy.context.active_object
    core.name = "AmberCore"
    core.scale = (2.14, 1.14, 6.2)
    bpy.ops.object.transform_apply(scale=True)
    core.data.materials.append(mat_amber_emit)

    # Soft grazing elongated area strips along seams (zero circular point-light hotspots)
    add_area_light("SeamWashFront", (0, -0.95, 2.2), (0, -0.7, 2.2), energy=22.0, color=(1.0, 0.50, 0.10), size=2.0, size_y=0.25)
    add_area_light("SeamWashSideL", (-1.45, 0.0, 2.6), (-1.1, 0.0, 2.6), energy=18.0, color=(1.0, 0.48, 0.08), size=0.35, size_y=3.2)
    add_area_light("SeamWashSideR", (1.45, 0.0, 2.6), (1.1, 0.0, 2.6), energy=18.0, color=(1.0, 0.48, 0.08), size=0.35, size_y=3.2)

    # Dark recessed/bridging nameplate masking the vertical slit behind BINANCE
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.715, 3.05))
    plate = bpy.context.active_object
    plate.name = "BinanceNameplate"
    plate.scale = (1.88, 0.06, 0.56)
    bpy.ops.object.transform_apply(scale=True)
    add_bevel(plate, width=0.012, segments=2)
    plate.data.materials.append(mat_nameplate)

    # 3D Extruded BINANCE text proud on the nameplate
    add_text_3d(
        "BinanceText", "BINANCE",
        location=(0, -0.75, 3.05),
        rotation_deg=(90, 0, 0),
        size=0.34,
        extrude=0.032,
        bevel=0.006,
        mat=mat_brass_text
    )

    # 10 glowing floor/air streams bursting outward from the monolith base
    for i in range(10):
        angle = math.radians(-155 + i * 34.4)
        dx = math.cos(angle)
        dy = math.sin(angle)

        curve_data = bpy.data.curves.new(f"Stream_{i}", type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.bevel_depth = 0.022 if i % 2 == 0 else 0.016
        curve_data.bevel_resolution = 4

        spline = curve_data.splines.new('BEZIER')
        spline.bezier_points.add(2)
        p0, p1, p2 = spline.bezier_points

        p0.co = (dx * 0.6, dy * 0.6, 0.25 + (i % 3) * 0.18)
        p1.co = (dx * 2.5, dy * 2.5, 0.08 + (i % 2) * 0.12)
        p2.co = (dx * 6.8, dy * 6.8, 0.03)
        for p in (p0, p1, p2):
            p.handle_left_type = 'AUTO'
            p.handle_right_type = 'AUTO'

        curve_obj = bpy.data.objects.new(f"StreamObj_{i}", curve_data)
        bpy.context.collection.objects.link(curve_obj)
        curve_obj.data.materials.append(mat_stream_amber if i % 2 == 0 else mat_stream_cyan)

    # Soft grazing rim lights + subtle volumetric background haze behind monolith
    add_spot_light("RimLeft", (-6.0, 4.0, 5.5), (0, 0, 2.5), energy=360.0, color=(0.45, 0.68, 1.0), spot_size_deg=42.0, spot_blend=0.5, radius=0.6)
    add_spot_light("RimRight", (6.0, 4.0, 5.5), (0, 0, 2.5), energy=340.0, color=(0.45, 0.68, 1.0), spot_size_deg=42.0, spot_blend=0.5, radius=0.6)
    add_area_light("BackHaze", (0, 6.5, 3.2), (0, 0, 2.4), energy=280.0, color=(0.30, 0.46, 0.72), size=7.0, size_y=4.5)
    add_spot_light("FaceKey", (2.4, -6.2, 5.0), (0, -0.75, 3.05), energy=210.0, color=(0.90, 0.92, 1.0), spot_size_deg=26.0, spot_blend=0.5, radius=0.35)

    # Camera: 50mm f/2.2
    add_camera("Cam_Beat01", location=(2.8, -13.5, 2.3), target=(0.0, -0.2, 2.0), lens=50.0, fstop=2.2, use_dof=True)
    return scene


def build_beat02():
    scene = reset_scene()
    add_volume_cube(size=60.0, location=(0, 0, 8), density=0.014, anisotropy=0.42, color=(0.55, 0.64, 0.76, 1.0))

    # Dark brushed slate/metal architectural floor catching soft specular reflections from conduits
    mat_floor = make_textured_mat("SlateGridFloor", base_color=(0.040, 0.045, 0.055, 1.0), metallic=0.40,
                                  rough_min=0.24, rough_max=0.34, noise_scale=12.0, bump_strength=0.05)
    mat_tile = make_textured_mat("SlateTile", base_color=(0.048, 0.055, 0.068, 1.0), metallic=0.42,
                                 rough_min=0.22, rough_max=0.32, noise_scale=10.0, bump_strength=0.05)
    mat_obsidian = make_textured_mat("ObsidianTower", base_color=(0.032, 0.036, 0.046, 1.0), metallic=0.35,
                                     rough_min=0.36, rough_max=0.48, noise_scale=8.0, bump_strength=0.08)
    mat_node_metal = make_principled_mat("NodePedestalMetal", base_color=(0.24, 0.27, 0.32, 1.0), metallic=0.90, roughness=0.24)
    mat_node_core = make_principled_mat("NodeDarkCore", base_color=(0.015, 0.018, 0.024, 1.0), roughness=0.65)
    mat_cyan = make_principled_mat("CyanEmit", base_color=(0.15, 0.80, 1.0, 1.0),
                                   emission_color=(0.12, 0.75, 1.0, 1.0), emission_strength=4.5)
    mat_amber = make_principled_mat("AmberEmit", base_color=(1.0, 0.52, 0.10, 1.0),
                                    emission_color=(1.0, 0.48, 0.08, 1.0), emission_strength=4.8)
    mat_ticker = make_principled_mat("TickerMetal", base_color=(0.88, 0.90, 0.96, 1.0),
                                     metallic=0.75, roughness=0.30,
                                     emission_color=(0.75, 0.85, 1.0, 1.0), emission_strength=1.4)

    # Base floor
    bpy.ops.mesh.primitive_plane_add(size=50.0, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(mat_floor)

    # Architectural grid tiles with visible beveled seams
    for gx in range(-6, 7):
        for gy in range(-6, 7):
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(gx * 2.2, gy * 2.2, 0.01))
            t = bpy.context.active_object
            t.scale = (2.12, 2.12, 0.04)
            bpy.ops.object.transform_apply(scale=True)
            add_bevel(t, width=0.015, segments=2)
            t.data.materials.append(mat_tile)

    # Central monolith tower (3D height + wide beveled top cap)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 2.4))
    mono = bpy.context.active_object
    mono.scale = (1.9, 1.35, 4.8)
    bpy.ops.object.transform_apply(scale=True)
    add_bevel(mono, width=0.08, segments=3)
    mono.data.materials.append(mat_obsidian)

    # Dark beveled octagonal collar around monolith base + thin non-clipping glowing ring
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1.75, depth=0.14, location=(0, 0, 0.07))
    collar = bpy.context.active_object
    add_bevel(collar, width=0.025, segments=2)
    collar.data.materials.append(mat_node_metal)

    bpy.ops.mesh.primitive_torus_add(major_radius=1.48, minor_radius=0.032, location=(0, 0, 0.15))
    ring = bpy.context.active_object
    ring.data.materials.append(mat_amber)

    # 10 radial conduits + 10 beveled 3D metallic octagonal pedestals with recessed glowing cores
    tickers = ["BTC", "ETH", "SOL", "XRP", "TRON", "BNB", "ADA", "AVAX", "DOGE", "LINK"]
    radius_node = 4.5
    for i, ticker in enumerate(tickers):
        ang = math.radians(i * 36.0 + 18.0)
        nx = math.cos(ang) * radius_node
        ny = math.sin(ang) * radius_node
        is_amber = (i % 2 == 0)
        c_mat = mat_amber if is_amber else mat_cyan

        # Conduit from collar to node
        mid_x = math.cos(ang) * (radius_node * 0.52)
        mid_y = math.sin(ang) * (radius_node * 0.52)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(mid_x, mid_y, 0.05))
        cond = bpy.context.active_object
        cond.scale = (radius_node - 1.5, 0.075, 0.045)
        cond.rotation_euler = (0, 0, ang)
        bpy.ops.object.transform_apply(scale=True)
        cond.data.materials.append(c_mat)

        # Beveled 3D brushed-metallic octagonal housing/pedestal
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.90, depth=0.32, location=(nx, ny, 0.16))
        plinth = bpy.context.active_object
        add_bevel(plinth, width=0.055, segments=3)
        plinth.data.materials.append(mat_node_metal)

        # Dark recessed inner core
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.68, depth=0.05, location=(nx, ny, 0.30))
        recess = bpy.context.active_object
        recess.data.materials.append(mat_node_core)

        # Recessed glowing ring inside pedestal
        bpy.ops.mesh.primitive_torus_add(major_radius=0.66, minor_radius=0.022, location=(nx, ny, 0.315))
        tor = bpy.context.active_object
        tor.data.materials.append(c_mat)

        # Engraved/raised 3D ticker text facing upward
        add_text_3d(
            f"Ticker_{ticker}", ticker,
            location=(nx, ny, 0.33),
            rotation_deg=(0, 0, 0),
            size=0.32,
            extrude=0.022,
            bevel=0.004,
            mat=mat_ticker
        )

    # Soft wide cool overhead area light so the brushed slate floor & 10 metallic nodes catch light & reflections
    add_area_light("WideOverheadSlate", (0, -2.0, 14.0), (0, 0, 0), energy=1200.0, color=(0.55, 0.72, 0.98), size=18.0, size_y=12.0)
    # Crisp rim lights on the top edges/bevels & faces of the central monolith tower
    add_spot_light("TowerTopRimL", (-5.5, 4.5, 7.8), (0, 0, 4.4), energy=900.0, color=(0.55, 0.78, 1.0), spot_size_deg=32.0, spot_blend=0.4, radius=0.25)
    add_spot_light("TowerTopRimR", (5.5, 4.5, 7.8), (0, 0, 4.4), energy=850.0, color=(1.0, 0.72, 0.38), spot_size_deg=32.0, spot_blend=0.4, radius=0.25)
    add_area_light("TowerTopCap", (0, 2.5, 8.5), (0, 0, 4.8), energy=320.0, color=(0.75, 0.86, 1.0), size=2.8)

    # Camera: 28mm pulled back ~12% so bottom AVAX node has generous margin above bottom edge
    add_camera("Cam_Beat02", location=(0.0, -7.0, 20.8), target=(0.0, -0.2, 0.2), lens=28.0, fstop=2.8, use_dof=True)
    return scene


def build_beat03():
    scene = reset_scene()
    add_volume_cube(size=50.0, location=(0, 0, 5), density=0.017, anisotropy=0.44, color=(0.52, 0.62, 0.75, 1.0))

    mat_stone = make_textured_mat("DarkStone", base_color=(0.020, 0.022, 0.027, 1.0),
                                  rough_min=0.76, rough_max=0.90, noise_scale=9.0, bump_strength=0.14)
    mat_abyss = make_principled_mat("Abyss", base_color=(0.002, 0.002, 0.003, 1.0), roughness=0.95)
    mat_brass = make_principled_mat("LedgerBrass", base_color=(0.88, 0.64, 0.22, 1.0), metallic=0.92, roughness=0.24)
    mat_dark_brass = make_principled_mat("EngravedLineBrass", base_color=(0.35, 0.25, 0.10, 1.0), metallic=0.85, roughness=0.38)
    mat_amber = make_principled_mat("DrainAmber", base_color=(1.0, 0.6, 0.15, 1.0),
                                    emission_color=(1.0, 0.52, 0.10, 1.0), emission_strength=6.5)
    mat_cyan = make_principled_mat("DrainCyan", base_color=(0.2, 0.82, 1.0, 1.0),
                                   emission_color=(0.15, 0.75, 1.0, 1.0), emission_strength=6.0)

    # Stepped pit floor
    for r_in, r_out, z in [
        (3.2, 20.0, 0.0),
        (2.8, 3.25, -0.35),
        (2.4, 2.85, -0.75),
        (2.0, 2.45, -1.20),
    ]:
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=r_out, depth=0.35, location=(0, 0, z - 0.175))
        outer = bpy.context.active_object
        outer.data.materials.append(mat_stone)
        if r_in > 0:
            bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=r_in, depth=1.0, location=(0, 0, z - 0.175))
            cutter = bpy.context.active_object
            bool_mod = outer.modifiers.new(name="PitCut", type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = cutter
            bpy.context.view_layer.objects.active = outer
            bpy.ops.object.modifier_apply(modifier="PitCut")
            bpy.data.objects.remove(cutter, do_unlink=True)

    # Pitch-black pit bottom
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=3.5, depth=0.2, location=(0, 0, -2.5))
    bpy.context.active_object.data.materials.append(mat_abyss)

    # Streams strictly confined to the central pit rim (no stray tubes poking into bottom corners)
    for i in range(6):
        ang = math.radians(35 + i * 22.0)  # Arc along the far/mid pit rim toward the abyss
        dx, dy = math.cos(ang), math.sin(ang)
        c_data = bpy.data.curves.new(f"Drain_{i}", type='CURVE')
        c_data.dimensions = '3D'
        c_data.bevel_depth = 0.020
        c_data.bevel_resolution = 4
        sp = c_data.splines.new('BEZIER')
        sp.bezier_points.add(2)
        p0, p1, p2 = sp.bezier_points
        p0.co = (dx * 3.1, dy * 3.1, 0.02)
        p1.co = (dx * 2.3, dy * 2.3, -0.25)
        p2.co = (dx * 1.1, dy * 1.1, -2.2)
        for p in (p0, p1, p2):
            p.handle_left_type = 'AUTO'
            p.handle_right_type = 'AUTO'
        obj = bpy.data.objects.new(f"DrainObj_{i}", c_data)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(mat_amber if i % 2 == 0 else mat_cyan)

    # Carved stone & brass ledger monument
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 3.6, 0.95))
    ledger = bpy.context.active_object
    ledger.scale = (5.4, 0.85, 1.9)
    bpy.ops.object.transform_apply(scale=True)
    add_bevel(ledger, width=0.045, segments=3)
    ledger.data.materials.append(mat_stone)

    # Subtle engraved horizontal ledger lines on slab face
    for lz in (0.48, 0.62, 1.54, 1.66):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 3.16, lz))
        ln = bpy.context.active_object
        ln.scale = (4.6, 0.02, 0.014)
        bpy.ops.object.transform_apply(scale=True)
        ln.data.materials.append(mat_dark_brass)

    # 3D Brass numerals "$6.3 BILLION"
    add_text_3d(
        "LedgerAmount", "$6.3 BILLION",
        location=(0, 3.14, 1.08),
        rotation_deg=(90, 0, 0),
        size=0.62,
        extrude=0.06,
        bevel=0.010,
        mat=mat_brass
    )

    # Sharp directional key light on "$6.3 BILLION"
    add_spot_light("SharpKey", (3.8, -1.8, 3.6), (0, 3.1, 1.05), energy=420.0, color=(1.0, 0.90, 0.75), spot_size_deg=28.0, spot_blend=0.25, radius=0.12)
    # Crisp rim light along top/right bevel of slab
    add_spot_light("SlabRim", (4.8, 5.2, 3.4), (0.8, 3.5, 1.4), energy=480.0, color=(0.55, 0.78, 1.0), spot_size_deg=34.0, spot_blend=0.35, radius=0.15)
    # Soft volumetric backlight gradient behind the slab
    add_area_light("BackGradient", (0, 7.8, 2.2), (0, 3.6, 1.2), energy=260.0, color=(0.32, 0.52, 0.82), size=7.5, size_y=4.0)
    add_point_light("PitGlow", (0, 0, -1.2), energy=28.0, color=(1.0, 0.52, 0.14), radius=0.5)

    # Camera: 65mm f/2.4 low-angle
    add_camera("Cam_Beat03", location=(1.6, -9.5, 1.05), target=(0.0, 2.2, 0.88), lens=65.0, fstop=2.4, use_dof=True)
    return scene
