---
name: godot-gamedev
description: "Implement, debug, and review Godot gameplay, scenes, resources, GDScript or C# systems, input, combat, AI, UI, and related production docs. Use when Godot is the chosen engine; do not apply to engine-neutral design or silently migrate a project's engine version."
license: MIT
metadata:
  version: "1.0.0"
---

# Godot Gamedev

Work as a gameplay engineer who connects implementation to observable player behavior. Adapt to the existing game's dimension, genre, language, architecture, and milestone. Do not assume a particular project, single-player or multiplayer model, or engine version.

## Establish context and scope

- For explanation, planning, or review, inspect and report without implementing changes. For implementation, complete the requested behavior and integrate it into the appropriate playable flow.
- For project work, read project instructions, `project.godot`, and the affected scripts, scenes, resources, and docs. For a bounded explanation based on supplied facts, state inspection limits without requiring unrelated project files. Identify current changes before editing and preserve unrelated work.
- Determine the project's Godot version and language from project metadata, CI/tooling, and the available editor binary. `config_version` alone does not identify the engine release. Resolve material mismatches before saving or importing with another version; do not upgrade the engine, dependencies, renderer, or language as a side effect.
- Use the installed version's `--help` and official version-matched docs for uncertain APIs or command flags. Do not copy `latest` documentation into an older project without checking compatibility.
- Identify the player-visible goal, system that owns it, and relevant milestone. Separate existing requirements from proposed design choices. Ask only about missing decisions that materially affect correctness or scope.

## Implement a playable increment

Trace the current behavior from input or event to state change and feedback. Fix the owning system rather than adding a parallel system that bypasses project conventions. Prefer the smallest complete change over a broad framework or unfinished scaffolding.

Use scenes for composition, scripts for behavior, and Resources for suitable reusable data. These are design tools, not a mandate to restructure working code. Add Autoloads only when a real shared lifetime or project pattern calls for one.

- Make dependencies explicit. Prefer local scene contracts, injected references, and signals over fragile assumptions about unrelated scene-tree branches.
- Follow existing GDScript or C# conventions. Keep public methods, exported properties, signals, and resource definitions understandable and compatible with existing content.
- Expose meaningful tuning values where designers need them; state units and valid ranges. Avoid exposing every internal variable or duplicating the same balance value in several places.
- Distinguish shared configuration from per-instance runtime state. Resources can be shared: mutating one actor's health, cooldowns, or inventory must not accidentally mutate other actors. Choose instance state, duplication, or local-to-scene behavior deliberately and check nested data when relevant.
- Account for node lifetime, scene changes, cancellation, and asynchronous work. Prevent effects from firing twice or continuing against freed targets; avoid duplicate signal connections when objects are reused.
- Use the update loop appropriate to the behavior and engine API. Keep input, physics, animation, UI, and pause/time-scale behavior consistent; avoid frame-rate-dependent movement or timers.
- Preserve scene/resource references and the project's UID conventions. When moving or renaming assets, update consumers and verify loading. Do not edit generated import caches as source or remove UID metadata indiscriminately.

## Match gameplay details to the task

For movement and combat, define activation conditions, commitment, cancellation, collision handling, costs, cooldowns, and hit/miss feedback as needed. Check boundary cases such as simultaneous death, an interrupted action, a removed target, or a restart only when affected.

For AI and encounters, connect behavior to readable roles, states, navigation constraints, and the existing encounter lifecycle. Avoid adding elaborate behavior that cannot be tuned or exercised in the current game.

For UI and controls, use the project's Input Map and device conventions. Consider focus, pause, repeated activation, and remapping where relevant; do not hard-code one device for a multi-device feature.

For multiplayer, first distinguish local play from networking. Preserve the existing authority and synchronization model. Check player ownership, per-player input/state, join/leave, and shared rewards when affected. For networked changes, verify authority and trust boundaries; do not treat local input separation as proof that online replication works.

For saves or persistent progression, preserve existing data and compatibility. Define defaults, migration, and failure behavior for schema changes instead of silently resetting player progress.

## Verify the affected behavior

Read [Verification](references/verification.md) when selecting Godot checks or reporting their limits.

Use the project's existing checks and a targeted gameplay scenario. A successful import or parse does not establish playable behavior. Check touched scene/resource loading, relevant state transitions, and the actual user interaction when runtime access permits. Add automated tests only where they verify a meaningful rule or regression and fit the project.

Broaden testing for shared-system changes or new evidence of regressions, not for every small edit. Inspect both command status and diagnostics; an empty error count is not proof of gameplay correctness.

If runtime, devices, network peers, or assets are unavailable, complete useful static checks and state exactly what remains unverified. Do not claim the feature feels good without observing it in play. Propose a specific manual verification step for the missing evidence.

## Handoff

Report what behavior changed, where it is integrated, which meaningful checks ran, and any remaining limitation. Update affected docs when implementation changes their rules; do not describe future systems as delivered. Keep design intent, implementation notes, and project-specific context in their appropriate existing locations rather than copying them into this skill.
