---
name: session-retention-contract
description: Create and maintain spaced-repetition recall cards after a completed learning session. Use when closing a session, converting completed reading and practice into future review, repairing an overloaded card, or auditing whether a track has sufficient session-level retention coverage.
---

# Session Retention Contract

Turn completed learning into small, scheduled retrieval prompts.

Resolve `<plugin-root>` as the nearest ancestor of this `SKILL.md` that contains
the portable root `plugin.json`. Do not assume the process working directory.

## Workflow

1. Read the completed session evidence, assigned material, and existing cards.
   Do not create cards from planned, unattempted, or unrelated material.
2. Create three atomic cards by default. Select the session's most important
   durable lessons: a rule or contract, a failure mode or counterexample, and
   a design or decision procedure when the session supports them.
3. Make each prompt answerable without notes and each answer independently
   assessable. Do not combine unrelated rules, whole chapters, or a complete
   implementation into one card.
4. Cite the session evidence and the relevant supplied or primary source.
   Set new cards to `active`, `interval_days: 0`, `repetitions: 0`, and
   `last_rating: new`. Set a first due date about two days after completion;
   stagger only when the track's review budget needs it.
5. Retire a superseded or overloaded card instead of silently deleting its
   history. Do not create duplicate prompts.
6. If the source evidence does not establish three distinct, durable lessons,
   ask the learner which material they want to retain rather than inventing
   cards. The learner may also request a different number of cards.
7. Validate the workspace. Report the created, retired, and remaining cards.

## Review

Use `due` to present only scheduled prompts. Assess a committed closed-book
answer, obtain the learner's rating confirmation, then use `record` to apply
the scheduling formula. Reading is preparation; later recall and a changed
transfer remain the evidence of retention.
