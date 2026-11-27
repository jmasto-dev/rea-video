import bpy
import math
from mathutils import Vector
from scene_utils import (
    reset_scene, add_volume_cube, make_principled_mat,
    add_camera, add_area_light, add_spot_light, add_point_light,
    add_text_3d, add_bevel
)


def build_beat07():
    scene = reset_scene()
    add_volume_cube(size=20.0, location=(0, 0, 2.0), density=0.016, anisotropy=0.45, color=(0.55, 0.62, 0.72, 1.0))

    mat_velvet = make_principled_mat("VelvetPedestal", base_color=(0.014, 0.013, 0.020, 1.0), roughness=0.95)
    mat_floor = make_principled_mat("DarkFloor", base_color=(0.006, 0.006, 0.008, 1.0), roughness=0.90)
    mat_brass = make_principled_mat("BrushedBrass", base_color=(0.84, 0.60, 0.22, 1.0), metallic=0.94, roughness=0.25)
    mat_steel = make_principled_mat("BrushedSteel", base_color=(0.72, 0.75, 0.80, 1.0), metallic=0.94, roughness=0.22)
    mat_glass = make_principled_mat("OpticalGlass", base_color=(0.92, 0.96, 1.0, 1.0), metallic=0.0, roughness=0.04,
                                    transmission=0.95, ior=1.52)
    mat_dark_metal = make_principled_mat("KeyholeMetal", base_color=(0.08, 0.08, 0.09, 1.0), metallic=0.85, roughness=0.35)

    # Background floor
    bpy.ops.mesh.primitive_plane_add(size=20.0, location=(0, 0, -0.5))
    bpy.context.active_object.data.materials.append(mat_floor)

    # Matte velvet pedestal
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.55, depth=0.50, location=(0, 0, -0.25))
    ped = bpy.context.active_object
    add_bevel(ped, width=0.015, segments=3)
    ped.data.materials.append(mat_velvet)

    # Padlock outer brushed-brass frame (hollowed front/back look via side/top/bottom rails + glass core)
    # Base body: 0.44 wide, 0.18 deep, 0.46 tall, resting at z=0
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.23))
    body = bpy.context.active_object
    body.scale = (0.44, 0.16, 0.46)
    bpy.ops.object.transform_apply(scale=True)
    add_bevel(body, width=0.025, segments=3)
    body.data.materials.append(mat_brass)

    # Optical glass front window & core plate
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.01, 0.23))
    glass_core = bpy.context.active_object
    glass_core.scale = (0.34, 0.175, 0.36)
    bpy.ops.object.transform_apply(scale=True)
    add_bevel(glass_core, width=0.012, segments=2)
    glass_core.data.materials.append(mat_glass)

    # Internal brass cryptographic tumbler discs visible behind/inside glass
    for tz, tr in [(0.16, 0.07), (0.24, 0.09), (0.32, 0.06)]:
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=tr, depth=0.04, location=(0.07, 0.0, tz), rotation=(math.radians(90), 0, 0))
        disc = bpy.context.active_object
        disc.data.materials.append(mat_brass)

    # Unmarred keyhole escutcheon on front
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.055, depth=0.02, location=(-0.05, -0.098, 0.22), rotation=(math.radians(90), 0, 0))
    esc = bpy.context.active_object
    esc.data.materials.append(mat_brass)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.05, -0.105, 0.21))
    slot = bpy.context.active_object
    slot.scale = (0.014, 0.015, 0.05)
    bpy.ops.object.transform_apply(scale=True)
    slot.data.materials.append(mat_dark_metal)

    # 4 corner brass rivets
    for rx in (-0.18, 0.18):
        for rz in (0.05, 0.41):
            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.016, depth=0.02, location=(rx, -0.085, rz), rotation=(math.radians(90), 0, 0))
            bpy.context.active_object.data.materials.append(mat_steel)

    # Intact U-shaped shackle (Bezier curve)
    shackle_data = bpy.data.curves.new("Shackle", type='CURVE')
    shackle_data.dimensions = '3D'
    shackle_data.bevel_depth = 0.036
    shackle_data.bevel_resolution = 6
    sp = shackle_data.splines.new('BEZIER')
    sp.bezier_points.add(3)
    pts = [
        (-0.13, 0.0, 0.44),
        (-0.13, 0.0, 0.72),
        (0.13, 0.0, 0.72),
        (0.13, 0.0, 0.44),
    ]
    for idx, co in enumerate(pts):
        sp.bezier_points[idx].co = co
        sp.bezier_points[idx].handle_left_type = 'AUTO'
        sp.bezier_points[idx].handle_right_type = 'AUTO'
    shackle_obj = bpy.data.objects.new("ShackleObj", shackle_data)
    bpy.context.collection.objects.link(shackle_obj)
    shackle_obj.data.materials.append(mat_steel)

    # Single overhead volumetric spotlight cone
    add_spot_light("OverheadCone", (0.08, -0.15, 2.4), (0, 0, 0.25), energy=260.0, color=(1.0, 0.94, 0.84), spot_size_deg=26.0, spot_blend=0.35, radius=0.06)
    # Subtle front-left graze to reveal glass & internal brass tumblers
    add_spot_light("FrontGraze", (-1.4, -2.2, 1.1), (0, 0, 0.24), energy=65.0, color=(1.0, 0.92, 0.80), spot_size_deg=24.0, spot_blend=0.5, radius=0.15)
    # Subtle cool rim light to catch glass & shackle edges
    add_area_light("CoolRim", (-0.9, 1.2, 0.9), (0, 0, 0.35), energy=36.0, color=(0.50, 0.70, 1.0), size=0.6)

    # Camera: 85mm f/2.0 macro (pulled back slightly so full shackle arch has headroom)
    add_camera("Cam_Beat07", location=(1.25, -5.4, 0.72), target=(0.0, 0.0, 0.36), lens=85.0, fstop=2.0, use_dof=True)
    return scene


