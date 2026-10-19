"""Blender-side helpers for turning Meshy / reference models into game assets.

Runs inside Blender: prepend to a job script with blender_exec.py
(`blender_exec.py bpy_lib.py job.py`) or exec() it from a `blender -b --python` script.
Units are metres, Z up, the model's front faces -Y (glTF/Godot +Z).
"""
import bpy
import bmesh
import math
import os
import time
from mathutils import Vector, Matrix, Quaternion

# --------------------------------------------------------------------------- files / scenes

def new_model_file(save_current_to=None):
    """Save the open file (to its own path, or to save_current_to) and start an empty one.
    One Blender file per model; the MCP add-on keeps listening across file loads."""
    if save_current_to:
        bpy.ops.wm.save_as_mainfile(filepath=save_current_to, compress=True)
    elif bpy.data.filepath:
        bpy.ops.wm.save_mainfile()
    bpy.ops.wm.read_homefile(use_empty=True)


def work_scene(name):
    """Get/create a scene and make it current (no-op on the window in background mode)."""
    sc = bpy.data.scenes.get(name) or bpy.data.scenes.new(name)
    if bpy.context.window:
        bpy.context.window.scene = sc
    return sc


def deselect_everywhere():
    """Deselect in every scene/view layer: glTF use_selection also picks up objects
    selected in other scenes."""
    for sc in bpy.data.scenes:
        for vl in sc.view_layers:
            for o in sc.objects:
                try:
                    o.select_set(False, view_layer=vl)
                except RuntimeError:
                    pass


def activate(obj, *others):
    """Select obj (+others) in the current view layer and make obj active."""
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in (obj,) + others:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = obj


def remove_object(name):
    o = bpy.data.objects.get(name)
    if not o:
        return
    data = o.data
    bpy.data.objects.remove(o, do_unlink=True)
    if data is not None and data.users == 0 and isinstance(data, bpy.types.Mesh):
        bpy.data.meshes.remove(data)


# --------------------------------------------------------------------------- import / inspect

def import_model(path):
    """Import FBX/GLB/OBJ into the current scene; returns the new objects."""
    before = set(bpy.data.objects)
    ext = os.path.splitext(path)[1].lower()
    if ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    elif ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=path)
    else:
        raise ValueError(f"unsupported format: {ext}")
    return [o for o in bpy.data.objects if o not in before]


def tri_count(mesh):
    return sum(len(p.vertices) - 2 for p in mesh.polygons)


def mesh_stats(o):
    m = o.data
    return {"name": o.name, "verts": len(m.vertices), "tris": tri_count(m),
            "dims": [round(d, 3) for d in o.dimensions],
            "loc": [round(c, 3) for c in o.location],
            "materials": [s.material.name for s in o.material_slots if s.material],
            "uv": [u.name for u in m.uv_layers], "vgroups": len(o.vertex_groups)}


def world_bounds(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)])
    mx = Vector([max(p[i] for p in pts) for i in range(3)])
    return mn, mx


def raycaster(obj):
    """hit(origin, direction) -> first hit location or None. Object space (Meshy imports
    have identity transforms; apply transforms first otherwise)."""
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())

    def hit(origin, direction):
        loc, _n, _i, _d = bvh.ray_cast(Vector(origin), Vector(direction).normalized())
        return loc
    return hit


# --------------------------------------------------------------------------- block-out

def prism(bm, pts, plane, lo, hi, drop=()):
    """Extrude a closed 2D profile. plane 'XZ': pts are (x, z), extruded along Y from lo to hi;
    'YZ': pts are (y, z), extruded along X. drop: side indices to delete (side i = pts[i]->pts[i+1])
    and/or 'cap_lo' / 'cap_hi'. Normals are recalculated outward before dropping."""
    def P(u, v, w):
        return (u, w, v) if plane == 'XZ' else (w, u, v)
    a = [bm.verts.new(P(u, v, lo)) for u, v in pts]
    b = [bm.verts.new(P(u, v, hi)) for u, v in pts]
    n = len(pts)
    faces = {'cap_lo': bm.faces.new(a), 'cap_hi': bm.faces.new(b)}
    for i in range(n):
        j = (i + 1) % n
        faces[i] = bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=list(faces.values()))
    bmesh.ops.delete(bm, geom=[faces[k] for k in drop], context='FACES_ONLY')


def box(bm, x0, x1, y0, y1, z0, z1, drop=()):
    """Axis-aligned box. Side indices for drop: 0 bottom, 1 +X, 2 top, 3 -X; caps = -Y/+Y."""
    prism(bm, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], 'XZ', y0, y1, drop)


