#!/bin/sh
# Synthetic read-only setup adapter. Prints local paths/template; never writes.
set -eu
if [ "$#" != 3 ] || [ "$1" != --json ] || [ "$2" != --template ] || [ "$3" != checklist-template ]; then
  echo 'Expected: --json --template checklist-template' >&2
  exit 2
fi
python3 - <<'PY'
import json
from pathlib import Path

root = Path.cwd().resolve()
print(json.dumps({
    "FEATURE_DIR": str(root / "specs/001-invitations"),
    "AVAILABLE_DOCS": ["spec.md"],
    "TEMPLATE_CONTENT": (root / ".specify/templates/checklist-template.md").read_text(),
}))
PY
