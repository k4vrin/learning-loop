# Learning workspace contract

The workspace is an ordinary filesystem directory containing Markdown.
Obsidian may be used as an editor, but it is not part of the storage contract.

Learning Loop owns only the configured learning folder:

```text
Learning/
├── Learning Config.md
├── Dashboard.md
├── Tracks/
├── Cards/
├── Sessions/
├── Sources/
└── Assessments/
```

- `Tracks/` describes goals, capability maps, sequencing, and readiness gates.
- `Cards/` contains plugin-owned flat YAML state plus recall and reference text.
- `Sessions/` contains append-only attempt evidence organized by local date.
- `Sources/` may contain learner-authored summaries or links to existing notes.
- `Assessments/` contains representative checkpoints and scored performances.

Existing notes remain outside this ownership boundary. Link to them only when the
user supplies the note or explicitly opts it in as a learning source. Managed
workspace paths must not be filesystem symlinks; use Markdown links to reference
content outside the learning folder.