def ledge_ring(bm, outer, inner, z):
    """Visible top strip of a plinth: ring between outer (x0,x1,y0,y1) and inner rectangles."""
    ox0, ox1, oy0, oy1 = outer
    ix0, ix1, iy0, iy1 = inner
    o = [bm.verts.new(v) for v in ((ox0, oy0, z), (ox1, oy0, z), (ox1, oy1, z), (ox0, oy1, z))]
    i = [bm.verts.new(v) for v in ((ix0, iy0, z), (ix1, iy0, z), (ix1, iy1, z), (ix0, iy1, z))]
    for k in range(4):
        f = bm.faces.new((o[k], o[(k + 1) % 4], i[(k + 1) % 4], i[k]))
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()


def offset_band(half, widths, lift=0.0):
    """Closed (x, z) profile of a symmetric trim band under a roof outline (barge boards).
    half: outline from the eave to the ridge, x >= 0, last point on x = 0.
    widths: band width per segment (len(half) - 1), measured perpendicular to the segment.
    lift raises the outer edge slightly above the roof so the band covers the roof end."""
    pts = [(x, z + lift) for x, z in half]
    segs = list(zip(pts[:-1], pts[1:]))

    def nrm(a, b):
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dz)
        return (dz / L, -dx / L)

    lines = []
    for (a, b), w in zip(segs, widths):
        n = nrm(a, b)
        lines.append(((a[0] - n[0] * w, a[1] - n[1] * w), (b[0] - a[0], b[1] - a[1])))

    def isect(l1, l2):
        (p, d), (q, e) = l1, l2
        det = d[0] * (-e[1]) - d[1] * (-e[0])
        t = ((q[0] - p[0]) * (-e[1]) - (q[1] - p[1]) * (-e[0])) / det
        return (p[0] + d[0] * t, p[1] + d[1] * t)

    inner = [lines[0][0]] + [isect(lines[k - 1], lines[k]) for k in range(1, len(lines))]
    p, d = lines[-1]
    inner.append((0.0, p[1] + d[1] * (-p[0] / d[0])))
    outer_full = pts + [(-x, z) for x, z in reversed(pts[:-1])]
    inner_full = [(-x, z) for x, z in inner[:-1]] + list(reversed(inner))
    return outer_full + inner_full


def mesh_from_bm(bm, name, scene=None, flat=True):
    """Merge doubles, write bm into a (re)created object `name` linked to scene."""
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    remove_object(name)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = not flat
    ob = bpy.data.objects.new(name, me)
    (scene or bpy.context.scene).collection.objects.link(ob)
    return ob


# --------------------------------------------------------------------------- UVs

def unwrap_hard_surface(obj, angle=45, shrink_down=0.35, margin=0.006, uv_name=None):
    """Smart-project UVs; downward faces (barely visible from a game camera) get smaller islands."""
    me = obj.data
    if uv_name:
        if uv_name in me.uv_layers:
            me.uv_layers.remove(me.uv_layers[uv_name])
        me.uv_layers.new(name=uv_name)
        me.uv_layers.active = me.uv_layers[uv_name]
    activate(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=0.0, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bm = bmesh.from_edit_mesh(me)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        if f.normal.z < -0.3:
            c = sum((l[uv].uv for l in f.loops), Vector((0, 0))) / len(f.loops)
            for l in f.loops:
                l[uv].uv = c + (l[uv].uv - c) * shrink_down
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, margin=margin)
    bpy.ops.object.mode_set(mode='OBJECT')