def build_beat08():
    scene = reset_scene()
    add_volume_cube(size=20.0, location=(0, 0, 2.0), density=0.014, anisotropy=0.35, color=(0.55, 0.62, 0.72, 1.0))

    mat_desk = make_principled_mat("DarkDesk", base_color=(0.022, 0.017, 0.014, 1.0), roughness=0.80)
    mat_paper = make_principled_mat("PaperManifest", base_color=(0.86, 0.85, 0.81, 1.0), roughness=0.88)
    mat_ink = make_principled_mat("DarkInk", base_color=(0.04, 0.04, 0.05, 1.0), roughness=0.85)
    mat_red_ink = make_principled_mat("RedStampInk", base_color=(0.72, 0.06, 0.05, 1.0), roughness=0.76)
    mat_gunmetal = make_principled_mat("GunmetalArm", base_color=(0.09, 0.10, 0.12, 1.0), metallic=0.88, roughness=0.35)
    mat_brass = make_principled_mat("StampBrass", base_color=(0.86, 0.63, 0.22, 1.0), metallic=0.94, roughness=0.24)

    # Dark desk surface
    bpy.ops.mesh.primitive_plane_add(size=16.0, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(mat_desk)

    # Staggered stack of white paper manifests with subtle curl/tilt
    num_sheets = 14
    for i in range(num_sheets):
        z = 0.004 + i * 0.0048
        ox = math.sin(i * 1.9) * 0.014
        oy = math.cos(i * 1.4) * 0.010
        rot_z = math.radians(math.sin(i * 2.3) * 2.6)
        rot_y = math.radians(math.sin(i * 1.1) * 0.4)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(ox, oy, z), rotation=(0, rot_y, rot_z))
        sheet = bpy.context.active_object
        sheet.scale = (0.48, 0.34, 0.0032)
        bpy.ops.object.transform_apply(scale=True)
        add_bevel(sheet, width=0.0008, segments=1)
        sheet.data.materials.append(mat_paper)

    top_z = 0.004 + (num_sheets - 1) * 0.0048 + 0.002

    # Printed dark ink lines on top sheet
    for li, ly in enumerate([0.11, 0.07, 0.03, -0.06, -0.10]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.06, ly, top_z + 0.0005))
        line = bpy.context.active_object
        line.scale = (0.28 if li > 0 else 0.18, 0.008, 0.001)
        bpy.ops.object.transform_apply(scale=True)
        line.data.materials.append(mat_ink)

    # Red "APPROVED" stamp impression cleanly visible on top sheet
    add_text_3d(
        "ApprovedInk", "APPROVED",
        location=(0.04, -0.02, top_z + 0.0015),
        rotation_deg=(0, 0, -5),
        size=0.056,
        extrude=0.001,
        bevel=0.0,
        mat=mat_red_ink
    )

    # Brass die head lifted slightly above the paper so the red APPROVED impression is clearly visible underneath
    die_z = top_z + 0.095
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.04, -0.01, die_z))
    die = bpy.context.active_object
    die.scale = (0.22, 0.11, 0.065)
    bpy.ops.object.transform_apply(scale=True)
    add_bevel(die, width=0.006, segments=3)
    die.data.materials.append(mat_brass)

    # Engraved "APPROVED" label on front face of brass stamp head
    add_text_3d(
        "DieLabel", "APPROVED",
        location=(0.04, -0.067, die_z),
        rotation_deg=(90, 0, 0),
        size=0.030,
        extrude=0.004,
        bevel=0.001,
        mat=mat_brass
    )

    # Smooth vertical piston shaft (48 vertices + Shade Smooth)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.030, depth=0.34, location=(0.04, -0.01, die_z + 0.20))
    piston = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    piston.data.materials.append(mat_gunmetal)

    # Smooth brass collar ring on piston
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.040, depth=0.028, location=(0.04, -0.01, die_z + 0.045))
    collar = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    collar.data.materials.append(mat_brass)

    # Sleek horizontal mechanical arm extending out of frame right (no giant dark foreground pillar!)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.45, -0.01, die_z + 0.37))
    arm = bpy.context.active_object
    arm.scale = (0.95, 0.085, 0.075)
    bpy.ops.object.transform_apply(scale=True)
    add_bevel(arm, width=0.010, segments=3)
    arm.data.materials.append(mat_gunmetal)

    # Warm tungsten desk lighting + subtle cool fill
    add_spot_light("TungstenLamp", (-0.65, -0.85, 1.35), (0.04, 0.0, 0.08), energy=145.0, color=(1.0, 0.72, 0.38), spot_size_deg=42.0, spot_blend=0.45, radius=0.10)
    add_area_light("CoolFill", (1.1, -0.7, 0.85), (0.0, 0.0, 0.15), energy=26.0, color=(0.45, 0.62, 0.92), size=0.8)

    # Camera: 50mm f/2.8 side-profile (balanced composition without right-side pillar)
    add_camera("Cam_Beat08", location=(-0.18, -1.72, 0.44), target=(0.04, 0.0, 0.16), lens=50.0, fstop=2.8, use_dof=True)
    return scene


