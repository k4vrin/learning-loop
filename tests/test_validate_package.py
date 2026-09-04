from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "validate_package.py"
SPEC = importlib.util.spec_from_file_location("validate_package", MODULE_PATH)
assert SPEC and SPEC.loader
validate_package = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validate_package
SPEC.loader.exec_module(validate_package)


class PackageValidatorTests(unittest.TestCase):
    def test_current_package_is_valid(self) -> None:
        errors = validate_package.validate(Path(__file__).parents[1])
        self.assertEqual(errors, [])

    def test_simulation_skill_is_packaged_with_its_interface_metadata(self) -> None:
        root = Path(__file__).parents[1]
        skill = root / "skills" / "build-learning-simulation"

        self.assertTrue((skill / "SKILL.md").is_file())
        self.assertTrue((skill / "agents" / "openai.yaml").is_file())
        self.assertTrue((skill / "references" / "simulation-contract.md").is_file())

    def test_package_versions_match(self) -> None:
        root = Path(__file__).parents[1]
        manifest = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
        codex_manifest = json.loads(
            (root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        claude_manifest = json.loads(
            (root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        claude_marketplace = json.loads(
            (root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(manifest["version"], project["project"]["version"])
        self.assertEqual(manifest["version"], codex_manifest["version"])
        self.assertEqual(manifest["version"], claude_manifest["version"])
        self.assertEqual(
            manifest["version"], claude_marketplace["plugins"][0]["version"]
        )

    def test_package_uses_apache_2_license_consistently(self) -> None:
        root = Path(__file__).parents[1]
        manifest = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
        codex_manifest = json.loads(
            (root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        claude_manifest = json.loads(
            (root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        claude_marketplace = json.loads(
            (root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))

        self.assertTrue((root / "LICENSE").is_file())
        self.assertEqual(manifest["license"], "Apache-2.0")
        self.assertEqual(codex_manifest["license"], "Apache-2.0")
        self.assertEqual(claude_manifest["license"], "Apache-2.0")
        self.assertEqual(claude_marketplace["plugins"][0]["license"], "Apache-2.0")
        self.assertEqual(project["project"]["license"], "Apache-2.0")

    def test_marketplaces_publish_the_repository_root_plugin(self) -> None:
        root = Path(__file__).parents[1]
        codex_marketplace = json.loads(
            (root / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        claude_marketplace = json.loads(
            (root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )

        self.assertEqual(
            codex_marketplace["plugins"][0]["source"],
            {
                "source": "url",
                "url": "https://github.com/k4vrin/learning-loop.git",
                "ref": "main",
            },
        )
        self.assertEqual(claude_marketplace["plugins"][0]["source"], ".")

    def test_rejects_unknown_manifest_field(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skills").mkdir()
            (root / "plugin.json").write_text(
                '{"$schema":"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",'
                '"name":"valid-name","unexpected":true}',
                encoding="utf-8",
            )
            errors = validate_package.validate(root)
            self.assertTrue(any("unknown fields" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
