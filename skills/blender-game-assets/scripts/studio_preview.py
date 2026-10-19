"""Neutral, repeatable character review lighting; Blender-side helper.

Create in a dedicated review scene. Does not modify mesh, UV or materials.
"""
from pathlib import Path
import bpy
from mathutils import Vector


def setup_studio(scene, objects, hdri_path=None):
    points = [ob.matrix_world @ Vector(p) for ob in objects for p in ob.bound_box]
    if not points:
        raise ValueError('Pass the optimized mesh objects to review')
    low = Vector([min(p[i] for p in points) for i in range(3)])
    high = Vector([max(p[i] for p in points) for i in range(3)])
    center = (low + high) / 2
    height = high.z - low.z
    scale = max(height, .01) / 2.5
    cx, cy = center.x, center.y
    if any(o.type == 'LIGHT' for o in scene.objects):
        raise ValueError('Use a dedicated preview scene without existing lights')
    def aim(ob, target):
        ob.rotation_euler = (Vector(target) - ob.location).to_track_quat('-Z', 'Y').to_euler()
    def area(name, xyz, power, size):
        data = bpy.data.lights.new(name, 'AREA')
        data.energy = power * scale ** 2
        data.shape = 'DISK'
        data.size = size * scale
        data.color = (1,1,1)
        ob = bpy.data.objects.new(name, data)
        scene.collection.objects.link(ob)
        ob.location = (cx + xyz[0]*scale, cy + xyz[1]*scale, low.z + xyz[2]*scale)
        aim(ob, center)
    area('Studio_Key', (-3,-4,4), 250, 3)
    area('Studio_Fill', (3,-2,3), 90, 4)
    area('Studio_Rim', (1,3,4), 180, 3)
    scene.world = bpy.data.worlds.new('Asset_Studio_World')
    scene.world.use_nodes = True
    nodes = scene.world.node_tree.nodes
    nodes.clear()
    out = nodes.new('ShaderNodeOutputWorld')
    env = nodes.new('ShaderNodeTexEnvironment')
    if hdri_path is None:
        hdri_path = Path(bpy.app.binary_path).parent.parent/'Resources'/('.'.join(map(str,bpy.app.version[:2])))/'datafiles/studiolights/world/studio.exr'
    hdri_path = Path(hdri_path)
    if not hdri_path.is_file():
        raise FileNotFoundError('Choose an existing neutral studio HDRI: '+str(hdri_path))
    env.image = bpy.data.images.load(str(hdri_path), check_existing=True)
    env.image.pack()
    illumination = nodes.new('ShaderNodeBackground')
    illumination.inputs['Strength'].default_value = .65
    background = nodes.new('ShaderNodeBackground')
    background.inputs['Color'].default_value = (.065,.065,.065,1)
    background.inputs['Strength'].default_value = 1
    rays = nodes.new('ShaderNodeLightPath')
    mix = nodes.new('ShaderNodeMixShader')
    links = scene.world.node_tree.links
    links.new(env.outputs['Color'], illumination.inputs['Color'])
    links.new(rays.outputs['Is Camera Ray'], mix.inputs[0])
    links.new(illumination.outputs[0], mix.inputs[1])
    links.new(background.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs['Surface'])
    scene.render.engine = 'BLENDER_EEVEE'
    scene.display_settings.display_device = 'sRGB'
    scene.view_settings.view_transform = 'Khronos PBR Neutral'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.shading.type = 'RENDERED'
                space.shading.use_scene_lights_render = True
                space.shading.use_scene_world_render = True
                space.overlay.show_overlays = False
                space.region_3d.view_perspective = 'CAMERA'
    return {'preset':'neutral-character-studio-v1','view_transform':scene.view_settings.view_transform,
            'exposure':0,'gamma':1,'hdri':str(hdri_path),'hdri_strength':.65,
            'key_w_at_2_5m':250,'fill_w_at_2_5m':90,'rim_w_at_2_5m':180,
            'height_m':height,'bounds_low':list(low),'bounds_high':list(high)}
