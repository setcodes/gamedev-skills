# Mixamo: prepare, rig on the website, fix, deliver

## 1. Prepare the upload

Requirements: single mesh, no armature, A- or T-pose, faces −Y in Blender, feet on z = 0, origin between the feet, transforms applied (location/rotation 0, scale 1). Check the mesh: one connected part, 0 non-manifold edges, 0 zero-area faces. **Reset the object transform** — the user may have moved it in the viewport.

```python
export_mixamo_fbx(obj, out_dir + f"{name}_mixamo.fbx")   # -Z fwd / Y up, embedded albedo+normal
```

Verify by re-import (`bg_verify.py`): height, zmin = 0, loc/rot/scale clean, nose at −Y, images packed. ORM does not survive FBX — it is re-attached after rigging. Give the FBX to the user as a file they can download.

Tell the user (in their language): Upload Character → markers chin / wrists / elbows / knees / groin → **Skeleton LOD: Standard (65)** (or whatever their existing characters use) → download **FBX Binary, With Skin**; extra animations later **Without Skin**. Ask them to put the file into `optimized/<name>/` or tell you its path; copy it into `optimized/<name>/mixamo/`.

## 2. Inspect the rigged FBX

Import into a separate scene of the model's file. Expect `mixamorig:*` bones (41 if fingers were fused: thumb + index only; 65 otherwise), one action `Armature|mixamo.com|Layer0`, mesh parented to the armature with an Armature modifier. Check that the game's rig loader tolerates the reduced set (e.g. matches bones by the suffix after `mixamorig:`/`mixamorig_` and skips missing ones).

## 3. Diagnose — the skewed chin

Render the face in `pose_position='REST'` and at several frames of the idle. If the face is fine at rest but the jaw/beard stretches when the head tilts, it's weights:

```python
rows = weight_profile(mesh, arm, z_from, z_to, step=0.012)   # front-most verts per height band
```

Typical Mixamo result: chin and jaw ≈ 50% `Neck`, mouth/nose 15–25% `Neck`, because the chin sits below the Head joint.

## 4. Fix

```python
fix_head_weights(mesh, arm,
    chin_yz=(-0.150, 1.632), nape_yz=(0.070, 1.668),     # jaw plane in side view (y, z), metres
    head_center=(0.0, -0.035, 1.75), radius=0.17, half_width=0.095)
limit_weights(mesh, 4)                                     # glTF / Godot use 4 influences
```

Everything above the jaw plane (face, ears, hair) → 100% Head with a ~2 cm smoothstep; neck and hood untouched. Read chin/nape/centre from the weight profile and rest-pose renders of *this* character — the numbers above are from one 1.9 m Meshy character. Re-render the idle frames: chin must stay compact.

Stress test before delivering (`stress_pose`): arms forward + elbows bent, leg forward + knee bent, spine twist + head turn; look at shoulders, elbows, knees, hips, neck.

### Crowd enemies: strip the fingers

A full Mixamo rig has 65 bones (73 with `_End` leaves in some exports), and about half are fingers. A top-down camera never shows fingers, but every bone is a track in every clip and is updated every frame for every enemy. Measured: ~10 µs of animation per visible enemy with fingers; removing them roughly halves that. For a crowd/horde enemy (see the budget table in `SKILL.md`):

1. Add each finger's vertex-group weight into its hand group (`*Hand`), then delete the finger groups.
2. Delete the finger bones (`*Thumb*`, `*Index*`, `*Middle*`, `*Ring*`, `*Pinky*`) and `*_End` leaf bones in Edit Mode. Keep the hands, because weapons attach to them.
3. `limit_weights(mesh, 4)` again, re-render the idle and stress poses, and check that the hands do not tear.
4. Re-export every clip against the reduced armature. Animation tracks for missing bones must be dropped (or the engine-side loader must skip them).

Heroes, elites and bosses keep the full rig.

## 5. Deliver

- Replace Mixamo's material with the full game material (`game_material`), delete its orphan copies.
- Rename: armature `<name>_Rig`, mesh `<name>` (rename the static copy first — names are global), action `mixamo_com` (Mixamo's default clip name, which engine-side loaders commonly key on — check the project).
- `export_glb(path, [arm, mesh], export_skins=True, export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True)` → `<name>_rigged.glb`; also `<name>_rigged.fbx` with the fixed weights.
- Verify: 1 skin, joints = bone count, one animation `mixamo_com`, one mesh with `JOINTS_0`/`WEIGHTS_0`; re-import in `-b` and render idle frames of the face.
- The user does **not** need to re-upload to Mixamo: animations downloaded *Without Skin* apply to the fixed model. Only Mixamo's own preview keeps the old weights (uploading `<name>_rigged.fbx` there skips the auto-rigger and keeps ours).
