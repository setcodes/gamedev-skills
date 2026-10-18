#!/usr/bin/env python3
"""Texture post-processing and reference measuring with PIL (system python3; no numpy needed).

  maps_post.py pack-orm TEX_DIR NAME [--rough R] [--metal M] [--keep]
      <NAME>_ao/_rough/_metal.png -> <NAME>_orm.png (R=AO, G=rough, B=metal). Missing maps use
      constants (--rough 0..1, --metal 0..1, AO=1). Removes the source maps unless --keep.
  maps_post.py flatten NORMAL_PNG POLYS_JSON [--key polys]
      Paint UV polygons flat (128,128,255) — e.g. downward faces that baked garbage.
  maps_post.py fill ALBEDO_PNG POLYS_JSON --key K --sample-key S
      Fill polygons under key K with the median colour of polygons under key S.
  maps_post.py grid IMAGE X0 Y0 X1 Y1 OUT [--scale 2] [--step 20]
      Zoomed crop with a labelled pixel grid for measuring reference views.
  maps_post.py sheet OUT --cols N --cell WxH [--title TEXT] IMG [IMG ...]
      Contact sheet for comparisons (original vs result).

POLYS_JSON: {"polys": [[[u,v],...],...], ...} or blender_exec.py output wrapping it in "result".
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont, ImageStat


def load_polys(path, key):
    d = json.load(open(path))
    if "result" in d and isinstance(d["result"], dict):
        d = d["result"]
    return d.get(key, [])


def px(poly, w, h):
    return [(u * w, (1 - v) * h) for u, v in poly]


def font(size):
    for p in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def cmd_pack_orm(a):
    base = os.path.join(a.tex_dir, a.name)
    size = None
    chans = []
    for k, const in (("ao", 1.0), ("rough", a.rough), ("metal", a.metal)):
        p = f"{base}_{k}.png"
        if os.path.exists(p):
            im = Image.open(p).convert("L")
            size = im.size
            chans.append(im)
        else:
            chans.append(const)
    if size is None:
        sys.exit("no ao/rough/metal maps found")
    chans = [c if isinstance(c, Image.Image) else Image.new("L", size, int(round(c * 255))) for c in chans]
    Image.merge("RGB", chans).save(f"{base}_orm.png")
    if not a.keep:
        for k in ("ao", "rough", "metal"):
            p = f"{base}_{k}.png"
            if os.path.exists(p):
                os.remove(p)
    print(f"{base}_orm.png")


def cmd_flatten(a):
    im = Image.open(a.normal).convert("RGB")
    w, h = im.size
    d = ImageDraw.Draw(im)
    polys = load_polys(a.polys, a.key)
    for p in polys:
        d.polygon(px(p, w, h), fill=(128, 128, 255), outline=(128, 128, 255), width=8)
    im.save(a.normal)
    print(f"flattened {len(polys)} polygons")


def cmd_fill(a):
    im = Image.open(a.albedo).convert("RGB")
    w, h = im.size
    mask = Image.new("L", im.size, 0)
    md = ImageDraw.Draw(mask)
    for p in load_polys(a.polys, a.sample_key):
        md.polygon(px(p, w, h), fill=255)
    col = tuple(int(c) for c in ImageStat.Stat(im, mask).median)
    d = ImageDraw.Draw(im)
    polys = load_polys(a.polys, a.key)
    for p in polys:
        d.polygon(px(p, w, h), fill=col, outline=col, width=8)
    im.save(a.albedo)
    print(f"filled {len(polys)} polygons with {col}")


def cmd_grid(a):
    im = Image.open(a.image).convert("RGB")
    x0, y0, x1, y1, k, st = a.x0, a.y0, a.x1, a.y1, a.scale, a.step
    c = im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * k, (y1 - y0) * k), Image.LANCZOS)
    d = ImageDraw.Draw(c)
    f = font(14)
    for x in range((x0 // st + 1) * st, x1, st):
        X = (x - x0) * k
        major = x % (st * 5) == 0
        d.line([(X, 0), (X, c.size[1])], fill=(255, 0, 0) if major else (255, 150, 150), width=1)
        if major:
            d.text((X + 2, 2), str(x), fill=(255, 0, 0), font=f)
    for y in range((y0 // st + 1) * st, y1, st):
        Y = (y - y0) * k
        major = y % (st * 5) == 0
        d.line([(0, Y), (c.size[0], Y)], fill=(0, 0, 255) if major else (150, 150, 255), width=1)
        if major:
            d.text((2, Y + 2), str(y), fill=(0, 0, 255), font=f)
    c.save(a.out)
    print(a.out)


def cmd_sheet(a):
    cw, ch = (int(v) for v in a.cell.lower().split("x"))
    rows = (len(a.images) + a.cols - 1) // a.cols
    top = 50 if a.title else 0
    s = Image.new("RGB", (cw * a.cols, ch * rows + top), (40, 40, 44))
    if a.title:
        ImageDraw.Draw(s).text((12, 12), a.title, fill=(235, 235, 235), font=font(26))
    for i, p in enumerate(a.images):
        s.paste(Image.open(p).convert("RGB").resize((cw, ch)), ((i % a.cols) * cw, top + (i // a.cols) * ch))
    s.save(a.out)
    print(a.out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack-orm"); p.add_argument("tex_dir"); p.add_argument("name")
    p.add_argument("--rough", type=float, default=0.85); p.add_argument("--metal", type=float, default=0.0)
    p.add_argument("--keep", action="store_true"); p.set_defaults(fn=cmd_pack_orm)
    p = sub.add_parser("flatten"); p.add_argument("normal"); p.add_argument("polys")
    p.add_argument("--key", default="polys"); p.set_defaults(fn=cmd_flatten)
    p = sub.add_parser("fill"); p.add_argument("albedo"); p.add_argument("polys")
    p.add_argument("--key", required=True); p.add_argument("--sample-key", required=True); p.set_defaults(fn=cmd_fill)
    p = sub.add_parser("grid"); p.add_argument("image")
    for n in ("x0", "y0", "x1", "y1"):
        p.add_argument(n, type=int)
    p.add_argument("out"); p.add_argument("--scale", type=int, default=2); p.add_argument("--step", type=int, default=20)
    p.set_defaults(fn=cmd_grid)
    p = sub.add_parser("sheet"); p.add_argument("out"); p.add_argument("images", nargs="+")
    p.add_argument("--cols", type=int, default=3); p.add_argument("--cell", default="600x450"); p.add_argument("--title")
    p.set_defaults(fn=cmd_sheet)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
