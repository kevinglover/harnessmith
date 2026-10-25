"""Harmless synthetic hook: append a local marker and checklist hash only."""

import hashlib
import json
from pathlib import Path
import sys


def main():
    allowed = {
        "pilot-pre-marker", "pilot-post-marker", "pilot-optional-pre",
        "pilot-optional-post", "pilot-disabled-pre", "pilot-disabled-post",
        "pilot-conditional-pre", "pilot-conditional-post",
    }
    if len(sys.argv) != 2 or sys.argv[1] not in allowed:
        raise SystemExit("Unknown synthetic command")
    root = Path(__file__).resolve().parent.parent
    target = root / "specs/001-invitations/checklists/security.md"
    marker = root / ".pilot/events.jsonl"
    for path in (target, *target.parents, marker):
        if path.is_symlink():
            raise SystemExit("Synthetic hook refuses symlinks")
    event = {
        "command": sys.argv[1],
        "target_exists": target.is_file(),
        "target_sha256": hashlib.sha256(target.read_bytes()).hexdigest()
        if target.is_file() else None,
    }
    with marker.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True) + "\n")
    print(json.dumps(event, sort_keys=True))


if __name__ == "__main__":
    main()