def unwrap_character(obj, head_scale=1.7, margin=0.004, cut_angle=2.2):
    """Body-part seams for an A-pose humanoid centred on X: regions + a cut on the least visible
    side of each cylinder, MINIMUM_STRETCH unwrap, average scale, head islands scaled up, pack.
    Returns island count. Thresholds are fractions of the mesh height."""
    from bpy_extras import bmesh_utils
    mn, mx = world_bounds(obj)
    h = mx.z - mn.z
    cx = (mn.x + mx.x) / 2
    mw = obj.matrix_world
    NECK, HIP, ANKLE = mn.z + 0.863 * h, mn.z + 0.437 * h, mn.z + 0.068 * h
    SHOULDER, WRIST, HAND_Z = 0.126 * h, 0.247 * h, mn.z + 0.579 * h
    activate(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    def label(f):
        p = mw @ f.calc_center_median()
        dx = p.x - cx
        side = 'L' if dx > 0 else 'R'
        if p.z < ANKLE:
            return 'sole' if f.normal.z < -0.5 else 'foot' + side
        if p.z > NECK:
            return 'head'
        if abs(dx) > WRIST and p.z < HAND_Z:
            return 'hand' + side
        if abs(dx) > SHOULDER and p.z > HIP:
            return 'arm' + side
        if p.z < HIP:
            return 'leg' + side
        return 'torso'

    def ref_dir(name):
        if name in ('head', 'torso'):
            return Vector((0, 1, 0))
        if name.startswith(('arm', 'hand')):
            return Vector((0, 0, -1))
        if name.startswith('leg'):
            return Vector((-1 if name.endswith('L') else 1, 0, 0))
        if name.startswith('foot'):
            return Vector((0, 1, 0))
        return None

    lab = {f.index: label(f) for f in bm.faces}
    groups = {}
    for f in bm.faces:
        groups.setdefault(lab[f.index], []).append(f)
    theta = {}
    for name, fs in groups.items():
        ref = ref_dir(name)
        if ref is None:
            continue
        pts = [f.calc_center_median() for f in fs]
        c = sum(pts, Vector()) / len(pts)
        cov = [[sum((p[i] - c[i]) * (p[j] - c[j]) for p in pts) for j in range(3)] for i in range(3)]
        a = Vector((0.3, 0.3, 1.0))
        for _ in range(30):
            a = Vector([sum(cov[i][j] * a[j] for j in range(3)) for i in range(3)]).normalized()
        u = -(ref - a * ref.dot(a)).normalized()
        v = a.cross(u)
        for f, p in zip(fs, pts):
            d = p - c
            theta[f.index] = math.atan2(d.dot(v), d.dot(u))
    for e in bm.edges:
        e.seam = False
        lf = e.link_faces
        if len(lf) != 2:
            continue
        fa, fb = lf
        if lab[fa.index] != lab[fb.index]:
            e.seam = True
            continue
        ta, tb = theta.get(fa.index), theta.get(fb.index)
        if ta is not None and tb is not None and abs(ta) > cut_angle and abs(tb) > cut_angle and (ta > 0) != (tb > 0):
            e.seam = True
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='MINIMUM_STRETCH', fill_holes=True, correct_aspect=True, margin=0.0)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    bm = bmesh.from_edit_mesh(obj.data)
    uv = bm.loops.layers.uv.active
    isl = bmesh_utils.bmesh_linked_uv_islands(bm, uv)
    for i in isl:
        if sum((mw @ f.calc_center_median()).z for f in i) / len(i) > NECK:
            c = sum((l[uv].uv for f in i for l in f.loops), Vector((0, 0))) / sum(len(f.loops) for f in i)
            for f in i:
                for l in f.loops:
                    l[uv].uv = c + (l[uv].uv - c) * head_scale
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, margin=margin)
    bpy.ops.object.mode_set(mode='OBJECT')
    return len(isl)


# --------------------------------------------------------------------------- reduction (characters)

def decimate_to(obj, target_tris, group=None, invert=False, tol=150):
    """Collapse-decimate obj to ~target_tris (binary search on ratio). With `group`, only that
    vertex group is decimated (invert=True: everything except it) — the group is a mask,
    not a soft weight. Applies the modifier; returns (ratio, tris)."""
    m = obj.modifiers.new("DecimateTo", 'DECIMATE')
    m.decimate_type = 'COLLAPSE'
    m.use_collapse_triangulate = True
    if group:
        m.vertex_group = group
        m.invert_vertex_group = invert

    def count(r):
        m.ratio = r
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        n = tri_count(me)
        ev.to_mesh_clear()
        return n

    lo, hi, best = 0.0005, 1.0, None
    for _ in range(18):
        mid = (lo + hi) / 2
        n = count(mid)
        best = (mid, n)
        if abs(n - target_tris) < tol:
            break
        if n > target_tris:
            hi = mid
        else:
            lo = mid
    m.ratio = best[0]
    activate(obj)
    bpy.ops.object.modifier_apply(modifier=m.name)
    return round(best[0], 5), tri_count(obj.data)


