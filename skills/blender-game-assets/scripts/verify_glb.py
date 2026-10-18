#!/usr/bin/env python3
"""Print what a GLB contains: meshes + attributes, materials + texture slots, skins, animations,
root nodes, embedded images. Usage: verify_glb.py file.glb"""
import json
import struct
import sys

b = open(sys.argv[1], "rb").read()
n = struct.unpack("<I", b[12:16])[0]
j = json.loads(b[20:20 + n])
out = {
    "meshes": [(m["name"], [sorted(p["attributes"]) for p in m["primitives"]]) for m in j.get("meshes", [])],
    "materials": [{"name": m.get("name"), "slots": sorted(k for k in m if k.endswith("Texture"))
                   + sorted("pbr." + k for k in m.get("pbrMetallicRoughness", {}) if k.endswith("Texture")),
                   "doubleSided": m.get("doubleSided", False)} for m in j.get("materials", [])],
    "images": [i.get("name") for i in j.get("images", [])],
    "skins": [len(s["joints"]) for s in j.get("skins", [])],
    "animations": [(a.get("name"), len(a["channels"])) for a in j.get("animations", [])],
    "root_nodes": [j["nodes"][i].get("name") for i in j["scenes"][j.get("scene", 0)]["nodes"]],
    "first_joints": [j["nodes"][i]["name"] for i in j["skins"][0]["joints"][:4]] if j.get("skins") else [],
}
print(json.dumps(out, indent=1, ensure_ascii=False))
