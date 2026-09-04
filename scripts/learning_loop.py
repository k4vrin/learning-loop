#!/usr/bin/env python3
"""Deterministic Markdown-workspace operations for Learning Loop.

The parser deliberately supports only the flat scalar frontmatter that this
plugin owns. Refusing unfamiliar state is safer than silently reformatting a
user's broader Obsidian metadata.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import tempfile
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import quote


REQUIRED_CARD_FIELDS = {
    "learning_id",
    "track",
    "status",
    "priority",
    "due",
    "interval_days",
    "repetitions",
    "last_rating",
}
RATINGS = {"new", "again", "hard", "good", "easy"}
PRIORITIES = {"critical": 0, "important": 1, "optional": 2}
FIELD_RE = re.compile(r"^([a-z][a-z0-9_-]*):\s*(.*?)\s*$")


class LearningLoopError(ValueError):
    """Raised when plugin-owned workspace state is unsafe or invalid."""


@dataclass(frozen=True)
class Card:
    path: Path
    metadata: dict[str, str]
    body: str

    @property
    def learning_id(self) -> str:
        return self.metadata["learning_id"]


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _reject_symlink_components(path: Path, boundary: Path) -> None:
    """Reject symlinks below an already authorized filesystem boundary."""
    workspace = boundary.resolve()
    candidate = path.absolute()
    try:
        relative = candidate.relative_to(workspace)
    except ValueError as exc:
        raise LearningLoopError(f"Path escapes the learning workspace: {candidate}") from exc

    current = workspace
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise LearningLoopError(
                f"Symlinks are not allowed in the learning workspace: {current}"
            )


def _safe_managed_path(root: Path, path: Path, *, parent_only: bool = False) -> Path:
    """Validate a managed path without following workspace-owned symlinks."""
    workspace = root.resolve()
    candidate = path.parent if parent_only else path
    _reject_symlink_components(candidate, workspace)
    if not _inside(candidate.resolve(), workspace):
        raise LearningLoopError(f"Path escapes the learning workspace: {path}")
    return path


def learning_root(vault: str | Path, folder: str = "Learning") -> Path:
    vault_root = Path(vault).expanduser().resolve()
    if not vault_root.exists() or not vault_root.is_dir():
        raise LearningLoopError(f"Workspace directory does not exist: {vault_root}")
    relative = Path(folder)
    if relative.is_absolute() or ".." in relative.parts:
        raise LearningLoopError("Learning folder must be a safe workspace-relative path")
    target = (vault_root / relative).resolve()
    if not _inside(target, vault_root):
        raise LearningLoopError("Learning folder escapes the workspace")
    return target


def _split_frontmatter(text: str) -> tuple[list[str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise LearningLoopError("Card must start with YAML frontmatter")
    try:
        closing = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as exc:
        raise LearningLoopError("Card frontmatter is not closed") from exc
    return lines[1:closing], "\n".join(lines[closing + 1 :]).lstrip("\n")


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines, body = _split_frontmatter(text)
    metadata: dict[str, str] = {}
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = FIELD_RE.match(line)
        if not match:
            raise LearningLoopError(
                "Learning cards support only flat scalar frontmatter; "
                f"unsupported line: {line!r}"
            )
        metadata[match.group(1)] = _unquote(match.group(2).strip())
    return metadata, body


def _yaml_scalar(value: str | int) -> str:
    raw = str(value)
    if re.fullmatch(r"[a-zA-Z0-9_.-]+", raw):
        return raw
    return json.dumps(raw, ensure_ascii=False)


def update_frontmatter(text: str, updates: dict[str, str | int]) -> str:
    frontmatter, body = _split_frontmatter(text)
    remaining = dict(updates)
    output = ["---"]
    for line in frontmatter:
        match = FIELD_RE.match(line)
        if match and match.group(1) in remaining:
            key = match.group(1)
            output.append(f"{key}: {_yaml_scalar(remaining.pop(key))}")
        else:
            output.append(line)
    for key, value in remaining.items():
        output.append(f"{key}: {_yaml_scalar(value)}")
    output.extend(["---", "", body.rstrip(), ""])
    return "\n".join(output)


def _parse_date(value: str, field: str = "date") -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise LearningLoopError(f"Invalid {field}: {value!r}; expected YYYY-MM-DD") from exc


def _parse_nonnegative_int(value: str, field: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise LearningLoopError(f"Invalid {field}: {value!r}; expected an integer") from exc
    if parsed < 0:
        raise LearningLoopError(f"Invalid {field}: must not be negative")
    return parsed


def _section(body: str, heading: str) -> str:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    return match.group(1).strip() if match else ""


def _title(body: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", body, re.MULTILINE)
    return match.group(1).strip() if match else fallback


def validate_card(card: Card) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_CARD_FIELDS - card.metadata.keys())
    if missing:
        errors.append(f"missing fields: {', '.join(missing)}")
        return errors
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", card.learning_id):
        errors.append("learning_id must be kebab-case")
    if card.metadata["status"] not in {"active", "paused", "retired"}:
        errors.append("status must be active, paused, or retired")
    if card.metadata["priority"] not in PRIORITIES:
        errors.append("priority must be critical, important, or optional")
    if card.metadata["last_rating"] not in RATINGS:
        errors.append("last_rating is invalid")
    try:
        _parse_date(card.metadata["due"], "due")
        _parse_nonnegative_int(card.metadata["interval_days"], "interval_days")
        _parse_nonnegative_int(card.metadata["repetitions"], "repetitions")
    except LearningLoopError as exc:
        errors.append(str(exc))
    if not _section(card.body, "Recall prompt"):
        errors.append("Recall prompt section is empty")
    return errors


def load_cards(root: Path) -> tuple[list[Card], list[str]]:
    cards_root = root / "Cards"
    cards: list[Card] = []
    errors: list[str] = []
    try:
        _safe_managed_path(root, cards_root)
    except LearningLoopError as exc:
        return cards, [str(exc)]
    if not cards_root.exists():
        return cards, ["Cards directory is missing"]
    for path in sorted(cards_root.rglob("*")):
        if path.is_symlink():
            errors.append(f"Unsafe card path skipped: {path}")
            continue
        if not path.is_file() or path.suffix != ".md":
            continue
        try:
            _safe_managed_path(root, path)
        except LearningLoopError:
            errors.append(f"Unsafe card path skipped: {path}")
            continue
        try:
            metadata, body = parse_frontmatter(path.read_text(encoding="utf-8"))
            card = Card(path=path, metadata=metadata, body=body)
            card_errors = validate_card(card)
            if card_errors:
                errors.extend(f"{path}: {error}" for error in card_errors)
            else:
                cards.append(card)
        except (OSError, LearningLoopError) as exc:
            errors.append(f"{path}: {exc}")
    return cards, errors


def _duplicate_id_errors(cards: list[Card]) -> list[str]:
    errors: list[str] = []
    seen: dict[str, Path] = {}
    for card in cards:
        previous = seen.get(card.learning_id)
        if previous:
            errors.append(f"Duplicate learning_id {card.learning_id!r}: {previous} and {card.path}")
        else:
            seen[card.learning_id] = card.path
    return errors


def initialize_vault(vault: str | Path, folder: str, title: str) -> dict[str, object]:
    root = learning_root(vault, folder)
    created: list[str] = []
    for name in ("Tracks", "Cards", "Sessions", "Sources", "Assessments"):
        path = root / name
        _safe_managed_path(root, path)
        if not path.exists():
            path.mkdir(parents=True)
            created.append(str(path))
    config = root / "Learning Config.md"
    _safe_managed_path(root, config)
    if not config.exists():
        config.write_text(
            "---\nlearning_loop_version: 1\nlearning_folder: "
            f"{_yaml_scalar(folder)}\n---\n\n# {title}\n\n"
            "This folder is managed explicitly by the Learning Loop plugin.\n",
            encoding="utf-8",
        )
        created.append(str(config))
    dashboard = root / "Dashboard.md"
    _safe_managed_path(root, dashboard)
    if not dashboard.exists():
        dashboard.write_text(
            f"# {title}\n\n## Today\n\nUse the learning agent to list due cards.\n\n"
            "## Tracks\n\nAdd relative links to active track notes here.\n",
            encoding="utf-8",
        )
        created.append(str(dashboard))
    return {"root": str(root), "created": created}


def due_cards(root: Path, on: date, limit: int) -> list[dict[str, object]]:
    cards, errors = load_cards(root)
    if errors:
        raise LearningLoopError("Vault validation failed:\n" + "\n".join(errors))
    eligible = [
        card
        for card in cards
        if card.metadata["status"] == "active"
        and _parse_date(card.metadata["due"], "due") <= on
    ]
    eligible.sort(
        key=lambda card: (
            _parse_date(card.metadata["due"], "due"),
            PRIORITIES[card.metadata["priority"]],
            card.learning_id,
        )
    )
    result = []
    for card in eligible[:limit]:
        result.append(
            {
                "learning_id": card.learning_id,
                "title": _title(card.body, card.learning_id),
                "track": card.metadata["track"],
                "priority": card.metadata["priority"],
                "due": card.metadata["due"],
                "recall_prompt": _section(card.body, "Recall prompt"),
                "path": str(card.path),
            }
        )
    return result


def _calendar_card_link(card: Card, cards_root: Path) -> str:
    relative = card.path.relative_to(cards_root)
    target = quote(relative.as_posix(), safe="/")
    title = (
        _title(card.body, card.learning_id)
        .replace("\\", "\\\\")
        .replace("]", "\\]")
        .replace("|", "\\|")
    )
    return f"[{title}]({target})"


def _calendar_rows(cards: list[Card], cards_root: Path) -> str:
    if not cards:
        return "_None._"
    rows = ["| Due | Priority | Track | Card |", "| --- | --- | --- | --- |"]
    for card in cards:
        rows.append(
            "| "
            + " | ".join(
                (
                    card.metadata["due"],
                    card.metadata["priority"],
                    card.metadata["track"].replace("|", "\\|"),
                    _calendar_card_link(card, cards_root),
                )
            )
            + " |"
        )
    return "\n".join(rows)


def refresh_recall_calendar(root: Path, on: date) -> dict[str, object]:
    """Rebuild the agent-readable schedule snapshot from card frontmatter."""
    cards, errors = load_cards(root)
    errors.extend(_duplicate_id_errors(cards))
    if errors:
        raise LearningLoopError("Vault validation failed:\n" + "\n".join(errors))

    cards_root = root / "Cards"
    active = [card for card in cards if card.metadata["status"] == "active"]
    active.sort(
        key=lambda card: (
            _parse_date(card.metadata["due"], "due"),
            PRIORITIES[card.metadata["priority"]],
            card.learning_id,
        )
    )
    due = [card for card in active if _parse_date(card.metadata["due"], "due") <= on]
    upcoming = [card for card in active if _parse_date(card.metadata["due"], "due") > on]
    reviewed = [card for card in active if card.metadata.get("last_attempt") == on.isoformat()]

    calendar_path = cards_root / "Recall Calendar.md"
    existing = next((card for card in cards if card.learning_id == "recall-calendar"), None)
    calendar_track = existing.metadata["track"] if existing else "learning-loop"
    content = (
        "---\n"
        "learning_id: recall-calendar\n"
        f"track: {_yaml_scalar(calendar_track)}\n"
        "status: retired\n"
        "priority: optional\n"
        f"due: {on.isoformat()}\n"
        "interval_days: 0\n"
        "repetitions: 0\n"
        "last_rating: new\n"
        "---\n\n"
        "# Recall Calendar\n\n"
        f"> **Last refreshed:** {on.isoformat()}\n>\n"
        "> Generated from active-card frontmatter at session start. Card frontmatter is the\n"
        "> scheduling source of truth; this retired card never enters the recall queue.\n\n"
        "## Recall prompt\n\n"
        "Operational calendar only; it is intentionally retired.\n\n"
        f"## Due through today — {on.isoformat()}\n\n"
        f"{_calendar_rows(due, cards_root)}\n\n"
        "## Upcoming\n\n"
        f"{_calendar_rows(upcoming, cards_root)}\n\n"
        f"## Reviewed today — {on.isoformat()}\n\n"
        f"{_calendar_rows(reviewed, cards_root)}\n"
    )
    _atomic_write(root, calendar_path, content)
    return {
        "calendar_path": str(calendar_path),
        "refreshed_on": on.isoformat(),
        "due_count": len(due),
        "upcoming_count": len(upcoming),
        "reviewed_today_count": len(reviewed),
    }


def start_session(root: Path, on: date, limit: int) -> dict[str, object]:
    if limit < 1:
        raise LearningLoopError("Limit must be at least 1")
    calendar = refresh_recall_calendar(root, on)
    return {**calendar, "due_cards": due_cards(root, on, limit)}


def next_interval(interval_days: int, repetitions: int, rating: str) -> tuple[int, int]:
    if rating not in RATINGS - {"new"}:
        raise LearningLoopError("Rating must be again, hard, good, or easy")
    if rating == "again":
        return 1, 0
    if rating == "hard":
        return max(2, math.ceil(interval_days * 1.5)), repetitions + 1
    if rating == "good":
        return (4 if repetitions == 0 else max(7, math.ceil(interval_days * 2))), repetitions + 1
    return (7 if repetitions == 0 else max(14, math.ceil(interval_days * 2.5))), repetitions + 1


def _atomic_write(root: Path, path: Path, content: str) -> None:
    _safe_managed_path(root, path, parent_only=True)
    if path.is_symlink():
        raise LearningLoopError(f"Refusing to replace a symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        _safe_managed_path(root, path, parent_only=True)
        if path.is_symlink():
            raise LearningLoopError(f"Refusing to replace a symlink: {path}")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _find_card(root: Path, learning_id: str) -> Card:
    cards, errors = load_cards(root)
    if errors:
        raise LearningLoopError("Vault validation failed:\n" + "\n".join(errors))
    matches = [card for card in cards if card.learning_id == learning_id]
    if len(matches) != 1:
        raise LearningLoopError(f"Expected exactly one card for {learning_id!r}; found {len(matches)}")
    return matches[0]


def record_attempt(
    root: Path,
    learning_id: str,
    rating: str,
    summary: str,
    gaps: str,
    evidence: str,
    on: date,
) -> dict[str, object]:
    card = _find_card(root, learning_id)
    previous_interval = _parse_nonnegative_int(card.metadata["interval_days"], "interval_days")
    previous_repetitions = _parse_nonnegative_int(card.metadata["repetitions"], "repetitions")
    interval, repetitions = next_interval(previous_interval, previous_repetitions, rating)
    due = on + timedelta(days=interval)
    attempt_id = uuid.uuid4().hex
    recorded_at = datetime.now(timezone.utc).isoformat()
    attempt_path = root / "Sessions" / on.isoformat() / f"{attempt_id}.md"
    attempt = (
        "---\n"
        f"attempt_id: {attempt_id}\n"
        f"learning_id: {learning_id}\n"
        f"track: {_yaml_scalar(card.metadata['track'])}\n"
        f"attempt_date: {on.isoformat()}\n"
        f"recorded_at: {_yaml_scalar(recorded_at)}\n"
        f"rating: {rating}\n"
        f"previous_interval_days: {previous_interval}\n"
        f"next_interval_days: {interval}\n"
        f"due_after: {due.isoformat()}\n"
        "---\n\n"
        f"# Attempt: {_title(card.body, learning_id)}\n\n"
        f"## Answer summary\n\n{summary.strip() or 'Not recorded.'}\n\n"
        f"## Gaps and corrections\n\n{gaps.strip() or 'None recorded.'}\n\n"
        f"## Evidence\n\n{evidence.strip() or 'None recorded.'}\n"
    )
    # The append-only attempt is the recovery record. If the subsequent cache
    # update fails, the scheduler can be rebuilt later without losing evidence.
    _atomic_write(root, attempt_path, attempt)
    original = card.path.read_text(encoding="utf-8")
    updated = update_frontmatter(
        original,
        {
            "due": due.isoformat(),
            "interval_days": interval,
            "repetitions": repetitions,
            "last_rating": rating,
            "last_attempt": on.isoformat(),
        },
    )
    _atomic_write(root, card.path, updated)
    return {
        "attempt_id": attempt_id,
        "attempt_path": str(attempt_path),
        "card_path": str(card.path),
        "previous_interval_days": previous_interval,
        "next_interval_days": interval,
        "repetitions": repetitions,
        "next_due": due.isoformat(),
    }


def validate_vault(root: Path) -> list[str]:
    cards, errors = load_cards(root)
    errors.extend(_duplicate_id_errors(cards))
    return errors


def _emit(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def common(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument(
            "--workspace",
            "--vault",
            dest="vault",
            required=True,
            metavar="WORKSPACE",
            help="Explicitly authorized Markdown workspace root directory",
        )
        subparser.add_argument(
            "--folder", default="Learning", help="Workspace-relative learning folder"
        )

    initialize = subparsers.add_parser("init", help="Initialize the isolated learning workspace")
    common(initialize)
    initialize.add_argument("--title", default="Learning Loop")

    due = subparsers.add_parser("due", help="Return due prompts without reference answers")
    common(due)
    due.add_argument("--on", default=date.today().isoformat())
    due.add_argument("--limit", type=int, default=3)

    start = subparsers.add_parser(
        "start", help="Refresh the recall calendar and return due prompts"
    )
    common(start)
    start.add_argument("--on", default=date.today().isoformat())
    start.add_argument("--limit", type=int, default=3)

    calendar = subparsers.add_parser(
        "refresh-calendar", help="Rebuild the recall calendar from active-card metadata"
    )
    common(calendar)
    calendar.add_argument("--on", default=date.today().isoformat())

    record = subparsers.add_parser("record", help="Record an attempt and update its schedule")
    common(record)
    record.add_argument("--card", required=True)
    record.add_argument("--rating", required=True, choices=sorted(RATINGS - {"new"}))
    record.add_argument("--summary", required=True)
    record.add_argument("--gaps", default="")
    record.add_argument("--evidence", default="")
    record.add_argument("--on", default=date.today().isoformat())

    validate = subparsers.add_parser("validate", help="Validate plugin-owned workspace state")
    common(validate)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            _emit(initialize_vault(args.vault, args.folder, args.title))
            return 0
        root = learning_root(args.vault, args.folder)
        if args.command == "due":
            if args.limit < 1:
                raise LearningLoopError("Limit must be at least 1")
            _emit(due_cards(root, _parse_date(args.on, "on"), args.limit))
            return 0
        if args.command == "start":
            _emit(start_session(root, _parse_date(args.on, "on"), args.limit))
            return 0
        if args.command == "refresh-calendar":
            _emit(refresh_recall_calendar(root, _parse_date(args.on, "on")))
            return 0
        if args.command == "record":
            _emit(
                record_attempt(
                    root,
                    args.card,
                    args.rating,
                    args.summary,
                    args.gaps,
                    args.evidence,
                    _parse_date(args.on, "on"),
                )
            )
            return 0
        errors = validate_vault(root)
        _emit({"valid": not errors, "errors": errors})
        return 1 if errors else 0
    except (OSError, LearningLoopError) as exc:
        _emit({"error": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
