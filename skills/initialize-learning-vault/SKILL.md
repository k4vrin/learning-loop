---
name: initialize-learning-vault
description: Initialize or inspect a safe Learning workspace inside an explicitly authorized filesystem directory containing Markdown; Obsidian is optional. Use when setting up Learning Loop, applying it to a new workspace, validating its folder contract, or preparing Tracks, Cards, Sessions, Sources, and Assessments without restructuring existing notes.
---

# Initialize a Learning Workspace

Keep Learning Loop additive. Treat the existing workspace as user-owned data.

Resolve `<plugin-root>` as the nearest ancestor of this `SKILL.md` that contains
the portable root `plugin.json`. Do not assume the process working directory.

## Workflow

1. Resolve the exact workspace root and confirm it is the intended target.
2. Inspect existing top-level folders and Git status when available.
3. Read [references/vault-contract.md](references/vault-contract.md).
4. Preview the intended learning folder. Default to `Learning/` unless the user
   supplies another safe workspace-relative path.
5. Run:

   ```bash
   python3 <plugin-root>/scripts/learning_loop.py init \
     --workspace <workspace-root> --title <title>
   ```

6. Report every created path. Initialization is idempotent and must not overwrite
   an existing configuration or dashboard.
7. Validate after adding cards:

   ```bash
   python3 <plugin-root>/scripts/learning_loop.py validate \
     --workspace <workspace-root>
   ```

## Safety rules

- Never infer a workspace path when several plausible roots exist.
- Never place the learning folder outside the authorized workspace.
- Never follow symlinked cards or rewrite unrelated notes.
- Never delete, move, rename, or normalize existing workspace content during setup.
- Request explicit authorization before operating on a real workspace that is not
  already writable in the active environment.