def character_lowpoly(hp, name="LP", voxel=0.005, detail_tris=3800, total_tris=12000, smooth_hair=True):
    """Voxel remesh a copy of hp, calm hair spikes, decimate head+hands then body to budget.
    Assumes an A-pose humanoid centred on X with identity transform. Returns the new object."""
    remove_object(name)
    mn, mx = world_bounds(hp)
    h = mx.z - mn.z
    cx = (mn.x + mx.x) / 2
    lp = hp.copy()
    lp.data = hp.data.copy()
    lp.name = name
    lp.data.name = name
    lp.modifiers.clear()
    lp.vertex_groups.clear()
    lp.data.materials.clear()
    bpy.context.scene.collection.objects.link(lp)
    lp.data.remesh_voxel_size = voxel
    lp.data.use_remesh_fix_poles = True
    activate(lp)
    bpy.ops.object.voxel_remesh()
    mw = lp.matrix_world
    V = lp.data.vertices
    det = lp.vertex_groups.new(name="detail")
    det_idx = [v.index for v in V
               if (mw @ v.co).z > mn.z + 0.868 * h
               or (abs((mw @ v.co).x - cx) > 0.232 * h and (mw @ v.co).z < mn.z + 0.579 * h)]
    det.add(det_idx, 1.0, 'REPLACE')
    if smooth_hair:
        hair = lp.vertex_groups.new(name="hair")
        z0, ramp = mn.z + 0.942 * h, 0.016 * h
        for v in V:
            z = (mw @ v.co).z
            if z > z0:
                hair.add([v.index], min(1.0, (z - z0) / ramp), 'REPLACE')
        sm = lp.modifiers.new("HairSmooth", 'SMOOTH')
        sm.vertex_group = "hair"
        sm.factor = 0.8
        sm.iterations = 25
        bpy.ops.object.modifier_apply(modifier=sm.name)
    start = tri_count(lp.data)
    share = len(det_idx) / len(V)
    decimate_to(lp, int(start - (start * share - detail_tris)), group="detail")
    decimate_to(lp, total_tris, group="detail", invert=True)
    for p in lp.data.polygons:
        p.use_smooth = True
    lp.vertex_groups.clear()
    return lp


# --------------------------------------------------------------------------- baking

def _new_image(name, res, color):
    i = bpy.data.images.get(name)
    if i:
        bpy.data.images.remove(i)
    i = bpy.data.images.new(name, res, res, alpha=False)
    i.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
    return i


