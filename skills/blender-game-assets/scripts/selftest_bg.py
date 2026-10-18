"""Smoke test for bpy_lib.py in a background Blender (run after Blender upgrades):

  /Applications/Blender.app/Contents/MacOS/Blender -b --python selftest_bg.py -- OUT_DIR

Exercises block-out, UVs, baking, post-processing, material, export, character reduction,
body seams and rig helpers on synthetic objects. Prints SELFTEST OK + a JSON summary.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "bpy_lib.py")).read())

out = sys.argv[sys.argv.index("--") + 1]
os.makedirs(out, exist_ok=True)
summary = {}
bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene

# --- block-out: a tiny gable house
bm = bmesh.new()
box(bm, -2.05, 2.05, -3.05, 3.05, 0, 0.5, drop=(0, 2))
ledge_ring(bm, (-2.05, 2.05, -3.05, 3.05), (-2, 2, -3, 3), 0.5)
prism(bm, [(-2, 0.5), (2, 0.5), (2, 3.0), (0, 4.5), (-2, 3.0)], 'XZ', -3, 3, drop=(0, 2, 3))
prism(bm, [(2.4, 2.65), (2.4, 2.8), (0, 4.62), (-2.4, 2.8), (-2.4, 2.65), (0, 4.47)], 'XZ', -3.3, 3.3,
      drop=('cap_lo', 'cap_hi'))
band = offset_band([(2.44, 2.78), (0, 4.63)], [0.2])
prism(bm, band, 'XZ', -3.34, -3.0)
prism(bm, band, 'XZ', 3.0, 3.34)
lp = mesh_from_bm(bm, "T_LP")
summary["lp_tris"] = tri_count(lp.data)

# --- high poly with a textured material (checker colour + metallic texture)
hp = lp.copy()
hp.data = lp.data.copy()
hp.name = "T_HP"
sc.collection.objects.link(hp)
sub = hp.modifiers.new("s", 'SUBSURF')
sub.subdivision_type = 'SIMPLE'
sub.levels = 3
activate(hp)
bpy.ops.object.modifier_apply(modifier="s")
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project()
bpy.ops.object.mode_set(mode='OBJECT')
img = bpy.data.images.new("chk", 256, 256)
img.generated_type = 'COLOR_GRID'
m = bpy.data.materials.new("HP_Mat")
m.use_nodes = True
bs = m.node_tree.nodes["Principled BSDF"]
t = m.node_tree.nodes.new('ShaderNodeTexImage')
t.image = img
m.node_tree.links.new(t.outputs[0], bs.inputs['Base Color'])
m.node_tree.links.new(t.outputs[0], bs.inputs['Metallic'])
hp.data.materials.append(m)
summary["hp_tris"] = tri_count(hp.data)

# --- UV, bake, post, material, export
unwrap_hard_surface(lp)
tex = os.path.join(out, "textures")
summary["bake_times"] = bake_maps(hp, lp, tex, "T", res=256, cage=0.03, max_ray=0.1, ao_samples=8)
polys = underside_uv_polys(lp)
import json
json.dump(polys, open(os.path.join(out, "under.json"), "w"))
post = os.path.join(HERE, "maps_post.py")
subprocess.run(["python3", post, "flatten", os.path.join(tex, "T_normal.png"), os.path.join(out, "under.json")], check=True)
subprocess.run(["python3", post, "pack-orm", tex, "T"], check=True)
game_material(lp, "T", tex)
summary["glb_bytes"] = export_glb(os.path.join(out, "T.glb"), [lp])

# --- self bake + normal from albedo
alb = bpy.data.images.load(os.path.join(tex, "T_albedo.png"))
nimg = normal_from_albedo(alb, "T_nrm2", strength=4.0)
ao = bpy.data.images.new("T_ao2", 128, 128)
bake_self(lp, ao, typ='AO', samples=4)
summary["self_bake"] = True

# --- character reduction + body seams on a stretched sphere "body"
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=0.3)
body = bpy.context.active_object
body.scale = (1.0, 0.6, 3.0)
bpy.ops.object.transform_apply(scale=True)
body.location = (6, 0, 0)
bpy.ops.object.transform_apply(location=True)
ch = character_lowpoly(body, name="T_CH", voxel=0.02, detail_tris=600, total_tris=2000)
summary["char_tris"] = tri_count(ch.data)
summary["char_islands"] = unwrap_character(ch)

# --- rig helpers on a 3-bone armature skinning the body
arm_data = bpy.data.armatures.new("T_Arm")
arm = bpy.data.objects.new("T_Arm", arm_data)
sc.collection.objects.link(arm)
activate(arm)
bpy.ops.object.mode_set(mode='EDIT')
for nm, h, tl, par in (("mixamorig:Hips", (6, 0, -0.9), (6, 0, 0.3), None),
                       ("mixamorig:Neck", (6, 0, 0.3), (6, 0, 0.6), "mixamorig:Hips"),
                       ("mixamorig:Head", (6, 0, 0.6), (6, 0, 0.9), "mixamorig:Neck")):
    b = arm_data.edit_bones.new(nm)
    b.head, b.tail = h, tl
    if par:
        b.parent = arm_data.edit_bones[par]
bpy.ops.object.mode_set(mode='OBJECT')
for nm in ("mixamorig:Hips", "mixamorig:Neck", "mixamorig:Head"):
    ch.vertex_groups.new(name=nm)
for v in ch.data.vertices:
    z = v.co.z
    if z < 0.3:
        ch.vertex_groups["mixamorig:Hips"].add([v.index], 1.0, 'REPLACE')
    else:
        ch.vertex_groups["mixamorig:Neck"].add([v.index], 0.5, 'REPLACE')
        ch.vertex_groups["mixamorig:Head"].add([v.index], 0.5, 'REPLACE')
ch.parent = arm
mod = ch.modifiers.new("Armature", 'ARMATURE')
mod.object = arm
summary["profile_rows"] = len(weight_profile(ch, arm, 0.3, 0.9, x_half=7))
summary["head_fix"] = fix_head_weights(ch, arm, chin_yz=(-0.2, 0.45), nape_yz=(0.2, 0.55),
                                       head_center=(6, 0, 0.7), radius=0.6, half_width=7)
limit_weights(ch, 4)
stress_pose(arm, [("Head", (0, 0, 1), 30), ("Neck", (1, 0, 0), -15)])
reset_pose(arm)
summary["mixamo_fbx_bytes"] = export_mixamo_fbx(body, os.path.join(out, "T_mixamo.fbx"))

# --- review renders
cam = review_setup()
files = render_shots({"lp": [lp], "hp": [hp]},
                     {"iso": dict(loc=(9, -9, 8), target=(0, 0, 2), lens=35),
                      "top": dict(loc=(0, 0, 20), target=(0, 0, 0), ortho=9)},
                     os.path.join(out, "r_"), res=(256, 256), cam=cam)
summary["renders"] = len(files)
print("SELFTEST OK " + json.dumps(summary, default=str))
