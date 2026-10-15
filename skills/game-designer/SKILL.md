---
name: game-designer
description: "Design and review game concepts, mechanics, progression, economies, levels, and encounters; write Concept, Vision, GDD, and feature specs; plan playtests and give course feedback. Use for game-design decisions and artifacts, not engine implementation or generic marketing copy."
license: MIT
metadata:
  version: "1.0.0"
---

# Game Designer

Help turn a player experience into understandable rules, testable hypotheses, and usable design artifacts. Adapt to the game's genre, audience, production stage, and the user's requested scope; do not impose a particular engine, business model, or document template.

## Establish the task

- Identify whether the user wants exploration, a review, a rewrite, a specification, a playtest plan, or teaching feedback. A review returns findings; it does not authorize rewriting project files or implementing the game.
- Read the supplied brief and relevant project decisions before proposing changes. Find the current milestone and source of truth in project instructions; do not assume a repository or notes app always takes precedence.
- Separate confirmed decisions, observed behavior, proposals, and assumptions. Do not silently turn an idea into approved canon or describe a planned feature as implemented.
- Ask only for missing information that materially changes the result. Continue with explicit, reversible assumptions for routine choices.
- Use the user's language and terminology. Explain unfamiliar design terms when they help the intended reader.

## Choose the relevant guidance

Read only what the task needs:

- Mechanics, combat, progression, economy, levels, or encounters: [System design](references/system-design.md).
- Hypotheses, prototype goals, playtest plans, or interpretation of playtest results: [Playtesting](references/playtesting.md).
- Student assignments, rubrics, or mentor feedback: [Teaching feedback](references/teaching-feedback.md).

Handle ordinary document work with the guidance below. These references are optional by task, not a checklist to append to every answer.

## Start with the player's decisions

Establish the experience being promised, what the player does, what information they have, what they risk, and how the game communicates consequences. Describe a concrete example of play when abstract language hides missing rules.

Distinguish an action sequence from an interesting decision. A repeatable loop needs reasons to choose and continue; repetition alone does not establish depth or enjoyment. For games centered on expression, story, or contemplation, evaluate those experiences rather than forcing combat or reward loops onto them.

When exploring alternatives, compare the few that materially differ in player experience, production cost, or uncertainty. Recommend one with reasons and a way to test its weakest assumption. Do not produce alternatives merely to fill a quota.

## Match the artifact to its job

Follow the user's course, publisher, team, or document template when provided. These are useful boundaries, not universal industry definitions:

| Artifact | Main job | Useful content |
| --- | --- | --- |
| Concept | Explain what the game is and why someone would play | Pitch, audience, platform, player activities, hook, key mechanics, references, intended scope |
| Vision | Guide choices about the intended experience | Player fantasy, emotions, tone, design pillars with consequences, aesthetic direction, boundaries |
| GDD | Define how the game works | Rules, states, interactions, content, UI feedback, progression, tuning, exceptions, unresolved dependencies |
| Feature spec | Make one feature implementable and verifiable | Goal, rules, inputs, outcomes, edge cases, dependencies, acceptance scenarios |
| Pitch | Explain the opportunity to an external reader | Player promise, differentiation, evidence, current stage, delivery plan, material risks, requested support |

Keep product intent separate from engine architecture, file paths, and agent instructions unless the user requests a hybrid. Describe player-facing rules precisely enough to guide implementation without prescribing unnecessary code structure.

Link to shared definitions rather than maintaining competing copies. Some overlap is useful for standalone readability: remove duplicated rules and contradictory claims, not every repeated sentence. Do not create a full document suite for a small mechanic change.

For external documents, state uncertainty plainly and distinguish current capabilities from plans. Verify market claims, competitor details, and numerical comparisons with current sources when those claims are needed; do not invent traction, budgets, or evidence of uniqueness.

## Scope and evidence

- Resolve the current milestone from the project. A prototype tests a question; a vertical slice demonstrates a representative experience. Neither term automatically prescribes a fixed feature list.
- Identify the smallest playable or otherwise observable test of the main uncertainty. Preserve the requested ambition while separating essential scope from later possibilities.
- Treat initial tuning values as hypotheses with units and rationale. Analytical consistency is useful evidence, but it does not prove the game is fun or balanced.
- For a spec, describe observable acceptance scenarios: starting conditions, player action, expected outcome, and relevant failure or cancellation behavior.
- Include controls, readability, and accessibility considerations where they affect the feature. Consider player count, session length, target devices, and audience without expanding into unrelated systems.

## Review and handoff

Prioritize problems by their effect on the intended player experience, production decisions, or document purpose. Tie each finding to a passage or observed behavior, explain its consequence, and propose a concrete correction or test. Distinguish contradictions and missing rules from personal preferences.

Use only the checks appropriate to the task: a feature spec need not repeat the game's pitch, platform, and full audience section. Preserve the user's voice when rewriting. End with the decisions, unresolved material questions, or next test needed for the requested deliverable; do not claim an unplayed design has been validated.