def bake_maps(hp, lp, out_dir, name, res=2048, cage=0.03, max_ray=0.1, margin=16, ao_samples=64):
    """Selected-to-active Cycles bake hp -> lp: albedo, normal (tangent), roughness, AO and
    metallic (via a temporary emission on hp's metallic texture). Saves
    <out_dir>/<name>_{albedo,normal,rough,ao,metal}.png. cage/max_ray are in scene units.
    Returns bake times."""
    os.makedirs(out_dir, exist_ok=True)
    sc = bpy.context.scene
    for o in (hp, lp):
        o.hide_render = False
        o.hide_set(False)
    sc.render.engine = 'CYCLES'
    try:
        sc.cycles.device = 'GPU'
    except Exception:
        pass
    sc.render.bake.margin = margin
    sc.render.bake.margin_type = 'EXTEND'
    ims = {"albedo": _new_image(name + "_albedo", res, True), "normal": _new_image(name + "_normal", res, False),
           "rough": _new_image(name + "_rough", res, False), "ao": _new_image(name + "_ao", res, False),
           "metal": _new_image(name + "_metal", res, False)}
    mat = bpy.data.materials.get(name + "_Bake") or bpy.data.materials.new(name + "_Bake")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    tex = {}
    for k, i in ims.items():
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = i
        t.name = k
        tex[k] = t
    lp.data.materials.clear()
    lp.data.materials.append(mat)
    activate(lp, hp)
    bpy.context.view_layer.objects.active = lp
    common = dict(use_selected_to_active=True, cage_extrusion=cage, max_ray_distance=max_ray,
                  margin=margin, use_clear=True)
    times = {}

    def bake(key, typ, samples, **kw):
        nt.nodes.active = tex[key]
        sc.cycles.samples = samples
        t = time.time()
        bpy.ops.object.bake(type=typ, **common, **kw)
        times[key] = round(time.time() - t, 1)

    hm = hp.active_material
    bsdf = None
    if hm and hm.use_nodes:
        bsdf = next((n for n in hm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)

    def bake_input_as_emission(key, input_name):
        """Route a Principled input (texture or constant) of the source into an emission and bake
        EMIT: the raw value, unaffected by lighting or metalness. Returns False if not possible."""
        if bsdf is None:
            return False
        hn = hm.node_tree
        out = next(n for n in hn.nodes if n.type == 'OUTPUT_MATERIAL')
        prev = out.inputs['Surface'].links[0].from_socket
        em = hn.nodes.new('ShaderNodeEmission')
        inp = bsdf.inputs[input_name]
        if inp.links:
            hn.links.new(inp.links[0].from_socket, em.inputs['Color'])
        else:
            v = inp.default_value
            em.inputs['Color'].default_value = tuple(v) if hasattr(v, "__len__") else (v, v, v, 1.0)
        hn.links.new(em.outputs[0], out.inputs['Surface'])
        try:
            bake(key, 'EMIT', 4)
        finally:
            hn.links.new(prev, out.inputs['Surface'])
            hn.nodes.remove(em)
        return True

    # albedo via emission: the DIFFUSE colour pass is base colour x (1 - metallic), which turns
    # chrome/metal parts black
    if not bake_input_as_emission("albedo", 'Base Color'):
        bake("albedo", 'DIFFUSE', 4, pass_filter={'COLOR'})
    bake("normal", 'NORMAL', 4, normal_space='TANGENT')
    bake("rough", 'ROUGHNESS', 4)
    bake("ao", 'AO', ao_samples)
    if not (bsdf and bsdf.inputs['Metallic'].links and bake_input_as_emission("metal", 'Metallic')):
        ims["metal"].pixels.foreach_set([0.0, 0.0, 0.0, 1.0] * (res * res))
        times["metal"] = "constant 0"
    for i in ims.values():
        i.filepath_raw = os.path.join(out_dir, i.name + ".png")
        i.file_format = 'PNG'
        i.save()
    return times


def underside_uv_polys(obj, z_thresh=-0.3, uv_name=None):
    """UV polygons of downward faces (for maps_post.py flatten). Returns {'polys': [...]}"""
    me = obj.data
    uvl = (me.uv_layers[uv_name] if uv_name else me.uv_layers.active).data
    return {"polys": [[list(uvl[li].uv) for li in p.loop_indices] for p in me.polygons if p.normal.z < z_thresh]}


def uv_polys_where(obj, predicate, uv_name=None):
    """UV polygons of faces where predicate(polygon) is True (center/normal are object space)."""
    me = obj.data
    uvl = (me.uv_layers[uv_name] if uv_name else me.uv_layers.active).data
    return [[list(uvl[li].uv) for li in p.loop_indices] for p in me.polygons if predicate(p)]


def bake_self(obj, image, typ='DIFFUSE', samples=8, margin=16, **kw):
    """Bake obj onto itself into `image` (uses the active UV layer as target): e.g. colour from a
    projection material read through another UV map, or AO. Adds a target node to each material."""
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    try:
        sc.cycles.device = 'GPU'
    except Exception:
        pass
    sc.cycles.samples = samples
    for s in obj.material_slots:
        nt = s.material.node_tree
        t = nt.nodes.get("bake_target") or nt.nodes.new('ShaderNodeTexImage')
        t.name = "bake_target"
        t.image = image
        nt.nodes.active = t
    activate(obj)
    if typ == 'DIFFUSE' and 'pass_filter' not in kw:
        kw['pass_filter'] = {'COLOR'}
    bpy.ops.object.bake(type=typ, use_selected_to_active=False, margin=margin, use_clear=True, **kw)


def bleed_reference(src_path, out_path, bg=None, tol=24, iters=12):
    """Grow the drawing's colours over the sheet background (dilation), so projected faces whose
    edges land slightly outside the drawn outline don't pick up a light background halo.
    bg: background RGB 0-255 (default: the bottom-left pixel). Uses numpy; returns out_path."""
    import numpy as np
    img = bpy.data.images.load(src_path, check_existing=False)
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[:, :, :3]
    bpy.data.images.remove(img)
    ref = np.array(bg, np.float32) / 255 if bg else a[0, 0].copy()
    known = np.abs(a - ref).sum(axis=2) > tol / 255 * 3
    col = a * known[..., None]
    for _ in range(iters):
        acc = np.zeros_like(col)
        cnt = np.zeros(known.shape, np.float32)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                acc += np.roll(np.roll(col * known[..., None], dy, 0), dx, 1)
                cnt += np.roll(np.roll(known.astype(np.float32), dy, 0), dx, 1)
        grow = (~known) & (cnt > 0)
        col[grow] = acc[grow] / cnt[grow][:, None]
        known = known | grow
    out = bpy.data.images.new(os.path.basename(out_path), w, h, alpha=False)
    rgba = np.dstack([np.where(known[..., None], col, a), np.ones((h, w, 1), np.float32)])
    out.pixels.foreach_set(rgba.astype(np.float32).ravel())
    out.filepath_raw = out_path
    out.file_format = 'PNG'
    out.save()
    bpy.data.images.remove(out)
    return out_path


def normal_from_albedo(albedo_img, out_name, strength=6.0):
    """Tangent-space normal map from albedo luminance (planks, sheets, trims). Uses numpy."""
    import numpy as np
    w, h = albedo_img.size
    a = np.array(albedo_img.pixels[:], dtype=np.float32).reshape(h, w, 4)[:, :, :3]
    lum = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
    k = np.array([1, 4, 6, 4, 1], np.float32)
    k /= k.sum()
    for ax in (0, 1):
        lum = np.apply_along_axis(lambda r: np.convolve(r, k, mode='same'), ax, lum)
    gx = np.zeros_like(lum)
    gy = np.zeros_like(lum)
    gx[:, 1:-1] = (lum[:, 2:] - lum[:, :-2]) * 0.5
    gy[1:-1, :] = (lum[2:, :] - lum[:-2, :]) * 0.5
    nx, ny, nz = -gx * strength, -gy * strength, np.ones_like(lum)
    L = np.sqrt(nx * nx + ny * ny + nz * nz)
    rgba = np.dstack([nx / L * 0.5 + 0.5, ny / L * 0.5 + 0.5, nz / L * 0.5 + 0.5, np.ones_like(lum)])
    img = _new_image(out_name, w, False)
    img.pixels.foreach_set(rgba.astype(np.float32).ravel())
    return img


# --------------------------------------------------------------------------- material / export

def game_material(obj, name, tex_dir, backface=True):
    """Principled material from <tex_dir>/<name>_{albedo,normal,orm}.png (ORM: R=AO, G=rough,
    B=metal), with the glTF occlusion hook. Replaces obj's materials. Returns the material."""
    for k in ("albedo", "normal", "orm"):
        i = bpy.data.images.get(f"{name}_{k}")
        if i:
            bpy.data.images.remove(i)

    def load(k, color):
        i = bpy.data.images.load(os.path.join(tex_dir, f"{name}_{k}.png"))
        i.name = f"{name}_{k}"
        i.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
        return i

    mat = bpy.data.materials.get(name + "_Mat") or bpy.data.materials.new(name + "_Mat")
    mat.use_nodes = True
    mat.use_backface_culling = backface
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    L = nt.links.new
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bs = nt.nodes.new('ShaderNodeBsdfPrincipled')
    L(bs.outputs[0], out.inputs[0])
    ta = nt.nodes.new('ShaderNodeTexImage')
    ta.image = load("albedo", True)
    L(ta.outputs[0], bs.inputs['Base Color'])
    tn = nt.nodes.new('ShaderNodeTexImage')
    tn.image = load("normal", False)
    nm = nt.nodes.new('ShaderNodeNormalMap')
    L(tn.outputs[0], nm.inputs['Color'])
    L(nm.outputs[0], bs.inputs['Normal'])
    to = nt.nodes.new('ShaderNodeTexImage')
    to.image = load("orm", False)
    sp = nt.nodes.new('ShaderNodeSeparateColor')
    L(to.outputs[0], sp.inputs[0])
    L(sp.outputs['Green'], bs.inputs['Roughness'])
    L(sp.outputs['Blue'], bs.inputs['Metallic'])
    g = bpy.data.node_groups.get('glTF Material Output')
    if not g:
        g = bpy.data.node_groups.new('glTF Material Output', 'ShaderNodeTree')
        g.interface.new_socket('Occlusion', in_out='INPUT', socket_type='NodeSocketFloat')
    gn = nt.nodes.new('ShaderNodeGroup')
    gn.node_tree = g
    L(sp.outputs['Red'], gn.inputs['Occlusion'])
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return mat


def export_glb(path, objs, **kw):
    """Export only objs from the active scene as GLB (Y up, embedded images)."""
    deselect_everywhere()
    for o in objs:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    opts = dict(export_format='GLB', use_selection=True, use_active_scene=True,
                export_yup=True, export_image_format='AUTO')
    opts.update(kw)
    bpy.ops.export_scene.gltf(filepath=path, **opts)
    return os.path.getsize(path)


def export_mixamo_fbx(obj, path):
    """Mixamo upload: transforms reset, single mesh, -Z forward / Y up, embedded textures."""
    obj.location = (0, 0, 0)
    obj.rotation_euler = (0, 0, 0)
    obj.scale = (1, 1, 1)
    deselect_everywhere()
    activate(obj)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'MESH'},
                             apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
                             axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE',
                             use_mesh_modifiers=True, add_leaf_bones=False,
                             path_mode='COPY', embed_textures=True, bake_anim=False)
    return os.path.getsize(path)


