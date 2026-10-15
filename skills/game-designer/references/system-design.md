# System design

Use the sections relevant to the requested system. Do not add combat, monetization, or procedural generation merely because this reference mentions them.

## Mechanics and interactions

Define purpose, player action, prerequisites, valid targets, costs, timing, outcomes, feedback, and recovery. Describe interruption, cancellation, failure, and interaction with existing rules where they matter.

Make the decision explicit: available options, information, tradeoffs, and consequences. Look for dominant strategies, compulsory chores, ambiguous feedback, and choices that appear different but resolve identically.

For a stateful feature, a small transition table is often enough:

| Current state | Trigger and conditions | Result | Feedback |
| --- | --- | --- | --- |
| Ready | Player activates; valid target and sufficient energy | Spend energy; enter preparation | Show target and windup |
| Preparation | Interrupted before release | Apply the specified refund rule; enter recovery | Show interruption |
| Preparation | Preparation finishes | Resolve effect once; enter recovery | Communicate hit or miss |
| Recovery | Recovery finishes | Return to Ready if other conditions allow | Restore availability cue |

This is an example, not a mandatory ability model. Define actual refund, cooldown, and timing rules instead of inheriting them accidentally from the example.

## Progression and economy

- Identify the intended arc: new capabilities, mastery, build variety, narrative access, or numerical power. Explain what changes for the player rather than assuming larger numbers are satisfying.
- Map resource sources, sinks, storage limits, conversion rules, unlock gates, and reset or loss conditions. Distinguish renewable flows from one-time rewards.
- State units and assumptions for proposed values: per action, minute, encounter, session, or account. Check a representative path from earning to spending, including repeated purchases and failure.
- Check snowballing, dead ends, grind, runaway accumulation, dominant farming routes, and whether an early mistake prevents recovery. For multiplayer, consider sharing, competition, and incentives to exploit others.
- Use a small numerical model when it resolves a real uncertainty. Label its inputs as assumptions and show how plausible variations change the result. Do not present model output as playtest evidence.
- Address monetization only when it is in scope. Explain its effect on fairness, pacing, and player incentives rather than prescribing a business model.

## Combat, levels, and encounters

For combat, define the decisions created by range, positioning, timing, commitment, enemy intent, and resources. Connect telegraphs and feedback to what the player needs to understand; spectacle alone does not establish clarity.

Give an encounter a purpose, starting conditions, relevant space, enemy or obstacle roles, success/failure rules, and intended pacing. Check combinations: individually fair elements can create unavoidable outcomes together. Allow recovery and counterplay appropriate to the game's goals.

For a level, connect landmarks, routes, gating, traversal, objectives, and teaching order to the intended experience. For procedural content, define generation constraints and validation of traversability or solvability rather than promising variety without limits.

## Co-op and competitive play

Resolve local versus online play and intended player count. Check role interaction, shared information, camera constraints, joining/leaving, failure/revival, reward ownership, and the effect of player-count changes only where relevant. Do not convert a solo feature into a multiplayer system without a project requirement.

## Compact handoff

A useful feature handoff contains the goal, rules, one example of play, exposed tuning values with units, relevant edge cases, and acceptance scenarios. Reference existing systems for shared behavior. Mark unresolved decisions as questions rather than silently choosing irreversible product rules.
