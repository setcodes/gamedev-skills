# Character delivery and scene preview

User preference, 2026-10-19: final optimized human/monster output is **FBX**, with its texture folder. GLB can be an internal interchange/check artifact; do not substitute it for the requested FBX. The user wants scene lighting/color display corrected when a preview looks dull, not the albedo brightened to compensate.

## Stable preview

Use [../scripts/studio_preview.py](../scripts/studio_preview.py) inside Blender in a dedicated review scene, passing only confirmed optimized mesh objects to `setup_studio(scene, objects)`. It does not change material nodes, mesh or UVs. It refuses an existing lit scene to avoid accidentally stacking rigs; create a separate review scene/file rather than deleting the user's lights.

The saved `neutral-character-studio-v1` preset uses:

- EEVEE, sRGB display, **Khronos PBR Neutral**, Look None, Exposure 0, Gamma 1.
- Blender's neutral `studio.exr` HDRI at strength 0.65, packed into the review BLEND for portability; neutral gray camera background independent of reflections.
- Broad white key/fill/rim area lights. At a 2.5 m character height: 250/90/180 W, sizes 3/4/3 m; positions/size scale with character height and power with height squared.
- Rendered viewport with the scene's world and lights enabled, matching saved render settings. Material Preview with Scene World/Lights disabled uses a separate HDRI and can disagree with a render.

Keep settings fixed for before/after and between comparable characters. Choose a different exposure only for a demonstrated lighting/calibration need and record it; do not tune every asset until its color happens to resemble a reference screenshot. Frame the whole body plus face/hand/seam close-ups. Pack the HDRI and save a companion preview BLEND; lights and cameras do not belong in the deliverable character FBX.

AgX is a photographic view transform that compresses highlights and desaturates highly exposed colors. Khronos PBR Neutral is intended to retain PBR base colors more faithfully under suitable neutral lighting. Neither guarantees identical shaded pixels across Meshy, Blender and a game engine: illumination, reflections, exposure, tone mapping and display must agree. Do not assume Meshy's viewer uses a particular transform or boosted saturation without checking it. Do not call a dim or washed-out render a texture defect until the scene settings have been checked.

For an albedo-only diagnostic, inspect the sRGB image or a temporary unlit review material under Standard. This reveals stored color without scene illumination; it is not the final material. Preserve the original shaders and restore them after the diagnostic.

## FBX package and verification

- Export the optimized mesh plus an existing armature when appropriate, preserving skin weights and animation within the requested scope. Static/unrigged output must not be described as rigged.
- Match the target's axes/units. Current character convention: metres, `-Z` forward / `Y` up in FBX, no added leaf bones. Verify scale and facing by import; do not reset transform values blindly on an imported object.
- Use a portable `textures/` directory with relative file links. Provide albedo and normal plus separate roughness/metallic maps when needed for FBX material wiring. If the source uses ORM, split R/G/B losslessly into AO/roughness/metallic and preserve the channel values. This is packaging, not a visual texture correction. AO may need explicit engine hookup.
- Keep albedo in sRGB and scalar/normal data in Non-Color. Do not rely on automatic FBX PBR interpretation in every engine. Include a brief map legend with the package; textures should remain usable even when an importer needs manual assignment.
- Export only intended objects: no hidden raw/high-poly source, studio lamps, cameras or duplicate meshes. Preserve user files and save a versioned FBX rather than silently replacing the current one.
- Reimport the produced FBX into an empty background scene. Check triangle count, world dimensions/orientation, UV correspondence, expected material maps and resolvable paths. For rigged output, also check bones, skinning and requested animation. Record format conversion limits honestly; a matching triangle count alone is insufficient.

The GLB exact-byte texture replacement helper remains useful when explicitly delivering GLB or testing intermediates. FBX is a different format and its roundtrip must be checked geometrically rather than claimed byte-identical to GLB.