# --------------------------------------------------------------------------- review renders

def look_at(cam, loc, target):
    cam.location = Vector(loc)
    d = Vector(target) - Vector(loc)
    if abs(d.normalized().z) > 0.999:          # straight down: keep +Y up in the image
        cam.rotation_euler = (0, 0, 0) if d.z < 0 else (math.pi, 0, 0)
    else:
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def review_setup(scene=None, sun_energy=3.0, world_color=(0.55, 0.6, 0.7, 1), name="Review"):
    """Camera + sun + flat world for comparison renders. Returns the camera."""
    sc = scene or bpy.context.scene
    cam = bpy.data.objects.get(name + "Cam")
    if not cam:
        cam = bpy.data.objects.new(name + "Cam", bpy.data.cameras.new(name + "Cam"))
        sc.collection.objects.link(cam)
    sun = bpy.data.objects.get(name + "Sun")
    if not sun:
        sun = bpy.data.objects.new(name + "Sun", bpy.data.lights.new(name + "Sun", 'SUN'))
        sc.collection.objects.link(sun)
    sun.data.energy = sun_energy
    sun.rotation_euler = (math.radians(45), 0, math.radians(30))
    if not sc.world:
        sc.world = bpy.data.worlds.new(name + "World")
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = world_color
    bg.inputs[1].default_value = 0.7
    sc.camera = cam
    return cam


