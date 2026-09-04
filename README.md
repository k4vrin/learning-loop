# Learning Loop

Learning Loop is a material-agnostic [Agent Plugin](https://agent-plugins.org/)
for building source-grounded learning tracks and running closed-book,
spaced-repetition practice from a portable Markdown learning workspace.

Obsidian is optional. The persistence contract is an ordinary filesystem
directory containing Markdown files with constrained frontmatter; it does not
use an Obsidian API, plugin runtime, database, or proprietary file format.
Obsidian, a code editor, a Git forge, or any other Markdown-capable interface
can be used to inspect and edit the workspace.

## Workspace model

The learning workspace is a durable command center and evidence ledger:

- `Dashboard.md` is the current operational view.
- `Tracks/` contains goals, capability maps, and readiness gates.
- `Cards/` contains recall prompts and deterministic scheduling state.
- `Sessions/` is the append-only attempt and correction ledger.
- `Sources/` records source provenance and learner-owned notes.
- `Assessments/` records representative performance evidence.

Use `--workspace` for the authorized root directory. The legacy `--vault` name
remains as a backward-compatible alias and does not imply Obsidian.

The portable package follows Agent Plugins `1.0.0`. Skills own the learning
workflow; deterministic scripts own dates and workspace mutations. The initial
slice is skills-first. A portable MCP wrapper and client-specific scheduling
adapters will be added only after the local workspace contract is stable.

## Current capabilities

- Initialize an isolated `Learning/` workspace without modifying existing notes.
- Discover due Markdown cards from constrained YAML frontmatter.
- Keep reference answers out of the due-card response.
- Record an append-only attempt before updating the card schedule.
- Apply deterministic `Again`, `Hard`, `Good`, and `Easy` intervals.
- Validate duplicate IDs, required fields, dates, ratings, and recall prompts.
- Build source-led, interactive learning simulations with prediction checkpoints,
  visible simplifications, and a claim-to-source ledger.

## Development

```bash
python3 -m unittest discover -s tests
python3 scripts/learning_loop.py --help
```

Example against a disposable workspace:

```bash
python3 scripts/learning_loop.py init --workspace /tmp/example-learning
python3 scripts/learning_loop.py start --workspace /tmp/example-learning
```

`start` validates the cards, rebuilds `Learning/Cards/Recall Calendar.md` from
active-card frontmatter, and returns due prompts without reference answers.
Use `due` only when a read-only queue lookup is specifically required.

The CLI writes only below the configured learning folder, which defaults to
`Learning/`. Managed workspace directories and files must not be symlinks.
Always inspect and authorize the exact filesystem root before enabling writes.
