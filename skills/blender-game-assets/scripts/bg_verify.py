"""Re-import an exported FBX/GLB in a clean background Blender and report what a consumer
(Mixamo, Godot) will see.

  /Applications/Blender.app/Contents/MacOS/Blender -b --python bg_verify.py -- FILE [RENDER_PREFIX]

Prints one line starting with VERIFY + JSON: objects, tris, height, zmin, transforms,
front direction (head's front-most vertex y; negative = faces -Y), images and whether they are
packed, armature bones, actions. With RENDER_PREFIX also renders the head at frames 1/20/40
of the first action (for checking skinning after export).
"""
import bpy
import json
import math
import sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
path = argv[0]
prefix = argv[1] if len(argv) > 1 else None
bpy.ops.wm.read_homefile(use_empty=True)
if path.lower().endswith(".fbx"):
    bpy.ops.import_scene.fbx(filepath=path)
else:
    bpy.ops.import_scene.gltf(filepath=path)
sc = bpy.context.scene
info = {"objects": [(o.name, o.type) for o in sc.objects]}
meshes = [o for o in sc.objects if o.type == 'MESH' and len(o.data.polygons) > 20]
arms = [o for o in sc.objects if o.type == 'ARMATURE']
if meshes:
    o = max(meshes, key=lambda m: len(m.data.polygons))
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    vs = [o.matrix_world @ v.co for v in me.vertices]
    zmin, zmax = min(v.z for v in vs), max(v.z for v in vs)
    head = [v for v in vs if v.z > zmax - 0.15 * (zmax - zmin)]
    info.update(mesh=o.name, tris=sum(len(p.vertices) - 2 for p in o.data.polygons),
                height=round(zmax - zmin, 3), zmin=round(zmin, 3),
                loc=[round(c, 3) for c in o.location], rot=[round(c, 3) for c in o.rotation_euler],
                scale=[round(c, 3) for c in o.scale], front_y=round(min(v.y for v in head), 3),
                materials=[s.material.name for s in o.material_slots if s.material])
    ev.to_mesh_clear()
info["images"] = [(i.name, tuple(i.size), bool(i.packed_file)) for i in bpy.data.images]
if arms:
    a = arms[0]
    info["bones"] = len(a.data.bones)
    info["action"] = a.animation_data.action.name if a.animation_data and a.animation_data.action else None
print("VERIFY " + json.dumps(info, ensure_ascii=False))

if prefix and arms and meshes:
    a = arms[0]
    cam = bpy.data.objects.new("C", bpy.data.cameras.new("C"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 0.32
    sun = bpy.data.objects.new("S", bpy.data.lights.new("S", 'SUN'))
    sc.collection.objects.link(sun)
    sun.data.energy = 3
    sun.rotation_euler = (math.radians(35), 0, math.radians(15))
    w = bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.6, 0.7, 1)
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = sc.render.resolution_y = 400
    head_bone = next((b for b in a.pose.bones if b.name.endswith("Head")), None)
    for f in (1, 20, 40):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        c = a.matrix_world @ head_bone.head + Vector((0, 0, 0.06))
        d = Vector((0.35, -1, 0.1)).normalized()
        cam.location = c + d * 2
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f"{prefix}face_{f}.png"
        bpy.ops.render.render(write_still=True)
    print("RENDERED")
