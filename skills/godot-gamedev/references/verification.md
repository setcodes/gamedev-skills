# Godot verification

Choose checks for the project's engine version, language, existing tooling, and the changed behavior. The examples below illustrate common Godot 4 command patterns; verify support with the selected editor binary's `--help`. Replace example paths with real project resources. These are not commands to run blindly or a required sequence.

## Command checks and their limits

```sh
godot --version
godot --help
godot --headless --path /path/to/project --import
godot --headless --path /path/to/project --script res://actors/player.gd --check-only
```

`--import` runs the editor import process and exits; it can update generated project files and caches. Use it only in an authorized working copy, with the intended engine version. Do not open an untrusted project just to inspect it: imports can involve editor plugins and tool scripts.

`--check-only` with `--script` checks that GDScript and relevant dependencies parse; it does not execute gameplay, validate every script in the project, or build C# code. Use the project's .NET build workflow for C# and its existing runner for project tests. Godot's engine `--test` flag is not a general runner for a game's test suite.

For a bounded smoke run where the project's version supports these options:

```sh
godot --headless --path /path/to/project res://tests/combat_smoke.tscn --quit-after 120
```

`--quit-after` counts iterations, not seconds. A run reaching its frame limit only establishes that it reached that point without the reported failures; require assertions or observable output for a behavioral test. Headless execution cannot establish visual readability, audio quality, or game feel. Use the existing project runner and scene if available rather than creating an empty smoke scene merely to pass a command.

See the official [command-line reference](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html); select the project's version before applying flags. The official [scene organization guide](https://docs.godotengine.org/en/stable/tutorials/best_practices/scene_organization.html) explains scene dependencies and reuse. For shared data, consult the version-matched [Resource reference](https://docs.godotengine.org/en/stable/classes/class_resource.html), including duplication and local-to-scene behavior.

## Choose an observable scenario

- A cooldown change: activation, repeated input, cancellation if supported, expiry, and relevant pause behavior.
- Shared-resource state: instantiate two consumers; mutate one; verify the other retains the intended independent state.
- A scene transition: enter, exit, return, and check that state and signal subscriptions have the intended lifetime.
- Local co-op: exercise two actual input owners and independent state, plus any changed shared camera or rewards.
- Online play: exercise the changed behavior across the required authority and peers; a one-instance test is insufficient.

Adapt these examples to the requested feature. Describe the tested build, setup, action, and outcome in the handoff. Distinguish static inspection, import/parse checks, automated behavioral checks, and a manual play session rather than calling them all "tested."
