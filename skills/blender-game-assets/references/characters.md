# Characters from a Meshy model

Example that worked: Meshy character 1 109 432 tris → 11 924 tris + 2K maps; face, beard, fingers, sneakers indistinguishable in renders; no visible seams.

Meshy characters arrive **unrigged, A-pose, ~1.9 m, one mesh, centred on X = 0**, often with non-manifold bits and spiky hair. Hand retopology is not practical through code, so the goal is an automatic, budgeted reduction that keeps the face and hands readable, plus clean UVs and a bake.

## Pipeline

```python
lp = character_lowpoly(hp, voxel=0.005, detail_tris=3800, total_tris=12000)
unwrap_character(lp, head_scale=1.7)
times = bake_maps(hp, lp, out_dir, name, res=2048, cage=0.02, max_ray=0.05)
# then: maps_post.py pack-orm; game_material(...); feet to z=0; export_glb(...)
```

What `character_lowpoly` does and why:

1. **Voxel remesh 5 mm** on a copy → one closed manifold mesh (~170k quads). Fixes Meshy's holes and self-intersections; 5 mm keeps fingers and ears.
2. **Smooth the hair** (Smooth modifier, weight ramp over the top ~6% of height). Spiky hair otherwise eats a third of the budget; the look comes back through the normal map.
3. **Two masked collapse passes**: head + hands to `detail_tris`, then the rest to `total_tris`. Region thresholds are fractions of the height (A-pose): head above 0.868·h, hands |x| > 0.232·h below 0.579·h.

Shape check after each change: grey Workbench renders, full body + face close-up + hand close-up, original vs low-poly.

## UVs

`unwrap_character` labels faces by body part (head, torso, arms, hands, legs, feet, soles) and cuts each cylinder on its least visible side (back of head/torso, underside of arms/hands, inner leg, heel), then unwraps with `MINIMUM_STRETCH`, averages island scale, scales head islands ×1.7 and packs. Expect ~25 islands. Check with a `COLOR_GRID` checker render front/back/face.

## Bake

`cage=0.02, max_ray=0.05` (metres). No underside flattening on characters. Review: iso + face + hand + seam close-ups (back of head, under the arm, inner leg, back). Lighting looks identical when it worked.

## Dead ends (don't repeat)

- **QuadriFlow** to ~6k quads: even distribution, face becomes a blob and hands a claw. Fine for bodies, not for game characters at 12k.
- **Decimate with vertex group as "protection"**: the group is a mask of what *gets* decimated; weight 0 = untouched. Inverting it protects the region completely instead of softly.
- **Decimate symmetry** on a voxel mesh: grid isn't mirrored at x = 0 → nothing collapses.
- **smart_project** on the decimated mesh: ~1200 islands (688 of them single triangles). Merging small islands by clearing seams collapses everything into 1–2 unsolvable islands.

## Known limits (state them in the report)

- Triangulated decimation topology, not quad retopo: fine for skinning at game distance, not for close-up facial animation.
- Fingers stay fused if Meshy fused them → Mixamo will create a "mitten" hand (thumb + index only).
