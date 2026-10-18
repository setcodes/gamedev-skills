#!/usr/bin/env python3
"""Minimal stdio MCP bridge for Blender's built-in MCP socket add-on.

The Blender add-on listens on a local TCP socket and accepts null-delimited
JSON execution requests. This process speaks MCP over stdio (Claude Code, Codex,
any MCP client) and forwards tool calls to that local Blender bridge.

Usage: blender_mcp_stdio.py [--host 127.0.0.1] [--port 9876] [--timeout 600]
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
from typing import Any


JSONRPC = "2.0"


TIMEOUT = 600.0


def blender_request(code: str, *, host: str, port: int, strict_json: bool) -> dict[str, Any]:
    payload = {
        "type": "execute",
        "code": code,
        "strict_json": strict_json,
    }
    data = json.dumps(payload).encode("utf-8") + b"\0"

    with socket.create_connection((host, port), timeout=TIMEOUT) as sock:
        sock.sendall(data)
        buf = bytearray()
        while b"\0" not in buf:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buf.extend(chunk)

    raw = bytes(buf).split(b"\0", 1)[0]
    if not raw:
        raise RuntimeError("Blender bridge returned an empty response")
    return json.loads(raw.decode("utf-8"))


def mcp_result(text: str, *, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": text}],
        "isError": is_error,
    }


def tool_scene_info(host: str, port: int) -> dict[str, Any]:
    code = """
import bpy
result = {
    "version": bpy.app.version_string,
    "file": bpy.data.filepath,
    "scene": bpy.context.scene.name,
    "objects": [
        {
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "rotation_euler": list(obj.rotation_euler),
            "scale": list(obj.scale),
        }
        for obj in bpy.context.scene.objects
    ],
}
"""
    response = blender_request(code, host=host, port=port, strict_json=True)
    return mcp_result(json.dumps(response, ensure_ascii=False, indent=2), is_error=response.get("status") != "ok")


def tool_execute_python(args: dict[str, Any], host: str, port: int) -> dict[str, Any]:
    code = args.get("code")
    if not isinstance(code, str) or not code.strip():
        return mcp_result("Argument 'code' must be a non-empty string.", is_error=True)

    strict_json = bool(args.get("strict_json", False))
    response = blender_request(code, host=host, port=port, strict_json=strict_json)
    return mcp_result(json.dumps(response, ensure_ascii=False, indent=2), is_error=response.get("status") != "ok")


def handle_request(request: dict[str, Any], host: str, port: int) -> dict[str, Any] | None:
    request_id = request.get("id")
    method = request.get("method")

    if request_id is None:
        return None

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "blender-stdio-bridge", "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": "blender_scene_info",
                        "description": "Read Blender version, current file, scene name, and objects from the active scene.",
                        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
                    },
                    {
                        "name": "blender_execute_python",
                        "description": (
                            "Execute Python inside the running Blender session. "
                            "Set a JSON-serializable dict named result to return data."
                        ),
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "code": {
                                    "type": "string",
                                    "description": "Python code to execute in Blender. Assign a dict to result.",
                                },
                                "strict_json": {
                                    "type": "boolean",
                                    "description": "Require result to be JSON serializable. Defaults to false.",
                                    "default": False,
                                },
                            },
                            "required": ["code"],
                            "additionalProperties": False,
                        },
                    },
                ]
            }
        elif method == "tools/call":
            params = request.get("params") or {}
            name = params.get("name")
            arguments = params.get("arguments") or {}
            if name == "blender_scene_info":
                result = tool_scene_info(host, port)
            elif name == "blender_execute_python":
                result = tool_execute_python(arguments, host, port)
            else:
                raise ValueError(f"Unknown tool: {name!r}")
        elif method in {"resources/list", "prompts/list"}:
            key = "resources" if method == "resources/list" else "prompts"
            result = {key: []}
        else:
            return {
                "jsonrpc": JSONRPC,
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        return {"jsonrpc": JSONRPC, "id": request_id, "result": result}
    except Exception as exc:
        return {
            "jsonrpc": JSONRPC,
            "id": request_id,
            "error": {"code": -32000, "message": str(exc)},
        }


def write_message(message: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9876)
    parser.add_argument("--timeout", type=float, default=600.0,
                        help="seconds to wait for Blender (bakes and big imports can take minutes)")
    args = parser.parse_args()
    global TIMEOUT
    TIMEOUT = args.timeout

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle_request(request, args.host, args.port)
        if response is not None:
            write_message(response)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