def render_shots(groups, shots, out_prefix, engine='BLENDER_EEVEE', res=(800, 800), cam=None):
    """groups: {tag: [objects shown for this tag]}; shots: {name: dict(loc=, target=,
    ortho=scale or None, lens=35)}. Writes <out_prefix><tag>_<name>.png. Other objects of all
    groups are hidden from render while a tag renders."""
    sc = bpy.context.scene
    cam = cam or review_setup(sc)
    sc.camera = cam
    sc.render.engine = engine
    sc.render.resolution_x, sc.render.resolution_y = res
    every = {o for objs in groups.values() for o in objs}
    files = []
    for tag, objs in groups.items():
        for o in every:
            o.hide_render = o not in objs
        for name, s in shots.items():
            if s.get("ortho"):
                cam.data.type = 'ORTHO'
                cam.data.ortho_scale = s["ortho"]
            else:
                cam.data.type = 'PERSP'
                cam.data.lens = s.get("lens", 35)
                cam.data.sensor_width = 36
            look_at(cam, s["loc"], s["target"])
            sc.render.filepath = f"{out_prefix}{tag}_{name}.png"
            bpy.ops.render.render(write_still=True)
            files.append(sc.render.filepath)
    for o in every:
        o.hide_render = False
    return files


# --------------------------------------------------------------------------- rigs (Mixamo)

def weight_profile(mesh, arm, z_from, z_to, step=0.012, x_half=0.05, front_n=6):
    """Average bone weights of the front-most vertices per height band (rest pose, world space).
    Use to find chin/jaw verts weighted to the neck."""
    prev = arm.data.pose_position
    arm.data.pose_position = 'REST'
    bpy.context.view_layer.update()
    mw = mesh.matrix_world
    names = {g.index: g.name.split(":")[-1] for g in mesh.vertex_groups}
    pts = [(mw @ v.co, v) for v in mesh.data.vertices]
    rows = []
    z = z_from
    while z < z_to:
        sl = sorted([(p, v) for p, v in pts if z <= p.z < z + step and abs(p.x) < x_half], key=lambda t: t[0].y)[:front_n]
        acc = {}
        for p, v in sl:
            for g in v.groups:
                acc[names[g.group]] = acc.get(names[g.group], 0) + g.weight / max(1, len(sl))
        rows.append((round(z, 3), round(sl[0][0].y, 3) if sl else None,
                     {k: round(w, 2) for k, w in sorted(acc.items(), key=lambda x: -x[1]) if w > 0.02}))
        z += step
    arm.data.pose_position = prev
    return rows


def fix_head_weights(mesh, arm, chin_yz, nape_yz, head_center, radius, half_width,
                     blend=(-0.006, 0.016), head_bone="mixamorig:Head"):
    """Move everything above the jaw plane (side view line chin -> nape) inside a sphere around the
    head to 100% head_bone, with a smoothstep over `blend` metres. Fixes Mixamo's 'skewed chin'.
    Returns (changed, fully_head)."""
    prev = arm.data.pose_position
    arm.data.pose_position = 'REST'
    bpy.context.view_layer.update()
    mw = mesh.matrix_world
    head = mesh.vertex_groups[head_bone]
    chin, nape = Vector(chin_yz), Vector(nape_yz)
    d = (nape - chin).normalized()
    n = Vector((-d.y, d.x))                   # (y, z) normal pointing above the jaw
    hc = Vector(head_center)
    lo, hi = blend
    changed = full = 0
    for v in mesh.data.vertices:
        p = mw @ v.co
        if abs(p.x) > half_width or (p - hc).length > radius:
            continue
        s = (Vector((p.y, p.z)) - chin).dot(n)
        if s <= lo:
            continue
        t = max(0.0, min(1.0, (s - lo) / (hi - lo)))
        t = t * t * (3 - 2 * t)
        hw = 0.0
        for g in v.groups:
            if g.group == head.index:
                hw = g.weight
        for g in list(v.groups):
            if g.group != head.index:
                mesh.vertex_groups[g.group].add([v.index], g.weight * (1 - t), 'REPLACE')
        head.add([v.index], hw * (1 - t) + t, 'REPLACE')
        changed += 1
        full += t > 0.999
    for g in mesh.vertex_groups:
        zero = [v.index for v in mesh.data.vertices for x in v.groups if x.group == g.index and x.weight < 1e-4]
        if zero:
            g.remove(zero)
    arm.data.pose_position = prev
    return changed, full


