# Building a model from a reference image only (no Meshy)

Example that worked: the 6-view sheet normally fed to Meshy (front / back / right / left / top / iso, 1536×1024) → wooden house, 162 tris, 2K atlas, almost identical to the sheet from all six views. Takeaway: for buildings and simple props a 3D generator isn't needed; for characters and organic shapes it is (their geometry can't be recovered from flat views).

Store the reference as `meshy_raw/<name>/reference.png`.

## 1. Measure in pixels

```bash
python3 maps_post.py grid reference.png 10 40 510 420 front_grid.png --scale 2 --step 20
```

Read each view's key coordinates off the gridded zooms: wall corners, plinth top, eave, ridge apex, door, windows, annex edges, chimney. Pick a scale anchor (door = 2.0 m → px/m). Orientation of side views: camera at +X sees the front on the **left**; camera at −X sees the front on the **right**; back view is mirrored in X; top view has the front at the bottom.

**AI-generated views disagree** (annex width, chimney position, roof proportions differ 10–40% between views). Build geometry from the most detailed elevations (front + one side), and resolve conflicts by majority (e.g. 3 views put the chimney at the back → back).

## 2. Block out

Same kit as `hard-surface.md` (`prism`, `box`, `ledge_ring`, `offset_band`, `mesh_from_bm`), all in metres with the origin at the centre of the main footprint on the ground. Compare silhouettes with the six views rendered at matching orthographic cameras, pasted next to the reference crops (`maps_post.py sheet`).

## 3. Texture by projection

For every face choose the view that sees it best — `n.z > 0.5` → top, `n.z < -0.5` → a small neutral patch (undersides aren't in the sheet), otherwise the dominant horizontal axis (−Y front, +Y back, ±X right/left) — and set its UVs to the pixel position of its vertices in that view. Calibrate **per part and per view** (main body, annex, chimney, steps) with a linear map from the part's 3D range to its pixel rectangle in that view; this absorbs the inconsistencies between views. Special cases: thin pent roofs and skirts use the front/back view even though their normals point up; step treads map to a strip of the stone in the front view; chimney sides all map to the chimney in the side view where it's fully visible, its top to the top view.

Before projecting, run `bleed_reference(src, out, bg=<sheet background RGB>)`: it grows the drawing's colours over the background so faces whose edges land just outside the drawn outline don't get a light halo (it also fills the gaps between drawn parts, e.g. between keycaps, which makes side strips usable as texture). The material is the (bled) reference image itself through a `UVMap` node pointing at the projection UV layer (`interpolation='Cubic'`). Render all six views next to the reference crops; fix pixel rectangles where background bleeds in (e.g. a too-wide rectangle on a slim view shows light-grey stripes).

## 4. Bake to a clean atlas

New UV layer `atlas` (`unwrap_hard_surface`), set it active + active_render, bake `DIFFUSE` colour from the projection material into a 2048 image (no selected-to-active), bake AO, derive a tangent normal map from albedo luminance with numpy inside Blender (blur 5-tap, central differences, strength ~6), pack ORM with constant roughness (0.85) and metallic 0, remove the projection UV and material, `game_material`, export.

Weapons and props: put the pivot where the game attaches them (grip centre for a hand-held weapon), state the axes in the report (e.g. blade +Z, face −Y in Blender), and render it next to the main character for scale. When re-baking, recreate the target images (`_new_image`) — images whose files were deleted by `pack-orm` fail with "Uninitialized image".

## 5. Limits to tell the user

- Lighting and shadows of the reference are baked in.
- Texel density is capped by the sheet (~55 px/m for a 1536×1024 six-view sheet): soft up close.
- Trims and shutters are flat (normal map only); hidden sides need neutral fills; details drawn on two views can appear twice (e.g. a meter box on a corner).

## Getting better results next time (advice for the user's image generation)

- One large image per view (≥2048 px wide) instead of six on one sheet.
- Ask for strictly orthographic, flat, shadowless lighting ("orthographic elevation, flat even lighting, no shadows, no perspective").
- Better still: separate seamless material tiles (wall boards, roof sheets, plinth stone) + elevations only for unique elements (windows, doors). Then build tiling materials (crisp at any distance) and take only the unique details from the elevations.
- Hybrid on existing sheets: procedural tiling materials for big surfaces coloured from the reference, projected details for windows/doors, protruding trims as geometry.

## Variant: clean geometry only (the user textures it elsewhere, e.g. Meshy)

When the user wants an untextured mesh for an external texturing/unwrapping tool, spend the budget on the detail a texturer needs to "see" instead of projecting: real window/door recesses (~10 cm, `EXACT` boolean of box cutters into the closed wall prism, then delete the bottom and roof-hidden faces and colour the recess backs as glass/door), U-shaped casings, two-step cornices, sills, aprons, sash crosses, corner boards, frieze, barge boards, ridge cap, porch canopy with cheeks and braces, chimney with an inset flue. A small rural house came to ~1.5k tris (one mesh, flat colour materials per zone as hints, no UV).

- Build trims in a wall-local frame (u along the wall, w outward, z up) and drop the face against the wall.
- In the MCP context `bpy.context.view_layer` may belong to another scene, so operators like `modifier_apply` fail. Apply modifiers with `bpy.data.meshes.new_from_object(obj.evaluated_get(scene.view_layers[0].depsgraph))` and render with `bpy.ops.render.render(write_still=True, scene=sc.name)`.
- Before handing the mesh over, triangulate a joined copy and run `remove_glued(bm)` then `coplanar_report(bm)`: zero `same_dir` pairs is required (those z-fight in every viewer), and glued contact faces should be gone. Typical offenders: a threshold or sill whose face lies on the door leaf or plinth front, beam ends flush with a fascia, a ridge cap running through a chimney. The first Meshy pass on such a mesh painted all of them.
- Don't keep the roof underside over the closed attic: split the roof extrusion at the gable walls and keep only the soffits under the overhangs. Otherwise the texturer gives the underside about 20% of the atlas.
- Chimney on a ridge: build its body as a prism whose bottom follows both slopes (no part inside the attic), add a flashing collar, and stop the ridge cap at the collar.
- Meshy texturing (observed): it keeps the geometry exactly and returns its own UVs at roughly uniform 180 px/m on a 4K atlas for a 7 × 8 m house. Common errors: thin trim gets the neighbouring wall colour, the flue interior is painted light, details are painted twice next to modelled ones (door handle), and shadows get baked under the chimney.
- Workbench shadows streak through open (non-manifold) meshes. That is not a geometry bug: check normals with `show_backface_culling` and shadows off.
