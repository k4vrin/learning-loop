# Learning Loop Engineering Guide

## Product boundary

Learning Loop is a material-agnostic Agent Plugins package. Keep subject content
in user vaults, not in the plugin. The portable v1 core contains Agent Skills and,
when implemented, MCP configuration. Client-specific scheduling and installation
must remain adapters outside the portable learning contract.

## Safety

- Require an explicit vault path before reading or writing learner data.
- Restrict mutations to the configured learning folder.
- Preserve existing notes and append-only attempts.
- Keep source provenance and uncertainty visible.
- Do not let model output alone establish mastery or scheduling state.

## Verification

Run before handoff:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q scripts tests
python3 -m json.tool plugin.json
python3 -m json.tool .codex-plugin/plugin.json
python3 scripts/validate_package.py .
git diff --check
```
