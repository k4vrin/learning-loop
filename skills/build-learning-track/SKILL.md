---
name: build-learning-track
description: Build or revise a material-agnostic, source-grounded learning track from a goal, syllabus, job posting, existing notes, files, URLs, or a request such as learning Java, Rust, Go, Python, or another subject. Use when an agent must research or organize learning material, create executable practice, seed recall cards, or adapt scope to a learner's outcome and time budget.
---

# Build a Learning Track

Design backward from a real performance. Keep subject material in the target
Markdown workspace; keep the plugin itself domain-neutral.

Resolve `<plugin-root>` as the nearest ancestor of this `SKILL.md` that contains
the portable root `plugin.json`. Do not assume the process working directory.

## Workflow

1. Inspect the learner's goal, current ability, time budget, deadline, supplied
   sources, allowed research, and exclusions.
2. Ask only questions whose answers materially change scope. State reasonable
   assumptions when the user delegates the choice.
3. Choose a source mode:
   - `provided`: use only learner-supplied material;
   - `research`: find current primary sources;
   - `mixed`: treat supplied material as the baseline and research gaps.
4. Read [references/source-policy.md](references/source-policy.md) before web
   research or time-sensitive claims.
5. Create a capability map that connects each required capability to priority,
   observable evidence, practice, and assessment.
6. Prefer the smallest sequence that reaches the target performance. Separate
   prerequisite, constrained, independent, mixed, and timed practice.
7. Create or update a track note using the
   [track template](../../templates/Track.md) as the shape.
8. Apply the `session-retention-contract` skill after each completed learning
   session. Create three atomic recall cards by default for the most important
   durable lessons, procedures, failure modes, or decisions from that session.
   Use the [card template](../../templates/Card.md); write one answerable
   `## Recall prompt` and a
   source-grounded `## Reference answer` for each card.
9. Set new cards to `interval_days: 0`, `repetitions: 0`, and
   `last_rating: new`. Stagger initial due dates to respect the daily budget.
10. Validate the learning folder with:

    ```bash
    python3 <plugin-root>/scripts/learning_loop.py validate \
      --workspace <workspace-root>
    ```

## Learning rules

- Require retrieval or an unaided attempt before reference use.
- Treat reading and watching as preparation, not mastery.
- Attach each important capability to an observable output or performance.
- Record corrections: what failed, why, the corrected rule, and a later test.
- Revisit important capabilities with changed prompts or contexts.
- Do not equate completion, confidence, or agent approval with mastery.
- Do not create a workload that exceeds the stated time budget without saying so.

## Boundaries

- Never invent sources, employer priorities, exam requirements, or current facts.
- Never copy substantial copyrighted material into reference answers.
- Do not rewrite unrelated workspace notes. Link to explicitly authorized source
  notes and write learning state only inside the configured learning folder.
- If no reliable material is available, request it or record a labeled research
  gap rather than filling the answer from memory.
