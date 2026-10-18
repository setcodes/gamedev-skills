# Props and buildings from a Meshy model

Example that worked: Meshy house 1 193 906 tris → 234 tris + 2K maps, visually equal from the game camera and clean in close-ups.

## 1. Import and look

```python
objs = import_model(path); hp = [o for o in objs if o.type == 'MESH'][0]
result = {"stats": mesh_stats(hp)}
```

Render front/back/left/right/top/iso orthographic views (Workbench, `color_type='TEXTURE'`) and look at them. Decide what is **silhouette** (geometry) and what is **surface** (texture): windows, doors, boards, bricks, stone, corrugation, keys on a keyboard, small trims → texture.

## 2. Measure with rays

```python
hit = raycaster(hp)                      # object space; Meshy imports have identity transforms
hit((x, -5, z), (0, 1, 0))               # first surface seen from the front
```

Sample profiles: roof height across X at a few Y (`hit((x,y,5),(0,0,-1))`), wall/roof silhouette from the side, gable/door planes from front and back, porch heights with a top-down grid **starting below overhangs** (cast from just under the roof so canopies don't hide steps). Print compact tables, not giant JSON. Typical Meshy units are ~1/7 of real size for buildings — pick a scale from the door (≈2.1 m) and apply it at export.

## 3. Block out

Use `prism(bm, profile2d, 'XZ'|'YZ', lo, hi, drop=...)` — a 2D profile extruded along Y or X — and `box`. Drop faces nobody sees (bottoms, faces against walls, wall tops inside the roof). Typical house kit:

- plinth: `box(..., drop=(0,2))` + `ledge_ring` (only the visible strip around the walls, not a full top face);
- walls + gables: one prism with the gable profile, roof-hidden edges dropped;
- roof: profile with thickness (outer + inner line), end caps dropped when trim covers them;
- **barge boards** along the roof outline on each gable: `offset_band(half_outline, widths)` — deeper on steep segments; run them back to the gable wall so no roof underside shows behind them;
- skirt/pent roofs: sheet + fascia + closed soffit (`[(wall,top),(tip,..),(tip,..),(fascia,..),(fascia,bottom),(wall,bottom)]`), drop the wall face;
- canopy + brackets (triangular prisms), porches as one stepped profile, chimney box + cap.

`mesh_from_bm(bm, name)` merges doubles and sets flat shading. Compare silhouettes against the original from the same ortho cameras (`render_shots`) before UVs.

## 4. UV and bake

```python
unwrap_hard_surface(lp, angle=45, shrink_down=0.35, margin=0.006)
times = bake_maps(hp, lp, out_dir, name, res=2048, cage=0.03, max_ray=0.1)
```

`cage`/`max_ray` are in the mesh's units (0.03/0.1 for Meshy-scale buildings; scale them with the model). Bake before applying the export scale; both objects must be visible and renderable.

Post-process outside Blender:

```bash
python3 blender_exec.py bpy_lib.py dump_undersides.py > polys.json    # underside_uv_polys(lp)
python3 maps_post.py flatten  textures/<name>_normal.png polys.json --key polys
python3 maps_post.py fill     textures/<name>_albedo.png polys.json --key barge_under --sample-key barge_front
python3 maps_post.py pack-orm textures <name>
```

Then `game_material(lp, name, tex_dir)` (albedo + normal + ORM, backface culling, glTF occlusion).

## 5. Review — where artifacts hide

From the iso view everything looks fine; close-ups find:

- streaks where projected trim sits at a grazing angle → make that trim geometry;
- red/garbage roof underside visible under gable overhangs → barge boards deeper and back to the wall, fill their underside colour;
- dark band under a skirt roof that is only a shadow → check with an unlit Workbench render (`light='FLAT'`, `color_type='TEXTURE'`) before "fixing" it;
- yellow/green blotches in the normal map → faces whose rays hit backfaces; find them by sampling the normal image per face (blue < 0.75) and flatten.

## 6. Export

Scale/offset a copy into metres with the pivot on the ground (centre of the wall footprint), `export_glb(path, [obj])`, save the `.blend` (`libraries.write(path, {scene})` if the open file holds other work, or `save_as_mainfile` when it is the model's own file). Verify with `verify_glb.py`: one mesh, `normalTexture`, `occlusionTexture`, `metallicRoughnessTexture` (same image as occlusion), `doubleSided: false`.
