# Vehicles from a Meshy model

Example that worked: Meshy VAZ-2106 sedan, 1 306 914 tris → 2 622 tris (body, tyres, bumpers, mirrors, lamps) + 2K maps; the missing tail lights added and painted.

Cars are neither buildings (too curved to block out by hand) nor characters (Meshy car panels are **thin open shells**, so voxel remesh shreds them, and the cabin interior + underbody eat any decimation budget). What worked:

## 1. Inspect

Render the six views, find what the generator invented or skipped (here: no tail lights, fake grilles on the rear panel). Find the tyres: rear tyres were separate loose parts, front ones fused with the body. Measure wheel centres/radius from the loose parts or from tyre contact patches (rays from below that hit z ≈ min). Scale from the real car length.

## 2. Visible shell

Copy the source, delete vertices inside the wheel cylinders, `decimate_to(~120k)`, then **cull faces invisible from the game camera**: for each face, cast rays along ~50 directions of the upper hemisphere + horizon (only those with `dot(dir, n) > 0.05`); keep the face if any ray escapes. Cabin behind glass and the underbody disappear (~20 s in Python for 120k faces).

## 3. Clean body

Decimating the visible shell straight to 3k distributes triangles badly (grille and lamps hog them, roof and bonnet sag). Instead:

- **Cage from cross-sections**: ~36 stations along the length; at each, the **same ray family** — horizontal rays from the side at fixed heights and vertical rays from above at fixed widths — with misses clamped to the last valid point, so vertex *i* is "the same ray" at every station (resampling by arc length twists the loft). Flat floor at sill height; mirror the half section. Skip stations through the side mirrors (detect mirrors strictly: beyond the body side *and* above the belt line).
- Subdivide (simple, ×2), **Shrinkwrap (nearest surface) onto the visible shell**, smooth, shrinkwrap again — the stair-steps of the cage land on the real surface.
- Flatten the front/rear panels and the floor, then `decimate_to(body budget)`.

## 4. Parts and bake

- Tyres: clean 14–16-sided cylinders (outer cap only). Bumpers, mirrors, missing lamps: boxes.
- **Split sharp edges (> 50°) before baking**: shared vertices make the cage extrude diagonally and rays hit the tyre sidewall instead of the hubcap.
- `bake_maps` with `cage≈0.02, max_ray≈0.08` (Meshy units). It bakes albedo from the source's Base Color through an emission — the DIFFUSE colour pass would turn chrome black (base × (1 − metallic)).
- Parts the source doesn't have: paint them with a procedural material on a temporary object made of just those faces (same UVs), bake `DIFFUSE` into the existing albedo with `use_clear=False`. Same trick to repaint a panel (body colour sampled as the median albedo under a nearby panel) and add a licence plate.
- `underside_uv_polys` → `maps_post.py flatten` is fine here (the floor is never seen).

## 5. Deliver

Rotate so the bonnet faces −Y, wheels on z = 0, origin at the car centre. Hide the Meshy source from renders before the final shots. Offer a worn variant (edge wear to metal, rust low, dirt in seams) as procedural layers over the same atlas.
