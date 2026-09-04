---
name: refresh-learning-sources
description: Verify and refresh unstable learning material in an existing Learning Loop track using current primary sources. Use when technologies, APIs, standards, interview expectations, laws, or other time-sensitive subjects may have changed, when a card's source is stale or broken, or when the user asks to keep a track up to date.
---

# Refresh Learning Sources

Refresh evidence, not novelty. Preserve historical attempts and scheduling state.

Resolve `<plugin-root>` as the nearest ancestor of this `SKILL.md` that contains
the portable root `plugin.json`. Do not assume the process working directory.

## Workflow

1. Identify active tracks, their target performance, source mode, source notes,
   and cards with version-sensitive claims.
2. Read [references/refresh-policy.md](references/refresh-policy.md).
3. Search current primary sources. Open and inspect the supporting pages rather
   than relying on search snippets.
4. Classify each finding as:
   - no meaningful change;
   - clarification only;
   - reference answer update;
   - capability changed enough to require a new card ID;
   - source unavailable or still uncertain.
5. Update source title, owner, link, purpose, verification date, and affected
   reference answer. Preserve the learner's original wording when it remains valid.
6. Create a new card ID when the tested capability materially changed; do not let
   prior repetitions silently establish mastery of a different capability.
7. Report what changed, why it matters to the target performance, and which
   claims remain unverified.

## Boundaries

- Never modify session attempts or pretend current documentation validates a
  historical answer retroactively.
- Never add release-note trivia without practical relevance.
- Never silently replace a learner-supplied source policy.
