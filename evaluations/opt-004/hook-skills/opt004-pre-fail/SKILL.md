---
name: opt004-pre-fail
description: Run the synthetic OPT-004 pre-fail fixture hook when invoked.
---
# Fixture hook

Run exactly `python3 .opt004/fixture_action.py pre-fail` from the fixture workspace.
Wait for completion and report its actual exit status and output. Do not retry.
