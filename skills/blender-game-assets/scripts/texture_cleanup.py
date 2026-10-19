#!/usr/bin/env python3
"""Conservative, registered albedo cleanup; requires Pillow and numpy.

UV JSON: {"uv_origin":"bottom-left", "triangles":[[[u,v],...],...]}.
Only albedo is supported. Normal/ORM maps need a different, data-aware pass.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cleanup(source, uv_path, output, strength=0.4, sharpen=0.3):
    source, uv_path, output = map(Path, (source, uv_path, output))
    if output.resolve() == source.resolve() or output.exists():
        raise ValueError('Output must be a new file, separate from the source')
    if not 0 <= strength <= 1 or not 0 <= sharpen <= 1:
        raise ValueError('Strength and sharpen must be between 0 and 1')
    original_hash = digest(source)
    image = Image.open(source)
    image.load()
    if image.mode not in ('RGB', 'RGBA'):
        raise ValueError('Expected RGB/RGBA albedo; do not pass normal/ORM data')
    width, height = image.size
    data = np.asarray(image).copy()
    rgb = data[:, :, :3].astype(np.float32)
    uv = json.loads(uv_path.read_text())
    if uv.get('uv_origin') != 'bottom-left' or not uv.get('triangles'):
        raise ValueError('Expected nonempty bottom-left UV triangle data')
    mask_image = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask_image)
    for triangle in uv['triangles']:
        if len(triangle) != 3 or any(not (-1e-5 <= x <= 1.00001) for p in triangle for x in p):
            raise ValueError('Only a single 0..1 atlas is supported; no tiled UVs')
        draw.polygon([(u * width, (1 - v) * height) for u, v in triangle], fill=255)
    covered = np.asarray(mask_image) > 0
    # Leave four texels at island edges and all padding unchanged. Fade the
    # adjustment inward, so an independently filtered island cannot form a seam.
    inset = mask_image.filter(ImageFilter.MinFilter(9))
    weight = np.asarray(inset.filter(ImageFilter.GaussianBlur(3)), dtype=np.float32) / 255
    weight *= np.asarray(inset) > 0
    valid = rgb.max(axis=2) > 3
    weight *= valid
    if data.shape[2] == 4:
        weight *= data[:, :, 3] / 255

    # Color-aware 5x5 bilateral estimate. No resizing, warping, synthesis or
    # interpolation of atlas coordinates. Neighbors across black gaps are excluded.
    padded = np.pad(rgb, ((2, 2), (2, 2), (0, 0)), mode='edge')
    valid_pad = np.pad(valid, 2, mode='edge')
    total = np.zeros_like(rgb)
    divisor = np.zeros((height, width), np.float32)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            neighbor = padded[2 + dy:2 + dy + height, 2 + dx:2 + dx + width]
            delta = np.mean((neighbor - rgb) ** 2, axis=2)
            spatial = np.exp(-(dx * dx + dy * dy) / (2 * 1.1 ** 2))
            w = spatial * np.exp(-delta / (2 * 9.0 ** 2))
            w *= valid_pad[2 + dy:2 + dy + height, 2 + dx:2 + dx + width]
            total += neighbor * w[:, :, None]
            divisor += w
    estimate = total / np.maximum(divisor[:, :, None], 1e-8)
    clean = rgb + (estimate - rgb) * strength
    luminance = clean @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    low = np.asarray(Image.fromarray(np.rint(luminance).clip(0, 255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.25)), dtype=np.float32)
    detail = luminance - low
    # Suppress sub-threshold fine noise; bound the correction to prevent halos.
    edge = np.sign(detail) * np.maximum(np.abs(detail) - 2.5, 0)
    correction = np.clip(edge * sharpen, -2.0, 2.0)
    candidate = np.clip(clean + correction[:, :, None], 0, 255)
    result = rgb + (candidate - rgb) * weight[:, :, None]
    result = np.rint(result).clip(0, 255).astype('uint8')
    out_data = data.copy()
    out_data[:, :, :3] = result
    output.parent.mkdir(parents=True, exist_ok=True)
    save_options = {'compress_level': 6}
    if image.info.get('icc_profile'):
        save_options['icc_profile'] = image.info['icc_profile']
    Image.fromarray(out_data).save(output, **save_options)
    saved = np.asarray(Image.open(output))
    delta = np.abs(saved[:, :, :3].astype(np.float32) - rgb)
    frozen = weight == 0
    assert saved.shape == data.shape
    assert np.array_equal(saved[frozen], data[frozen]), 'Frozen seam/padding pixels changed'
    if data.shape[2] == 4:
        assert np.array_equal(saved[:, :, 3], data[:, :, 3]), 'Alpha changed'
    assert digest(source) == original_hash, 'Source was modified'
    report = {
        'source': str(source), 'source_sha256': original_hash,
        'output': str(output), 'output_sha256': digest(output),
        'size': [width, height], 'mode': image.mode,
        'strength': strength, 'sharpen': sharpen,
        'uv_sha256': digest(uv_path), 'uv_triangles': len(uv['triangles']),
        'covered_pixels': int(covered.sum()),
        'changed_pixels': int(np.any(saved != data, axis=2).sum()),
        'frozen_seam_and_padding_pixels': int(frozen.sum()),
        'mean_abs_channel_delta_covered': float(delta[covered].mean()),
        'max_abs_channel_delta': float(delta.max()),
        'mean_rgb_delta_covered': (saved[:, :, :3].astype(np.float32) - rgb)[covered].mean(axis=0).tolist(),
        'checks': {'source_unchanged': True, 'dimensions_unchanged': True,
                   'frozen_seam_and_padding_unchanged': True,
                   'alpha_unchanged': True, 'no_coordinate_resampling': True},
        'scope': 'Albedo only; no normal, ORM, mesh, rig or UV edits. On-mesh visual review is still required.'
    }
    output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('uv_json')
    parser.add_argument('output')
    parser.add_argument('--strength', type=float, default=0.4)
    parser.add_argument('--sharpen', type=float, default=0.3)
    args = parser.parse_args()
    print(json.dumps(cleanup(args.source, args.uv_json, args.output,
                             args.strength, args.sharpen), indent=2))