def build_beat10():
    scene = reset_scene()
    scene.cycles.samples = 40  # Bumped to 40 with denoiser to eliminate floor shadow noise
    add_volume_cube(size=60.0, location=(0, 12, 3), density=0.024, anisotropy=0.48, color=(0.55, 0.66, 0.80, 1.0))

    mat_floor = make_principled_mat("CorridorFloor", base_color=(0.012, 0.014, 0.018, 1.0), roughness=0.72)
    mat_wall = make_principled_mat("CorridorWall", base_color=(0.008, 0.009, 0.012, 1.0), roughness=0.88)
    mat_rack = make_principled_mat("ServerRack", base_color=(0.018, 0.020, 0.026, 1.0), metallic=0.68, roughness=0.42)
    mat_rail = make_principled_mat("RackRail", base_color=(0.10, 0.12, 0.15, 1.0), metallic=0.88, roughness=0.32)
    mat_led_green = make_principled_mat("LEDGreen", base_color=(0.2, 1.0, 0.45, 1.0),
                                        emission_color=(0.15, 1.0, 0.42, 1.0), emission_strength=6.5)
    mat_led_white = make_principled_mat("LEDWhite", base_color=(0.85, 0.95, 1.0, 1.0),
                                        emission_color=(0.80, 0.92, 1.0, 1.0), emission_strength=5.5)
    mat_backlit = make_principled_mat("BacklitDoor", base_color=(0.65, 0.82, 1.0, 1.0),
                                      emission_color=(0.55, 0.78, 1.0, 1.0), emission_strength=2.6)
    mat_terminal_screen = make_principled_mat("TerminalScreen", base_color=(0.15, 0.85, 0.95, 1.0),
                                              emission_color=(0.12, 0.82, 1.0, 1.0), emission_strength=4.5)

    # Floor & ceiling & side walls
    bpy.ops.mesh.primitive_plane_add(size=40.0, location=(0, 12, 0))
    bpy.context.active_object.data.materials.append(mat_floor)

    bpy.ops.mesh.primitive_plane_add(size=40.0, location=(0, 12, 3.6), rotation=(math.radians(180), 0, 0))
    bpy.context.active_object.data.materials.append(mat_wall)

    for sx in (-2.3, 2.3):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sx, 12, 1.8))
        w = bpy.context.active_object
        w.scale = (0.2, 36.0, 3.8)
        bpy.ops.object.transform_apply(scale=True)
        w.data.materials.append(mat_wall)

    # Beveled server racks with vertical metallic rack rails along both sides
    for i in range(9):
        ry = 1.5 + i * 2.2
        for side in (-1, 1):
            rx = side * 1.68
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(rx, ry, 1.45))
            rack = bpy.context.active_object
            rack.scale = (0.95, 1.75, 2.9)
            bpy.ops.object.transform_apply(scale=True)
            add_bevel(rack, width=0.025, segments=2)
            rack.data.materials.append(mat_rack)

            # Vertical metallic rack rails on front & back edges of each cabinet
            rail_x = side * 1.19
            for rail_dy in (-0.82, 0.82):
                bpy.ops.mesh.primitive_cube_add(size=1.0, location=(rail_x, ry + rail_dy, 1.45))
                rail = bpy.context.active_object
                rail.scale = (0.04, 0.05, 2.86)
                bpy.ops.object.transform_apply(scale=True)
                rail.data.materials.append(mat_rail)

            # Status LEDs facing the aisle
            led_x = side * 1.17
            for lz_idx in range(6):
                lz = 0.45 + lz_idx * 0.42
                bpy.ops.mesh.primitive_cube_add(size=1.0, location=(led_x, ry - 0.35 + (lz_idx % 3) * 0.32, lz))
                led = bpy.context.active_object
                led.scale = (0.02, 0.14, 0.020)
                bpy.ops.object.transform_apply(scale=True)
                led.data.materials.append(mat_led_green if (i + lz_idx) % 2 == 0 else mat_led_white)

    # Pure ominous architectural end: open beveled doorway frame + single glowing open terminal inside
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 23.5, 1.5))
    door = bpy.context.active_object
    door.scale = (2.1, 0.1, 3.0)
    bpy.ops.object.transform_apply(scale=True)
    door.data.materials.append(mat_backlit)

    # Doorway frame pillars & lintel
    for dx in (-1.10, 1.10):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(dx, 23.35, 1.5))
        dp = bpy.context.active_object
        dp.scale = (0.14, 0.24, 3.0)
        bpy.ops.object.transform_apply(scale=True)
        add_bevel(dp, width=0.015, segments=2)
        dp.data.materials.append(mat_rail)

    # Single open glowing terminal console silhouetted inside the doorway at y = 21.8
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 21.8, 0.55))
    desk = bpy.context.active_object
    desk.scale = (0.85, 0.55, 1.10)
    bpy.ops.object.transform_apply(scale=True)
    add_bevel(desk, width=0.02, segments=2)
    desk.data.materials.append(mat_rack)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 21.75, 1.32), rotation=(math.radians(-12), 0, 0))
    monitor = bpy.context.active_object
    monitor.scale = (0.68, 0.04, 0.42)
    bpy.ops.object.transform_apply(scale=True)
    monitor.data.materials.append(mat_terminal_screen)

    # Volumetric light beams pouring from the back doorway down the corridor
    add_spot_light("BackSpotMain", (0, 23.2, 2.3), (0, 8.0, 0.6), energy=750.0, color=(0.60, 0.80, 1.0), spot_size_deg=38.0, spot_blend=0.5, radius=0.35)
    add_spot_light("BackSpotFloor", (0, 23.2, 1.2), (0, 10.0, 0.0), energy=350.0, color=(0.45, 0.72, 1.0), spot_size_deg=44.0, spot_blend=0.6, radius=0.4)
    for ly in (3.0, 9.0, 15.0):
        add_point_light(f"AisleLight_{ly}", (0, ly, 3.3), energy=18.0, color=(0.55, 0.78, 0.95), radius=0.3)

    # Camera: 35mm 1-point perspective
    add_camera("Cam_Beat10", location=(0.0, -1.8, 1.48), target=(0.0, 21.8, 1.30), lens=35.0, fstop=2.8, use_dof=True)
    return scene
