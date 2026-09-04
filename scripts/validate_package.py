#!/usr/bin/env python3
"""Validate the Agent Plugins v1 fields used by this package without dependencies."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
ALLOWED_FIELDS = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}
NAME_RE = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?$")


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = root / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"plugin.json: {exc}"]
    if not isinstance(manifest, dict):
        return ["plugin.json must contain an object"]
    unknown = sorted(set(manifest) - ALLOWED_FIELDS)
    if unknown:
        errors.append(f"plugin.json has unknown fields: {', '.join(unknown)}")
    if manifest.get("$schema") != SCHEMA:
        errors.append("plugin.json targets an unsupported Agent Plugins schema")
    name = manifest.get("name")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        errors.append("plugin name violates Agent Plugins v1 constraints")
    for field in ("version", "description", "homepage", "repository", "license"):
        if field in manifest and not isinstance(manifest[field], str):
            errors.append(f"plugin field {field!r} must be a string")
    if "keywords" in manifest and (
        not isinstance(manifest["keywords"], list)
        or not all(isinstance(item, str) for item in manifest["keywords"])
    ):
        errors.append("plugin keywords must be an array of strings")
    skills_root = root / "skills"
    if not skills_root.is_dir():
        errors.append("skills must be a directory when present")
    else:
        names: set[str] = set()
        for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.is_file():
                continue
            text = skill_file.read_text(encoding="utf-8")
            match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
            if not match:
                errors.append(f"{skill_file}: missing frontmatter")
                continue
            fields = {}
            for line in match.group(1).splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    fields[key.strip()] = value.strip()
            skill_name = fields.get("name")
            if skill_name != skill_dir.name:
                errors.append(f"{skill_file}: name must match its directory")
            if not fields.get("description"):
                errors.append(f"{skill_file}: description is required")
            if skill_name in names:
                errors.append(f"duplicate skill name: {skill_name}")
            if skill_name:
                names.add(skill_name)
    return errors


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors = validate(root)
    print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
