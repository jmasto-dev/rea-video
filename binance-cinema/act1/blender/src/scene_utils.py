import bpy
import math
from mathutils import Vector, Euler

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    # Render engine: Cycles CPU
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 28
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.02
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 3
    scene.cycles.transmission_bounces = 6
    scene.cycles.volume_bounces = 0
    scene.cycles.volume_step_rate = 1.5
    scene.cycles.volume_max_steps = 64

    # Resolution: 1920x804 (2.39:1 anamorphic)
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 804
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '8'

    # Color Management: AgX - High Contrast
    scene.view_settings.view_transform = 'AgX'
    try:
        scene.view_settings.look = 'AgX - High Contrast'
    except Exception:
        scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0

    # World Background: near-black (0.004, 0.005, 0.007)
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.004, 0.005, 0.007, 1.0)
        bg.inputs["Strength"].default_value = 1.0

    return scene


def add_volume_cube(name="VolumeCube", size=60.0, location=(0, 0, 10), density=0.022, anisotropy=0.4, color=(0.75, 0.82, 0.90, 1.0)):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.active_object
    cube.name = name

    mat = bpy.data.materials.new(name=f"{name}_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    vol = nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = color
    vol.inputs["Density"].default_value = density
    vol.inputs["Anisotropy"].default_value = anisotropy

    links.new(vol.outputs["Volume"], out.inputs["Volume"])
    cube.data.materials.append(mat)
    # Hide from viewport/shadow rays if needed, keep volume
    cube.display_type = 'WIRE'
    return cube


def make_principled_mat(name, base_color=(0.05, 0.05, 0.06, 1.0), metallic=0.0, roughness=0.82,
                        emission_color=(0, 0, 0, 1), emission_strength=0.0,
                        transmission=0.0, ior=1.45):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = transmission
    bsdf.inputs["IOR"].default_value = ior
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = emission_color
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def make_textured_mat(name, base_color=(0.015, 0.017, 0.022, 1.0), metallic=0.0,
                      rough_min=0.72, rough_max=0.90, noise_scale=12.0, bump_strength=0.10):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Metallic"].default_value = metallic

    tex_coord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.65

    map_range = nodes.new("ShaderNodeMapRange")
    map_range.inputs["From Min"].default_value = 0.25
    map_range.inputs["From Max"].default_value = 0.75
    map_range.inputs["To Min"].default_value = rough_min
    map_range.inputs["To Max"].default_value = rough_max

    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.02

    links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], map_range.inputs["Value"])
    links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def add_camera(name="Camera", location=(0, -10, 2), target=(0, 0, 2), lens=50.0, fstop=2.2, use_dof=True):
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = lens
    cam_data.sensor_width = 36.0
    cam_data.clip_start = 0.1
    cam_data.clip_end = 200.0

    cam_obj = bpy.data.objects.new(name, cam_data)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = Vector(location)

    direction = Vector(target) - Vector(location)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

    if use_dof:
        cam_data.dof.use_dof = True
        cam_data.dof.focus_distance = direction.length
        cam_data.dof.aperture_fstop = fstop

    bpy.context.scene.camera = cam_obj
    return cam_obj


def add_area_light(name, location, target, energy=200.0, color=(1, 1, 1), size=2.0, size_y=None):
    light_data = bpy.data.lights.new(name=name, type='AREA')
    light_data.energy = energy
    light_data.color = color
    if size_y is not None:
        light_data.shape = 'RECTANGLE'
        light_data.size = size
        light_data.size_y = size_y
    else:
        light_data.shape = 'DISK'
        light_data.size = size

    light_obj = bpy.data.objects.new(name, light_data)
    bpy.context.collection.objects.link(light_obj)
    light_obj.location = Vector(location)
    direction = Vector(target) - Vector(location)
    light_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return light_obj


def add_spot_light(name, location, target, energy=500.0, color=(1, 1, 1), spot_size_deg=35.0, spot_blend=0.3, radius=0.2):
    light_data = bpy.data.lights.new(name=name, type='SPOT')
    light_data.energy = energy
    light_data.color = color
    light_data.spot_size = math.radians(spot_size_deg)
    light_data.spot_blend = spot_blend
    light_data.shadow_soft_size = radius

    light_obj = bpy.data.objects.new(name, light_data)
    bpy.context.collection.objects.link(light_obj)
    light_obj.location = Vector(location)
    direction = Vector(target) - Vector(location)
    light_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return light_obj


def add_point_light(name, location, energy=100.0, color=(1, 1, 1), radius=0.2):
    light_data = bpy.data.lights.new(name=name, type='POINT')
    light_data.energy = energy
    light_data.color = color
    light_data.shadow_soft_size = radius
    light_obj = bpy.data.objects.new(name, light_data)
    bpy.context.collection.objects.link(light_obj)
    light_obj.location = Vector(location)
    return light_obj


def add_text_3d(name, text, location=(0, 0, 0), rotation_deg=(90, 0, 0), size=1.0, extrude=0.05, bevel=0.008, align_x='CENTER', align_y='CENTER', mat=None):
    bpy.ops.object.text_add(location=location, rotation=tuple(math.radians(a) for a in rotation_deg))
    obj = bpy.context.active_object
    obj.name = name
    obj.data.body = text
    obj.data.size = size
    obj.data.extrude = extrude
    obj.data.bevel_depth = bevel
    obj.data.align_x = align_x
    obj.data.align_y = align_y
    if mat:
        obj.data.materials.append(mat)
    return obj


def add_bevel(obj, width=0.015, segments=2):
    mod = obj.modifiers.new(name="Bevel", type='BEVEL')
    mod.width = width
    mod.segments = segments
    return mod
