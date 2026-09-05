# Learning Loop

Learning Loop turns an AI coding agent into a learning coach with a durable
memory. Give it a goal, such as "learn Spring Boot microservices for a backend
interview," and it can build a source-grounded track, guide practice, schedule
closed-book recall, and keep an auditable record of what you actually did.

The memory is a directory of ordinary Markdown files. **Obsidian is optional.**
You can use Obsidian, VS Code, a Git repository, or any other Markdown-capable
tool to inspect and edit it.

Learning Loop is packaged for:

- Codex and ChatGPT plugin surfaces
- Claude Code
- clients that implement the [Agent Plugins 1.0 specification](https://agent-plugins.org/)
- direct command-line use with Python 3.11 or newer

## The idea in one minute

Most AI tutoring disappears when the chat ends. Learning Loop separates the
conversation from the learning record:

```text
Goal -> Track -> Learn and build -> Evidence -> Recall cards
                                             |
                                             v
Progress review <- Attempt ledger <- Closed-book recall
```

The agent provides judgment: it researches, asks questions, evaluates answers,
and adapts the track. The Python runner provides deterministic state changes:
it finds due cards, records attempts, advances schedules, and validates the
workspace. Markdown remains the source of truth.

This distinction matters. A plan is not evidence, reading is not mastery, and a
green build is not automatically proof that you can explain or reproduce the
work. Learning Loop records these as different things.

## Install

### Codex

Add this repository as a marketplace and install the plugin:

```bash
codex plugin marketplace add k4vrin/learning-loop
codex plugin add learning-loop@learning-loop
```

Start a new Codex session after installation. In an interactive Codex session,
`/plugins` shows installed plugins.

The same `.agents/plugins/marketplace.json` can be imported by a ChatGPT
workspace administrator from GitHub. Availability still depends on the
workspace's plugin policies and the ChatGPT surface being used.

### Claude Code

Add the repository as a Claude marketplace and install the plugin:

```bash
claude plugin marketplace add k4vrin/learning-loop
claude plugin install learning-loop@learning-loop
```

For a temporary local test instead of an installation:

```bash
git clone https://github.com/k4vrin/learning-loop.git
claude --plugin-dir ./learning-loop
```

Use `/reload-plugins` if Claude Code reports that a reload is required.

### Other agent harnesses

The repository root is an Agent Plugins 1.0 package. A compatible client can
load `plugin.json` and the skills beneath `skills/`; the exact installation
command is client-specific. The specification currently lists clients such as
Cursor, GitHub Copilot, Kiro, Hermes Agent, OpenClaw, Grok Bot, and NanoClaw.

Portability means the package has a common structure. It does not mean every
client exposes the same tools, permissions, scheduling, or installation UI.
The core learning workflow works best in a harness that can read and write a
local directory and execute Python.

### Runner only

No Python package installation is required:

```bash
git clone https://github.com/k4vrin/learning-loop.git
cd learning-loop
python3 scripts/learning_loop.py --help
```

Python 3.11 or newer is required.

## Quick start

After installing the plugin, ask the agent to initialize an explicitly chosen
Markdown directory:

> Initialize Learning Loop in `/absolute/path/to/my-notes`.

Then create a concrete track:

> Build a six-week, source-grounded track for learning Spring Boot
> microservices. I can study 60 minutes per day. Include implementation tasks,
> tests, explanation gates, and interview-style recall.

During track design, the agent first inspects relevant context and recent
learning evidence that already exist in the workspace. It does not repeat
questions answered by reliable current context. If important information is
missing, it asks at most three consolidated questions whose answers would
materially change the track. If the starting level is uncertain, it may use a
short diagnostic task instead of relying only on self-reported confidence. The
track records the reused context, assumptions, open questions, and basis for its
starting level.

Before a new application task, the agent states the required reading or setup
and waits until you say `prepared`. Due-card recall is closed-book and starts
without preparation.

Useful follow-up requests include:

- `Run five due recall cards.`
- `Review this week's evidence and adapt the track.`
- `Refresh sources that may have changed.`
- `Create retention cards for the session we just completed.`
- `Build an interactive simulation of this process.`

The simulation capability is opt-in; it is not silently substituted for normal
practice.

## How the parts work

| Path | Responsibility |
| --- | --- |
| `plugin.json` | Portable Agent Plugins 1.0 identity and discovery metadata |
| `skills/` | The learning behaviors and safety rules that an agent follows |
| `scripts/learning_loop.py` | Deterministic workspace initialization, queues, scheduling, recording, and validation |
| `templates/` | Starting shapes for tracks and recall cards |
| `.codex-plugin/plugin.json` | Native Codex presentation and skill registration |
| `.agents/plugins/marketplace.json` | Codex and ChatGPT marketplace distribution |
| `.claude-plugin/plugin.json` | Claude Code identity metadata |
| `.claude-plugin/marketplace.json` | Claude Code marketplace distribution |
| `tests/` | Regression coverage for scheduling, safety, and packaging |

The seven skills form a lifecycle:

1. `initialize-learning-vault` creates or inspects the isolated workspace. The
   historical skill name says "vault," but the implementation only requires a
   filesystem directory containing Markdown.
2. `build-learning-track` turns a goal, syllabus, job posting, source set, or
   existing notes into an executable track with evidence gates.
3. `build-learning-simulation` creates a source-grounded interactive model only
   when the learner explicitly requests one.
4. `session-retention-contract` converts completed learning into focused recall
   cards.
5. `run-recall-session` presents due prompts one at a time, closed-book, then
   evaluates and records the confirmed result.
6. `review-learning-progress` uses attempt evidence to advance, remediate,
   pause, or reduce scope.
7. `refresh-learning-sources` rechecks unstable facts against current primary
   sources without rewriting historical attempt evidence.

Files under `skills/*/agents/` provide optional interface metadata for clients
that understand it. The actual portable instructions remain in each
`SKILL.md`.

## The Markdown workspace

Initialization creates one isolated `Learning/` folder beneath the directory
you authorize:

```text
Learning/
├── Dashboard.md
├── Tracks/          goals, capability maps, activities, and readiness gates
├── Cards/           recall prompts and scheduling frontmatter
├── Sessions/        append-first attempts, ratings, gaps, and corrections
├── Sources/         source provenance and learner-owned notes
└── Assessments/     representative performance evidence
```

`Dashboard.md` is the command center. Card frontmatter is the scheduling source
of truth. `Sessions/` is the learning ledger: attempts are recorded before a
card's schedule is updated so a failed second write does not erase the attempt.

The runner deliberately supports only the flat scalar frontmatter it owns. It
refuses unfamiliar state instead of silently reformatting broader Markdown or
Obsidian metadata.

## Direct runner commands

Initialize a disposable example:

```bash
python3 scripts/learning_loop.py init --workspace /tmp/example-learning
```

Start a session and return due prompts without reference answers:

```bash
python3 scripts/learning_loop.py start \
  --workspace /tmp/example-learning \
  --limit 5
```

Record a confirmed result:

```bash
python3 scripts/learning_loop.py record \
  --workspace /tmp/example-learning \
  --card example-card-id \
  --rating good \
  --summary "Explained the concept and reproduced the main steps" \
  --gaps "Need a clearer failure-mode explanation" \
  --evidence "Completed closed-book in this session"
```

Validate the workspace after manual or bulk changes:

```bash
python3 scripts/learning_loop.py validate \
  --workspace /tmp/example-learning
```

`--vault` remains a backward-compatible alias for `--workspace`; it does not
make Obsidian a dependency.

## Safety and privacy

- The runner writes only inside the exact workspace and learning folder you
  provide; the default learning folder is `Learning/`.
- Managed workspace paths must not be symbolic links. This prevents a symlink
  inside the workspace from redirecting a write outside the authorized root.
- Due-card responses omit reference answers.
- Attempt records are appended before scheduling metadata is changed.
- No remote service, account, database, or Obsidian API is required.
- Sources can contain external links, but the learning ledger stays in your
  chosen filesystem unless you publish or sync it yourself.

Always inspect and authorize the exact filesystem root before allowing a
harness to write.

## What this plugin does not claim

- It does not prove mastery merely because a track or card exists.
- It does not treat assisted repair as equivalent to closed-book ownership.
- It does not include a background scheduler; the harness or user starts a
  recall session.
- It does not guarantee identical behavior in every agent client. Skill
  selection and tool permissions remain client-specific.
- It is not tied to Obsidian and does not install an Obsidian community plugin.

## Development and validation

```bash
python3 -m unittest discover -s tests
python3 scripts/validate_package.py .
python3 scripts/learning_loop.py --help
claude plugin validate .
```

Contributions should preserve the boundary between agent judgment and
deterministic state mutation, keep historical evidence append-first, and add
tests for changes to scheduling or workspace safety.

## License

Learning Loop is licensed under the
[Apache License 2.0](LICENSE). You may use, modify, and redistribute it,
including commercially, subject to the license terms.
