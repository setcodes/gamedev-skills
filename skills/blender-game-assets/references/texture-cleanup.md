# Texture cleanup on optimized characters

Use this mode when the user asks to remove texture artifacts, improve texture clarity, or polish materials on an already optimized human or monster. This is a texture task; do not run remesh, decimation, automatic unwrap or the raw-to-game pipeline.

Recorded user choice, 2026-10-19: use precise local Python pixel processing for this saved cleanup workflow, preserving atlas coordinates and dimensions. Prefer that method for existing game UV atlases; do not require a new generative trial for every asset. This preference does not authorize processing unrelated assets, changing the mesh, or using paid external APIs.


Final character delivery is FBX + textures per [preview-and-fbx.md](preview-and-fbx.md); GLB helper instructions below concern optional intermediates or explicitly requested GLB output. When the complaint is scene brightness/saturation, inspect the lighting and view transform first; do not recolor albedo to compensate.

## Scope and preservation

- For this user's character library, use only optimized versions: normally `models/<id>/game/`, or a confirmed `optimized/` directory. Announce the model IDs and versions found. Do not edit raw sources or a hidden high-poly object bundled into a game `.blend`. If no optimized version exists, report that and ask which asset to use; do not silently create one.
- Preserve mesh topology, silhouette, UV coordinates, rig, weights, material assignments and texture layout. Preserve identity, palette and intentional scars, veins, scales and wear. Changes to any of these require separate task authority.
- Work on versioned copies in the existing model's `game/` layout. Keep the current working `.blend` and original textures intact. Save a source manifest with paths and hashes, and make the candidate independently reviewable before replacing an existing model or updating the catalogue.
- If the request is only to inspect or explain, stop after assessment. Authorization to update this skill does not authorize a batch edit of the asset library. Use one representative authorized model first and state which other assets remain unprocessed.

## Diagnose before editing

Inspect albedo, tangent-space normal and ORM separately, then inspect them on the optimized mesh. Check front/back, face, hands and seams with identical lighting and cameras. Separate texture noise or baked-in lighting from UV stretch, geometric faceting, normal-map errors and texture filtering. Do not call a vivid color in a normal map a defect without checking it on the model. Black atlas background is not a defect by itself.

Keep the existing resolution initially (usually 2K). Diagnose loss of detail before suggesting 4K; an upscale does not recover missing source detail. Prioritize faces, eyes, hands, silhouette-adjacent details and large readable material boundaries.

## Choose the least disruptive correction

- Albedo: remove isolated stains, generation noise and smears locally; keep broad color transitions and intentional surface texture. Sharpen selected edges conservatively after cleanup. Avoid global sharpening, halos, crunchy pores or blanket smoothing.
- Human clothing follows this project's established preference: coherent solid garment colors, matte fabric and readable folds; remove random mottling, marbling and faceted color patches. Do not apply smooth-cloth rules to monster skin, scales or armor.
- Normals: preserve tangent-space encoding, orientation and unit-length vectors. Diagnose cage/projection misses and seam discontinuities on the mesh. Do not sharpen normals like a color photograph, generate them blindly from albedo, or flatten broad character undersides. Under optimized-only scope, do not rebake from hidden/raw high-poly geometry without separate authorization.
- ORM: maintain R=AO, G=roughness, B=metallic. Treat channels as data. Clean roughness/metalness according to visible material regions without adding noisy gloss or treating all dark armor as metal. Do not add painted lighting or AO to albedo as a substitute for correct shading.
- Keep albedo in sRGB and normal/ORM in Non-Color. Check actual material connections and normal strength before changing pixels.

For raster image edits, follow the available image-editing tool requirements; when using ImageGen, inspect the input first and lock exact dimensions, UV island positions, outlines, orientation, spacing and atlas padding in the prompt. Use generation only as a candidate. Check its registration against the original atlas: matching image dimensions alone is insufficient. Reject any island movement, feature drift, repacking, text, new decoration or changed identity. Never use generative output directly as normal/ORM data. Respect any need for explicit authorization before using a different image-editing backend.

## Reusable deterministic helpers

For conservative **albedo** cleanup use [../scripts/texture_cleanup.py](../scripts/texture_cleanup.py) (Pillow and numpy). It performs color-aware 5x5 denoising and bounded luminance sharpening without coordinate resampling. It freezes four texels inside UV borders plus all exterior padding and fades the correction inward. Therefore it intentionally cannot repair an existing UV seam or a large smeared/generated patch. Do not describe a mild filtering pass as complete artifact repair. Choose parameters from actual on-mesh comparisons rather than repeatedly increasing sharpening.

Export UV triangles from the confirmed optimized mesh only, e.g. in Blender:

```python
import bpy, json
from pathlib import Path
ob = bpy.data.objects[optimized_object_name]
ob.data.calc_loop_triangles()
uv = ob.data.uv_layers.active.data
triangles = [[[float(uv[i].uv.x), float(uv[i].uv.y)] for i in t.loops]
             for t in ob.data.loop_triangles]
Path(uv_json_path).write_text(json.dumps({
    'uv_origin': 'bottom-left', 'triangles': triangles, 'object': ob.name
}))
```

Run with an available Python containing Pillow and numpy; output paths must be new:

```bash
python3 scripts/texture_cleanup.py albedo.png source_uv.json albedo_clean_v1.png --strength 0.4 --sharpen 0.3
```

The adjacent output JSON records hashes, dimensions, frozen pixels, actual pixel deltas and checks. Large changes in detail or color still require visual rejection even when these checks pass. This helper accepts one non-tiled 0..1 RGB/RGBA atlas, not UDIMs or normal/ORM data.

For a texture-only standard embedded GLB, prefer [../scripts/replace_glb_albedo.py](../scripts/replace_glb_albedo.py):

```bash
python3 scripts/replace_glb_albedo.py source.glb albedo_clean_v1.png model_texture_clean_v1.glb
```

It replaces the existing embedded albedo image and updates buffer offsets, keeping every other bufferView byte-exact. It refuses different atlas dimensions, source overwrite, shared image roles, sparse accessors, unsupported material extensions and overlapping bufferViews; inspect those cases before choosing another method. It requires Pillow. A Blender import/export roundtrip can change vertex normal numbers even for a texture-only edit. Compare all non-albedo data before accepting an export; visual similarity and unchanged triangle count alone are insufficient.

## Acceptance and delivery

Compare the original and candidate on the same optimized mesh under the same cameras, lights, exposure, filtering and resolution. Review both game distance and close-ups; include a second light direction for changes affecting normals or roughness. Check UV borders and padding under minification so cleanup does not introduce seams. If a candidate fails, keep the source and record the failure; do not describe it as an improvement.

For an accepted texture pass, save the versioned texture(s), a candidate `.blend`/GLB when requested or needed to review the asset, a before/after image and a concise report. Record actual changes, resolution, untouched data, verification and remaining defects. Verify exported texture references and mesh/UV/rig invariants before calling an export ready. Distinguish reduced file size or VRAM use from improved appearance; measure either before claiming optimization. Update a shared catalogue only when an accepted output is being registered, following its existing build/check workflow.
