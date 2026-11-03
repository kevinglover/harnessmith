#!/usr/bin/env python3
"""Harmless fixture operations. Not executed by offline preparation."""
import argparse
import json
from pathlib import Path
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument("operation", choices=["pre", "post", "optional", "disabled", "conditional", "pre-fail", "post-fail", "approval-denied", "approval-granted", "interrupt", "after-interrupt"])
args = parser.parse_args()
root = Path.cwd().resolve()
observed = root / ".opt004-observed"
observed.mkdir(exist_ok=True)
with (observed / "actions.jsonl").open("a", encoding="utf-8") as handle:
    handle.write(json.dumps({"operation": args.operation, "phase": "started"}) + "\n")
    handle.flush()
print("fixture:" + args.operation + ":started", flush=True)
if args.operation == "interrupt":
    time.sleep(120)
code = 17 if args.operation == "pre-fail" else 23 if args.operation == "post-fail" else 0
with (observed / "actions.jsonl").open("a", encoding="utf-8") as handle:
    handle.write(json.dumps({"operation": args.operation, "phase": "completed", "exit_code": code}) + "\n")
print("fixture:" + args.operation + ":completed", flush=True)
if code:
    print("synthetic " + args.operation + " failure", file=sys.stderr, flush=True)
sys.exit(code)
