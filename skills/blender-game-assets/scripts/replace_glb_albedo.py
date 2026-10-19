#!/usr/bin/env python3
"""Replace one embedded PNG albedo in a standard GLB without mesh round-tripping."""
import argparse
import copy
import hashlib
import json
import struct
from pathlib import Path


def parse(path):
    raw = Path(path).read_bytes()
    if len(raw) < 20 or struct.unpack_from('<III', raw) != (0x46546C67, 2, len(raw)):
        raise ValueError('Expected GLB 2.0')
    chunks = {}
    offset = 12
    while offset < len(raw):
        length, kind = struct.unpack_from('<II', raw, offset)
        if kind in chunks or offset + 8 + length > len(raw):
            raise ValueError('Invalid/repeated GLB chunk')
        chunks[kind] = raw[offset+8:offset+8+length]
        offset += 8 + length
    if offset != len(raw) or set(chunks) != {0x4E4F534A, 0x004E4942}:
        raise ValueError('Expected exactly JSON and BIN chunks')
    return json.loads(chunks[0x4E4F534A]), chunks[0x004E4942]


def replace(source, image_path, output, material_index=0):
    source, image_path, output = map(Path, (source, image_path, output))
    if output.resolve() == source.resolve() or output.exists():
        raise ValueError('Output must be a new file')
    doc, binary = parse(source)
    if len(doc.get('buffers', [])) != 1 or 'uri' in doc['buffers'][0]:
        raise ValueError('Expected a single embedded buffer')
    texture = doc['materials'][material_index]['pbrMetallicRoughness']['baseColorTexture']['index']
    target_image = doc['textures'][texture]['source']
    for i, material in enumerate(doc['materials']):
        for role, value in material.items():
            if role.endswith('Texture') and isinstance(value, dict):
                if doc['textures'][value['index']].get('source') == target_image:
                    raise ValueError('Albedo image is shared with another texture role')
        for role, value in material.get('pbrMetallicRoughness', {}).items():
            if role.endswith('Texture') and isinstance(value, dict) and (role != 'baseColorTexture' or i != material_index):
                if doc['textures'][value['index']].get('source') == target_image:
                    raise ValueError('Albedo image is shared with another material/role')
        if material.get('extensions'):
            # This conservative helper intentionally handles simple core materials.
            # An extension may reuse the image through a nonstandard texture role.
            raise ValueError('Material extensions require an explicit reference audit')
    img = doc['images'][target_image]
    view_index = img['bufferView']
    if any(a.get('bufferView') == view_index or a.get('sparse') for a in doc.get('accessors', [])):
        raise ValueError('Image view used by accessor, or sparse accessor unsupported')
    if sum(im.get('bufferView') == view_index for im in doc['images']) != 1:
        raise ValueError('Image bufferView shared with another image')
    view = doc['bufferViews'][view_index]
    start = view.get('byteOffset', 0)
    end = start + view['byteLength']
    if start % 4 or end > len(binary):
        raise ValueError('Invalid image buffer range/alignment')
    old_end_aligned = (end + 3) // 4 * 4
    for i, other in enumerate(doc['bufferViews']):
        if i != view_index:
            a, b = other.get('byteOffset', 0), other.get('byteOffset', 0) + other['byteLength']
            if a < old_end_aligned and b > start:
                raise ValueError('Overlapping bufferViews unsupported')
    png = image_path.read_bytes()
    if png[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Replacement must be PNG')
    from PIL import Image
    import io
    old_image = Image.open(io.BytesIO(binary[start:end]))
    new_image = Image.open(image_path)
    new_image.load()
    if new_image.size != old_image.size:
        raise ValueError('Atlas dimensions must stay exactly unchanged')
    padded = png + b'\x00' * (-len(png) % 4)
    updated = copy.deepcopy(doc)
    delta = len(padded) - (old_end_aligned - start)
    updated['bufferViews'][view_index]['byteLength'] = len(png)
    for i, other in enumerate(updated['bufferViews']):
        if i != view_index and other.get('byteOffset', 0) >= old_end_aligned:
            other['byteOffset'] = other.get('byteOffset', 0) + delta
    updated['images'][target_image]['mimeType'] = 'image/png'
    new_bin = binary[:start] + padded + binary[old_end_aligned:]
    updated['buffers'][0]['byteLength'] = len(new_bin)
    # Every non-albedo bufferView must retain its exact bytes.
    for i, old_view in enumerate(doc['bufferViews']):
        if i == view_index:
            continue
        new_view = updated['bufferViews'][i]
        a, b = old_view.get('byteOffset', 0), new_view.get('byteOffset', 0)
        n = old_view['byteLength']
        assert binary[a:a+n] == new_bin[b:b+n]
    json_bytes = json.dumps(updated, separators=(',', ':'), ensure_ascii=False).encode('utf8')
    json_bytes += b' ' * (-len(json_bytes) % 4)
    result = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(json_bytes) + 8 + len(new_bin))
    result += struct.pack('<II', len(json_bytes), 0x4E4F534A) + json_bytes
    result += struct.pack('<II', len(new_bin), 0x004E4942) + new_bin
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result)
    check, _ = parse(output)
    assert check['meshes'] == doc['meshes'] and check['accessors'] == doc['accessors']
    return {'source': str(source), 'output': str(output), 'size':new_image.size,
            'all_non_albedo_bufferViews_byte_exact':True,
            'mesh_and_accessor_descriptions_exact':True,
            'sha256':hashlib.sha256(result).hexdigest()}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source')
    p.add_argument('albedo')
    p.add_argument('output')
    p.add_argument('--material-index',type=int,default=0)
    a = p.parse_args()
    print(json.dumps(replace(a.source,a.albedo,a.output,a.material_index),indent=2))
