from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "learning_loop.py"
SPEC = importlib.util.spec_from_file_location("learning_loop", MODULE_PATH)
assert SPEC and SPEC.loader
learning_loop = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = learning_loop
SPEC.loader.exec_module(learning_loop)


def card_markdown(
    learning_id: str,
    *,
    due: str = "2026-08-10",
    priority: str = "important",
    interval_days: int = 0,
    repetitions: int = 0,
) -> str:
    return f"""---
learning_id: {learning_id}
track: test-track
status: active
priority: {priority}
due: {due}
interval_days: {interval_days}
repetitions: {repetitions}
last_rating: new
---

# {learning_id}

## Recall prompt

Explain {learning_id} from memory.

## Reference answer

SECRET REFERENCE FOR {learning_id}.
"""


class LearningLoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.vault = Path(self.temporary.name)
        result = learning_loop.initialize_vault(self.vault, "Learning", "Test Learning")
        self.root = Path(result["root"])

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_card(self, learning_id: str, **kwargs: object) -> Path:
        path = self.root / "Cards" / f"{learning_id}.md"
        path.write_text(card_markdown(learning_id, **kwargs), encoding="utf-8")
        return path

    def test_initialize_is_idempotent(self) -> None:
        second = learning_loop.initialize_vault(self.vault, "Learning", "Changed")
        self.assertEqual(second["created"], [])
        config = (self.root / "Learning Config.md").read_text(encoding="utf-8")
        self.assertIn("# Test Learning", config)

    def test_due_returns_prompt_without_reference_answer(self) -> None:
        self.write_card("older", due="2026-08-01", priority="optional")
        self.write_card("critical", due="2026-08-10", priority="critical")
        self.write_card("future", due="2026-08-11", priority="critical")

        due = learning_loop.due_cards(self.root, date(2026, 8, 10), 3)

        self.assertEqual([item["learning_id"] for item in due], ["older", "critical"])
        self.assertNotIn("SECRET REFERENCE", str(due))

    def test_start_session_refreshes_agent_readable_calendar(self) -> None:
        self.write_card("overdue", due="2026-08-09", priority="critical")
        reviewed = self.write_card("reviewed", due="2026-08-14", priority="important")
        reviewed.write_text(
            reviewed.read_text(encoding="utf-8").replace(
                "last_rating: new", "last_rating: good\nlast_attempt: 2026-08-10"
            ),
            encoding="utf-8",
        )
        self.write_card("future", due="2026-08-11", priority="optional")

        result = learning_loop.start_session(self.root, date(2026, 8, 10), 3)

        self.assertEqual(
            [item["learning_id"] for item in result["due_cards"]],
            ["overdue"],
        )
        self.assertEqual(result["due_count"], 1)
        self.assertEqual(result["reviewed_today_count"], 1)
        calendar = Path(result["calendar_path"]).read_text(encoding="utf-8")
        self.assertIn("learning_id: recall-calendar", calendar)
        self.assertIn("status: retired", calendar)
        self.assertIn("[overdue](overdue.md)", calendar)
        self.assertIn("[future](future.md)", calendar)
        self.assertIn("[reviewed](reviewed.md)", calendar)
        self.assertNotIn("SECRET REFERENCE", calendar)
        self.assertEqual(learning_loop.validate_vault(self.root), [])

    def test_refresh_calendar_replaces_stale_snapshot_without_queueing_it(self) -> None:
        self.write_card("due", due="2026-08-10")
        calendar_path = self.root / "Cards" / "Recall Calendar.md"
        calendar_path.write_text(
            card_markdown("recall-calendar", due="2026-08-01").replace(
                "status: active", "status: retired"
            )
            + "\nSTALE SNAPSHOT\n",
            encoding="utf-8",
        )

        result = learning_loop.refresh_recall_calendar(self.root, date(2026, 8, 10))

        calendar = calendar_path.read_text(encoding="utf-8")
        self.assertNotIn("STALE SNAPSHOT", calendar)
        self.assertEqual(result["due_count"], 1)
        self.assertEqual(
            [item["learning_id"] for item in learning_loop.due_cards(self.root, date(2026, 8, 10), 3)],
            ["due"],
        )

    def test_start_session_rejects_duplicate_ids_before_refreshing_calendar(self) -> None:
        self.write_card("duplicate")
        nested = self.root / "Cards" / "nested"
        nested.mkdir()
        (nested / "copy.md").write_text(card_markdown("duplicate"), encoding="utf-8")

        with self.assertRaisesRegex(learning_loop.LearningLoopError, "Duplicate learning_id"):
            learning_loop.start_session(self.root, date(2026, 8, 10), 3)

        self.assertFalse((self.root / "Cards" / "Recall Calendar.md").exists())

    def test_good_first_attempt_schedules_four_days_and_records_evidence(self) -> None:
        card = self.write_card("ownership")

        result = learning_loop.record_attempt(
            self.root,
            "ownership",
            "good",
            "Borrowing has scoped rules.",
            "Need to explain mutable aliasing.",
            "Answered without notes.",
            date(2026, 8, 10),
        )

        self.assertEqual(result["next_interval_days"], 4)
        self.assertEqual(result["next_due"], "2026-08-14")
        updated = card.read_text(encoding="utf-8")
        self.assertIn("due: 2026-08-14", updated)
        self.assertIn("repetitions: 1", updated)
        attempt = Path(result["attempt_path"]).read_text(encoding="utf-8")
        self.assertIn("Need to explain mutable aliasing.", attempt)

    def test_again_resets_repetitions(self) -> None:
        card = self.write_card("channels", interval_days=8, repetitions=3)

        result = learning_loop.record_attempt(
            self.root, "channels", "again", "Blank", "Core semantics", "", date(2026, 8, 10)
        )

        self.assertEqual(result["next_interval_days"], 1)
        self.assertEqual(result["repetitions"], 0)
        self.assertIn("repetitions: 0", card.read_text(encoding="utf-8"))

    def test_learning_folder_cannot_escape_vault(self) -> None:
        with self.assertRaises(learning_loop.LearningLoopError):
            learning_loop.learning_root(self.vault, "../outside")

    def test_symlinked_cards_directory_is_rejected(self) -> None:
        cards = self.root / "Cards"
        cards.rmdir()
        with tempfile.TemporaryDirectory() as directory:
            outside = Path(directory)
            cards.symlink_to(outside, target_is_directory=True)
            (outside / "escape.md").write_text(card_markdown("escape"), encoding="utf-8")

            errors = learning_loop.validate_vault(self.root)

            self.assertTrue(any("Symlinks are not allowed" in error for error in errors))

    def test_symlinked_sessions_directory_blocks_attempt_recording(self) -> None:
        card = self.write_card("contained")
        sessions = self.root / "Sessions"
        sessions.rmdir()
        with tempfile.TemporaryDirectory() as directory:
            outside = Path(directory)
            sessions.symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(learning_loop.LearningLoopError, "Symlinks are not allowed"):
                learning_loop.record_attempt(
                    self.root,
                    "contained",
                    "good",
                    "Answer",
                    "",
                    "Closed-book",
                    date(2026, 8, 10),
                )

            self.assertEqual(list(outside.iterdir()), [])
            self.assertIn("due: 2026-08-10", card.read_text(encoding="utf-8"))

    def test_nested_card_directory_symlink_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            nested = self.root / "Cards" / "external"
            nested.symlink_to(Path(directory), target_is_directory=True)

            errors = learning_loop.validate_vault(self.root)

            self.assertTrue(any("Unsafe card path" in error for error in errors))

    def test_workspace_flag_is_the_primary_cli_name(self) -> None:
        args = learning_loop.build_parser().parse_args(
            ["validate", "--workspace", str(self.vault)]
        )

        self.assertEqual(args.vault, str(self.vault))

    def test_duplicate_ids_fail_validation(self) -> None:
        self.write_card("duplicate")
        nested = self.root / "Cards" / "nested"
        nested.mkdir()
        (nested / "copy.md").write_text(card_markdown("duplicate"), encoding="utf-8")

        errors = learning_loop.validate_vault(self.root)

        self.assertTrue(any("Duplicate learning_id" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
