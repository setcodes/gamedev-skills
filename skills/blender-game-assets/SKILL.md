---
name: blender-game-assets
description: "Turn Meshy.ai (or other AI/photogrammetry) models, reference images and concept sheets into game-ready low-poly assets by driving a live Blender over MCP: rebuild props and buildings and bake detail into textures, reduce characters to a budget, prepare Mixamo uploads and fix Mixamo skin weights, or build a model straight from a reference sheet without Meshy; exports GLB for game engines. Use whenever the user mentions Blender, Meshy, low-poly, retopology, polycount, baking, normal maps, game-ready or optimized models, Mixamo or rigging, or asks to make a 3D asset from a picture, even if they don't name the skill."
license: MIT
metadata:
  version: "1.0.0"
---

# Blender Game Assets

Turn heavy AI-generated models into cheap, clean game assets that still look like the original. Meshy-style output looks good but is unusable in a game as-is: 0.5–1.2M triangles, keys/bricks/boards as geometry, one messy mesh. The result must hold up from the game camera (often isometric or top-down) **and** when the user inspects it up close in Blender, from low angles. Answer in the user's language; keep file names and code identifiers as they are.

## 0. Connect to Blender

Requires Blender 5.1+ with the Blender Lab **MCP** add-on (a socket server inside Blender, default `127.0.0.1:9876`) and an MCP bridge registered in the agent. Look for the tools `blender_execute_python` / `blender_scene_info` (Claude Code lists them as `mcp__blender__…`). If they are missing, follow `references/connection.md` — the skill bundles the bridge (`scripts/blender_mcp_stdio.py`).

For long operations (FBX import, bakes, remesh) or when the MCP tools aren't loaded yet, run job files with the bundled client; it has a long timeout and lets you prepend the helper library:

```bash
python3 <skill>/scripts/blender_exec.py <skill>/scripts/bpy_lib.py my_job.py
```

Job scripts run in Blender's main thread and must assign a dict to `result`. Keep job scripts in a temporary/scratch directory, not in the user's asset folders.

## 1. Conventions

Use the user's or project's own layout when one exists; otherwise propose this default once and stick to it:

