---
name: build-learning-simulation
description: Build a source-grounded interactive simulation that helps a learner understand a complex process, system, or causal model. Use only when a learner explicitly asks for a simulation, explorable visual model, game-like walkthrough, puzzle, or interactive explanation; never select or propose this skill as a default learning-track activity.
---

# Build Learning Simulation

Create a learner-facing model, not an authoritative illustration. This is an
optional learning format: use it only when the learner explicitly authorizes a
simulation for the current topic. Do not select, recommend, or build one as a
default learning-track activity. Keep subject content and generated artifacts
in the explicitly authorized learning workspace or learner-owned project; keep
this plugin material-agnostic.

Resolve `<plugin-root>` as the nearest ancestor of this `SKILL.md` that contains
the portable root `plugin.json`. Do not assume the process working directory.

## Workflow

1. Confirm the learner explicitly authorized a simulation for the current
   topic. Resolve the learner's target performance, prior knowledge, available
   time, source mode, and exact artifact destination. Do not write to a workspace
   or repository until the learner authorizes its path.
2. Read [references/simulation-contract.md](references/simulation-contract.md).
3. Build a compact concept map. For each scene or interaction, record the claim,
   causal relationship, source, verification date, and any deliberate
   simplification.
4. Ask the learner to review the map and the source ledger before implementation
   when factual precision materially matters. Correct unsupported or conflicting
   claims; preserve unresolved points as visible uncertainty.
5. Choose the smallest useful representation:
   - a step-through process for ordered transformations;
   - a system map for components, dependencies, and feedback loops;
   - a scenario simulator for decisions, constraints, and consequences;
   - a puzzle or prediction checkpoint for relationships that must be recalled.
6. Build an accessible interactive artifact. Include pause, restart, step,
   reduced-motion, keyboard, and small-screen support where the runtime permits.
   Let learners inspect the claim and source behind each meaningful scene.
7. Add retrieval before explanation. At high-value transitions, ask the learner
   to predict what happens next or explain why; reveal the model's explanation
   only after their response.
8. Create or update Learning Loop cards for durable causal rules. Keep card
   reference answers and source links separate from the simulation copy.
9. Validate the artifact against the source ledger. Label it as an educational
   model, list known simplifications, and report claims that remain unverified.

## Learning rules

- Prefer causal relationships and decision trade-offs over decorative detail.
- Use visual changes to make transformations inspectable, not to imply certainty.
- Test transfer with a changed scenario; a learner following an animation is not
  evidence of understanding.
- Keep puzzles answerable from the represented model and avoid scoring model
  output as learner mastery without an unaided learner response.

## Boundaries

- Never infer permission to use a simulation from a general request to learn,
  study, review progress, build a track, or explain a topic. Ask before using
  it when authorization is absent.
- Never claim a generated simulation is fully accurate or hallucination-free.
- Never use an LLM-only review as factual verification for high-stakes or
  contested claims.
- Never invent source provenance, measurements, processes, or visual details.
- Do not publish learner workspace content or generated artifacts without explicit
  authorization.
