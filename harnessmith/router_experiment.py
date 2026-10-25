"""Reviewed experimental package loading; not a compiler transformation."""

import hashlib
import json
from pathlib import Path
import re


def load_router(path, source_bytes):
    path = Path(path)
    if path.is_symlink():
        raise ValueError("router package cannot be a symlink")
    review_path = path.with_suffix(".review.json")
    review_bytes = review_path.read_bytes()
    review = json.loads(review_bytes)
    if (
        review.get("kind") != "reviewed-semantic-redesign"
        or review.get("source_sha256") != hashlib.sha256(source_bytes).hexdigest()
    ):
        raise ValueError("router review must pin the canonical source")
    files = {}
    for item in sorted(path.rglob("*")):
        if item.is_symlink():
            raise ValueError("router package cannot contain symlinks")
        if item.is_file():
            if item.stat().st_mode & 0o111:
                raise ValueError(
                    "router experiment only accepts nonexecutable documents"
                )
            files[item.relative_to(path).as_posix()] = item.read_bytes()
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    if "SKILL.md" not in files or hashes != review.get("files"):
        raise ValueError("router package differs from reviewed hashes")
    source = source_bytes.decode()
    for name, spans in review.get("verbatim_source_spans", {}).items():
        expected = "".join(
            source[source.index(start) : source.index(end) if end else len(source)]
            for start, end in spans
        )
        if files.get(name) != expected.encode():
            raise ValueError("router source retention failed: " + name)
    if not review.get("verbatim_source_spans") or not review.get("semantic_changes"):
        raise ValueError(
            "router review requires retention mapping and semantic changes"
        )
    return files, {
        "kind": review["kind"],
        "review_sha256": hashlib.sha256(review_bytes).hexdigest(),
        "semantic_changes": review["semantic_changes"],
    }


def quality_checks(scenario_id, output):
    """Structural/exact-content checks, not a semantic quality verdict."""
    checks = []
    if scenario_id == "checklist-core-security-codex":
        items = re.findall(r"^\s*- \[([ xX])\] (CHK\d+)\s+(.+)$", output, re.M)
        checks.append(
            (
                "quality-item-format",
                len(items) == 4
                and [i[1] for i in items] == ["CHK001", "CHK002", "CHK003", "CHK004"]
                and all(i[0] == " " and "?" in i[2] for i in items),
                "exactly four unchecked sequential questions",
            )
        )
        markers = ("Spec §", "Gap", "Ambiguity", "Conflict", "Assumption")
        checks.append(
            (
                "quality-traceability",
                len(items) == 4
                and all(
                    any(m in b for m in markers)
                    for _, _, line in items
                    for b in [" ".join(re.findall(r"\[([^]]+)\]", line))]
                ),
                "each requested item has a traceability marker",
            )
        )
    if scenario_id in (
        "checklist-optional-some-codex",
        "checklist-optional-most-codex",
    ):
        quotes = [
            "Are retry/timeout requirements defined for external dependencies? [Coverage, Gap]"
        ]
        if scenario_id == "checklist-optional-some-codex":
            quotes.append("Is versioning strategy documented in requirements? [Gap]")
        else:
            quotes.extend(
                [
                    "Are security failure/breach response requirements defined? [Gap, Exception Flow]",
                    "- [ ] CHK001 - Are the number and layout of featured episodes explicitly specified? [Completeness, Spec §FR-001]",
                ]
            )
            checks.append(
                (
                    "quality-word-limit",
                    len(output.split()) < 250,
                    "under 250 words including commentary",
                )
            )
        checks.append(
            (
                "quality-verbatim-quotes",
                all(q in output for q in quotes),
                "requested source questions quoted verbatim",
            )
        )
    if not checks:
        raise ValueError("no enhanced quality rubric for scenario: " + scenario_id)
    return checks