- Raw input: `<assets>/meshy_raw/<name>/` (zip or folder: FBX/GLB/OBJ + PBR PNGs; a same-named image is the prompt reference). Let the user refer to a model by its name only.
- Output: `<assets>/optimized/<name>/` → `<name>.glb`, `<name>.blend`, `textures/<name>_{albedo,normal,orm}.png`, `compare.png`, `report.md` (in the user's language). Rigged: `<name>_mixamo.fbx`, `mixamo/` (the downloaded file), `<name>_rigged.glb`.
- Copy results into a game project only when asked.
- **One Blender file per model.** Before starting another model: save the current file (into its `optimized/<old>/` folder if unsaved), then `read_homefile(use_empty=True)` — the MCP add-on keeps listening. Never discard work you didn't make: if the open file holds other things, work in a new scene and mention what you saw.
- ORM packing: R = AO, G = Roughness, B = Metallic; glTF occlusion is wired through a `glTF Material Output` node group (`game_material` in `bpy_lib.py`).

## 2. Pick the workflow

| Input | Workflow | Guide |
|---|---|---|
| Meshy prop / building / furniture / weapon | Rebuild clean low-poly from measurements, bake from the Meshy mesh | `references/hard-surface.md` |
| Meshy vehicle (car, truck, cart) | Visible shell → cross-section cage shrinkwrapped onto it → decimate; clean tyres; add missing parts | `references/vehicles.md` |
| Meshy character / creature | Voxel remesh → calm hair → budgeted decimation → body-part seams → bake | `references/characters.md` |
| Character needs a skeleton | Mixamo-ready FBX → user rigs on mixamo.com → fix weights → rigged GLB | `references/mixamo.md` |
| Only a reference image / multi-view sheet | Measure in pixels → block out → project views as texture → bake atlas | `references/from-reference.md` |

Budgets for an isometric/top-down camera (detail into textures, silhouette into geometry):

| Type | Triangles | Texture |
|---|---|---|
| Small prop | 50–500 | 256–512 |
| Medium prop | 500–2 000 | 512–1024 |
| Building | 150–8 000 | 1024–2048 |
| Character / enemy | 8 000–15 000 | 2048 |

## 3. The loop (every workflow)

1. **Inspect**: import into a fresh file/scene, report tris/dims/materials, render 4–6 orthographic views and look at them.
2. **Measure before modelling**: BVH ray casts on the source mesh (`raycaster`) or pixel measurement on a gridded zoom of the reference (`maps_post.py grid`). Pick a scale anchor (door ≈ 2.0–2.1 m, adult ≈ 1.75–1.9 m).
3. **Build / reduce**, then compare silhouettes against the source from the same cameras (flat grey, original vs low-poly side by side).
4. **UV + bake** (or project), post-process maps, build the game material.
5. **Review the way the user will**: lit EEVEE renders from the game angle **and** perspective close-ups from low angles (porch, eaves, gable edges, face, hands, UV seams). Zoom into anything suspicious. Bake artifacts hide in the overview and jump out in close-ups.
6. **Export, then verify by re-importing** in a background Blender (`scripts/bg_verify.py`) or by reading the GLB (`scripts/verify_glb.py`): one mesh, the right material maps, `doubleSided: false`, clean transforms, ground at z = 0.
7. **Deliver**: `compare.png` (original vs result, overview + close-ups), `report.md` (tris before/after, what stayed geometry vs went to textures, decisions, known limits); show the image to the user and summarise.

## 4. Hard-won rules

- Anything that sticks out of the silhouette (barge boards, fascia under a pent roof, brackets, posts) must be **real geometry**. Baked as a projection it streaks and exposes the source's roof underside.
- Downward faces of Meshy buildings often hit backfaces: shrink their UV islands and **flatten their normals** (`maps_post.py flatten`); fill visible soffits with the neighbouring board colour. Don't do this on characters — chins and arm undersides are real.
- Don't keep large hidden faces (full plinth tops under walls, roof end caps behind trim) — they waste atlas space.
- Decimate's vertex group is a **hard mask** ("decimate only these"), not a soft weight; use two masked passes for per-region budgets. Decimate symmetry does nothing on voxel meshes. QuadriFlow at ~12k melts faces and hands.
- `smart_project` on a decimated character gives ~1200 islands — use semantic body-part seams.
- glTF export with `use_selection` also exports objects selected in *other scenes*: use `use_active_scene=True` and deselect everywhere (`export_glb` does both). Object names are global across scenes — renaming to a taken name silently fails.
- Mixamo's auto-rig often gives the chin/jaw ~50% `Neck` weight → "skewed chin" when the head tilts. Fix it before delivering (`fix_head_weights`).
- Long operations can run in `blender -b` (synchronous, keeps the user's UI free); exchange data via `bpy.data.libraries.write` / `libraries.load`.
- Bake albedo from the source's Base Color through an emission (`bake_maps` does): the DIFFUSE colour pass is base × (1 − metallic) and turns chrome black. Split sharp edges before selected-to-active bakes, or shared vertex normals skew the rays at hard corners.
- Meshy panels are often thin open shells (cars): voxel remesh shreds them — cull invisible faces and shrinkwrap a clean cage instead.
- System Python may lack numpy (the post scripts only need Pillow); Blender's Python has numpy.

## Bundled scripts

- `scripts/blender_mcp_stdio.py` — stdio MCP bridge for the Blender add-on (register it in Claude Code or Codex).
- `scripts/blender_exec.py` — run job files in the live Blender (long timeout, concatenates files).
- `scripts/bpy_lib.py` — Blender-side helpers: file hygiene, import/stats, ray casting, block-out (`prism`, `box`, `ledge_ring`, `offset_band`), `unwrap_hard_surface`, `character_lowpoly`, `decimate_to`, `unwrap_character`, `bake_maps`, `bake_self`, `bleed_reference`, `normal_from_albedo`, `underside_uv_polys`, `game_material`, `export_glb`, `export_mixamo_fbx`, review renders, rig helpers (`weight_profile`, `fix_head_weights`, `limit_weights`, `stress_pose`).
- `scripts/maps_post.py` — Pillow post-processing: `pack-orm`, `flatten`, `fill`, `grid` (measuring references), `sheet` (comparison images).
- `scripts/bg_verify.py` — re-import FBX/GLB in background Blender and report.
- `scripts/verify_glb.py` — inspect a GLB (meshes, materials, skins, animations).
- `scripts/selftest_bg.py` — smoke test of `bpy_lib.py` in `blender -b` (run after Blender upgrades).