def limit_weights(mesh, limit=4):
    """Keep the strongest `limit` influences per vertex and renormalise (glTF/Godot use 4)."""
    activate(mesh)
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=limit)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
    bpy.ops.object.mode_set(mode='OBJECT')


def stress_pose(arm, ops, prefix="mixamorig:"):
    """Pose bones by world-axis rotations through their joints: ops = [(bone, axis, degrees), ...].
    Mute the action first (arm.animation_data.action = None) and reset afterwards with
    reset_pose(arm)."""
    P = arm.pose.bones
    W = arm.matrix_world.to_3x3()
    for bone, axis, deg in ops:
        pb = P[prefix + bone]
        bpy.context.view_layer.update()
        cur = (W @ pb.matrix.to_3x3()).normalized()
        new = Quaternion(Vector(axis).normalized(), math.radians(deg)).to_matrix() @ cur
        if pb.parent:
            parent_world = (W @ pb.parent.matrix.to_3x3()).normalized()
            rest_rel = pb.parent.bone.matrix_local.to_3x3().inverted() @ pb.bone.matrix_local.to_3x3()
        else:
            parent_world = W
            rest_rel = pb.bone.matrix_local.to_3x3()
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = ((parent_world @ rest_rel).inverted() @ new).to_quaternion()
    bpy.context.view_layer.update()


def reset_pose(arm):
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)


# --------------------------------------------------------------------------- coplanar faces

def _coplanar_groups(bm):
    groups = {}
    for f in bm.faces:
        if f.calc_area() < 1e-8:
            continue
        n = f.normal
        k = max(range(3), key=lambda i: abs(n[i]))
        sgn = 1 if n[k] > 0 else -1
        cn = n * sgn
        groups.setdefault((round(cn.x, 2), round(cn.y, 2), round(cn.z, 2)), []).append(
            (cn.dot(f.verts[0].co), sgn, f, cn))
    return groups


_BARY = [(1/3, 1/3, 1/3), (0.8, 0.1, 0.1), (0.1, 0.8, 0.1), (0.1, 0.1, 0.8),
         (0.45, 0.45, 0.1), (0.1, 0.45, 0.45), (0.45, 0.1, 0.45)]


def coplanar_report(bm, tol=0.003):
    """Pairs of overlapping triangles in one plane (bm must be triangulated).
    same_dir=True -> visible z-fighting; False -> faces glued face-to-face."""
    from mathutils import geometry as G
    out = []
    for items in _coplanar_groups(bm).values():
        items.sort(key=lambda x: x[0])
        for i, (d1, s1, f1, cn) in enumerate(items):
            t = cn.orthogonal().normalized(); b = cn.cross(t)
            P = lambda v: Vector((v.dot(t), v.dot(b)))
            v1 = [P(v.co) for v in f1.verts]
            for d2, s2, f2, _ in items[i + 1:]:
                if d2 - d1 > tol:
                    break
                v2 = [P(v.co) for v in f2.verts]
                p1 = [v1[0] * a + v1[1] * c + v1[2] * e for a, c, e in _BARY]
                p2 = [v2[0] * a + v2[1] * c + v2[2] * e for a, c, e in _BARY]
                if any(G.intersect_point_tri_2d(p, *v2) for p in p1) or \
                   any(G.intersect_point_tri_2d(p, *v1) for p in p2):
                    out.append({"same_dir": s1 == s2, "a": f1.index, "b": f2.index,
                                "at": [round(c, 2) for c in f1.calc_center_median()]})
    return out


def remove_glued(bm, tol=5e-4):
    """Delete triangles fully covered by an opposite-facing coplanar surface (contact faces
    between stacked trim pieces): invisible, but texturers and unwrappers still spend atlas on
    them. bm must be triangulated. Returns the number removed."""
    from mathutils import geometry as G
    kill = []
    for items in _coplanar_groups(bm).values():
        for d1, s1, f1, cn in items:
            t = cn.orthogonal().normalized(); b = cn.cross(t)
            P = lambda v: Vector((v.dot(t), v.dot(b)))
            opp = [[P(v.co) for v in f2.verts] for d2, s2, f2, _ in items
                   if s2 != s1 and abs(d2 - d1) < tol]
            if not opp:
                continue
            v = [P(x.co) for x in f1.verts]
            pts = [v[0] * a + v[1] * c + v[2] * e for a, c, e in _BARY]
            if all(any(G.intersect_point_tri_2d(p, *o) for o in opp) for p in pts):
                kill.append(f1)
    bmesh.ops.delete(bm, geom=kill, context='FACES_ONLY')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    return len(kill)
