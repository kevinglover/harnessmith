---
name: opt004-post
description: Run the synthetic OPT-004 post fixture hook when invoked.
---
# Fixture hook

Run exactly `python3 .opt004/fixture_action.py post` from the fixture workspace.
Wait for completion and report its actual exit status and output. Do not retry.
