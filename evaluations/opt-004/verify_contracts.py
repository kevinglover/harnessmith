"""Read-only verification of prospective OPT-004 fixtures, pins and packages.

No provider, host, fixture helper or collector is invoked. Run from repository
root: ``python3 evaluations/opt-004/verify_contracts.py``.
"""

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "evaluations/opt-004"
sys.path.insert(0, str(ROOT))

from harnessmith.verification import verify_compiled_package


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_pin(record):
    directory = ROOT / record["path"]
    actual = []
    for path in sorted(directory.rglob("*")):
        require(not path.is_symlink(), "symlink in pinned directory: " + str(path))
        if path.is_file():
            actual.append({"path": path.relative_to(directory).as_posix(),
                           "sha256": digest(path.read_bytes()), "bytes": path.stat().st_size,
                           "mode": oct(path.stat().st_mode & 0o777)})
    require(actual == record["files"], "file inventory drift: " + record["path"])
    raw = json.dumps(actual, sort_keys=True, separators=(",", ":")).encode()
    require(digest(raw) == record["inventory_sha256"], "inventory hash drift: " + record["path"])


def main():
    pins = read_json(BASE / "fixture-pins.json")
    for name, filename in (("contracts", "contracts.json"), ("catalog", "catalog.json"),
                           ("packages_index", "packages.json"), ("preparer", "prepare_contracts.py")):
        require(digest((BASE / filename).read_bytes()) == pins[name + "_sha256"], filename + " pin drift")
    for key in ("workspace", "hook_skills", "catalog_skills"):
        check_pin(pins[key])
    packages = read_json(BASE / "packages.json")["packages"]
    verified = 0
    for record in packages:
        check_pin(record["canonical"])
        require(digest((ROOT / record["recipe"]).read_bytes()) == record["recipe_sha256"], "recipe drift")
        if "compiled" in record:
            check_pin(record["compiled"])
            report = verify_compiled_package(ROOT / record["compiled"]["path"])
            require(report.valid, "independent package verification failed: " + str(report.as_dict()))
            require(report.checks.get("regeneration") == "passed",
                    "source/recipe regeneration unavailable: " + str(report.as_dict()))
            verified += 1
        else:
            require((record["fixture"], record["target"], record["status"]) ==
                    ("explicit", "generic", "expected-offline-rejection"), "unexpected missing package")
    contracts = read_json(BASE / "contracts.json")
    require(contracts["collection_enabled"] is False, "prospective contract must not enable collection")
    require(contracts["whole_trajectory_deadline_seconds"] == 180, "deadline changed")
    require(contracts["repetitions"] == 3, "repetition count changed")
    cases = {case["id"]: case for case in contracts["cases"]}
    expected_turns = {"R0": 1, "R1": 1, "R2": 1, "D1": 1, "D2": 1, "D3": 2,
                      "W1": 1, "W2": 1, "W3": 1, "H1": 2, "H2": 2,
                      "H3": 1, "H4": 1, "P1": 4, "L1": 3, "L2": 1,
                      "L3": 2, "L4": 2, "L5": 2}
    require(set(cases) == set(expected_turns), "bounded case catalog changed")
    for case_id, expected in expected_turns.items():
        require(cases[case_id]["max_task_turns"] == expected == len(cases[case_id]["prompts"]),
                "turn cap or exact prompts changed: " + case_id)
        require(cases[case_id]["physical_threads"] == (2 if case_id == "L4" else 1), "thread cap changed")
    new_cells = [(host, case) for host in ("codex", "claude", "cursor") for case in cases.values()
                 if not (host == "codex" and case["id"] in ("R0", "R1", "R2"))
                 and not (host != "claude" and case["id"] == "L5")]
    require((len(new_cells), len(new_cells) * 6,
             sum(c["physical_threads"] for _, c in new_cells) * 6,
             sum(c["max_task_turns"] for _, c in new_cells) * 6) == (52, 312, 330, 498),
            "completion-plan ceilings no longer match")
    catalog = read_json(BASE / "catalog.json")
    entries = catalog["entries"]
    require(len(entries) == 16 and entries[7]["name"] == "speckit-checklist", "catalog count or target position changed")
    require([e["name"] for e in entries] == sorted(e["name"] for e in entries), "catalog order changed")
    require(sum(e["kind"] == "near-topic" for e in entries) == 7 and
            sum(e["kind"] == "unrelated" for e in entries) == 8, "catalog composition changed")
    for case_id in ("D1", "D2"):
        prompt = cases[case_id]["prompts"][0]
        require(not any(e["name"] in prompt for e in entries), "explicit skill hint in discovery prompt")
    for case_id in ("R0", "R1", "R2"):
        case = cases[case_id]
        source = ROOT / case["prompt_source"]
        require(digest(source.read_bytes()) == case["prompt_source_sha256"], "reference prompt source drift")
        require(case["prompts"] == [read_json(source)["prompt"]], "reference prompt differs from declared source")
    original = BASE / "workspace/append/specs/001-invitations/checklists/security.md"
    require(len(original.read_bytes()) == 694, "append baseline size changed")
    print("Verified 19 bounded contracts, 16 catalog entries, %d regenerated packages, all fixture/source/recipe pins and 312/330/498 ceilings; no live calls." % verified)


if __name__ == "__main__":
    main()
