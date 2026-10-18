# Connecting an agent to the live Blender

## Pieces

1. **Blender side** — the Blender Lab "MCP" extension (Blender 5.1+). It runs a TCP socket server inside Blender (default `127.0.0.1:9876`). Protocol: JSON + `\0`,
   `{"type":"execute","code":"...","strict_json":false}` → `{"status":"ok","result":{...},"stdout":"..."}`.
   Preferences: `use_autostart` (turn on), host, port. Blender's "Allow Online Access" must be enabled for it to start.
2. **Agent side** — a stdio MCP server that forwards tool calls to that socket. The skill bundles one: `scripts/blender_mcp_stdio.py` (tools `blender_scene_info`, `blender_execute_python`; `--timeout` for long operations, default 600 s).

Register the bridge once per agent (user scope, survives sessions). Use an absolute path to the skill's copy and a Python 3.9+ interpreter:

```bash
# Claude Code
claude mcp add --scope user blender -- python3 /ABS/PATH/blender-game-assets/scripts/blender_mcp_stdio.py --port 9876
claude mcp get blender
```

```toml
# Codex: ~/.codex/config.toml
[mcp_servers.blender]
command = "python3"
args = ["/ABS/PATH/blender-game-assets/scripts/blender_mcp_stdio.py", "--port", "9876"]
startup_timeout_sec = 10
```

Each agent keeps its own MCP registry: a bridge registered in one agent is invisible to the other. New MCP tools appear in a new session; until then use `scripts/blender_exec.py`.

## Check / repair

```bash
lsof -nP -iTCP:9876 -sTCP:LISTEN                       # is Blender listening?
claude mcp get blender                                 # Claude Code registration
grep -A3 'mcp_servers.blender' ~/.codex/config.toml    # Codex registration
```

Add-on location (macOS): `~/Library/Application Support/Blender/<version>/extensions/user_default/mcp`. If Blender isn't running, ask the user to open it — with autostart on, the socket comes up by itself.

## Talking to it

- The first Cycles bake on a 1M-triangle source takes minutes (kernel compile + BVH); later bakes take seconds. Use `blender_exec.py` (30 min timeout) or a bridge with a long `--timeout` for such calls.
- Code runs in Blender's main thread; the UI freezes while it runs — warn the user before long bakes.
- `result` must be a dict (a list is rejected).
- Prefer one job script per step, so steps can be re-run after a fix.
- There is a window: `bpy.context.window.scene = sc` works; edit-mode operators work after making the object active and calling `mode_set`.

## Background Blender (synchronous, UI stays free)

```bash
blender -b in.blend --python job.py -- args      # macOS: /Applications/Blender.app/Contents/MacOS/Blender
```

Pass data in and out with `bpy.data.libraries.write(path, {obj})` and `with bpy.data.libraries.load(path) as (src, dst): dst.objects = [...]`. In `-b` there is no window: guard `bpy.context.window` before switching scenes.
