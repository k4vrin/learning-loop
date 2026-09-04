---
name: run-recall-session
description: Run an interactive closed-book learning session from due cards in a portable Learning Loop Markdown workspace; Obsidian is optional. Use for daily review, spaced repetition, active recall, interview questions, repair practice, or a short rescue session where prompts must be shown one at a time and answers assessed before references are revealed.
---

# Run a Recall Session

Make starting easier than browsing the learning system. Present one concrete
question, wait for the learner, then continue.

Resolve `<plugin-root>` as the nearest ancestor of this `SKILL.md` that contains
the portable root `plugin.json`. Do not assume the process working directory.

## Start

1. Resolve the explicitly authorized Markdown workspace and learning folder.
2. Validate state. Stop on duplicate IDs or invalid cards.
3. Start the session through the deterministic helper. It refreshes
   `Learning/Cards/Recall Calendar.md` from active-card frontmatter before
   returning due prompts, so other agents can inspect the current queue without
   opening reference answers:

   ```bash
   python3 <plugin-root>/scripts/learning_loop.py start \
     --workspace <workspace-root> --limit 3
   ```

4. Treat card frontmatter as scheduling truth and the generated calendar as an
   operational snapshot. Read due prompts from the command's `due_cards` field.
5. Select the first returned card unless the user requests a particular track.
6. Present only its `recall_prompt`. Say that notes and references must remain
   closed. Do not include hints, headings from the reference answer, or a task
   checklist.
7. End the turn and wait for the learner's answer.

## Assess after the answer

1. Commit to the received answer before opening the card's `Reference answer`.
2. Compare claims against the card's reference and cited primary sources.
3. Identify correct points, material gaps, incorrect claims, assistance used, and
   the smallest useful repair question.
4. Ask the repair or transfer question when it would test the gap. Do not leak its
   answer. Wait again when an answer is expected.
5. Recommend a rating using [references/rating-rubric.md](references/rating-rubric.md),
   then ask the learner to confirm or change it.
6. Record only after confirmation:

   ```bash
   python3 <plugin-root>/scripts/learning_loop.py record \
     --workspace <workspace-root> --card <learning-id> --rating <rating> \
     --summary <answer-summary> --gaps <gaps> --evidence <evidence>
   ```

7. Report the next review date and one concise correction. Offer another card only
   if it fits the user's time budget.

## New application tasks

Before presenting a new application task from any course or track:

1. Inspect the selected session for its prescribed reading, setup, or other
   preparation.
2. State that preparation explicitly and wait for the learner to confirm it is
   complete. Do not silently replace it with an application prompt.
3. If the task is meant to be closed-book, tell the learner to close notes and
   references only after the preparation step, then present the task.

This sequence applies after due reviews as well as when a learner starts a
session directly. Due-card recalls themselves remain closed-book and do not
require preparatory reading first.

## Session closure

After the learner completes and records an application session, apply the
`session-retention-contract` skill. Do not create cards before the session
evidence exists.

## Session limits

- Default to at most two due reviews and one new application task.
- In rescue mode, run exactly one review.
- Never turn missed days into a large visible backlog.
- Prioritize due and weak high-value material before new content.
- Agent assessment informs the rating; it does not establish mastery by itself.
