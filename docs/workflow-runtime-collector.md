# Approved six-session workflow collector

On 2026-10-24 the user approved exactly six GPT-6 Luna sessions for the
[frozen workflow pilot](workflow-fidelity-pilot.md), after implementation and
validation of a write-capable collector. This approval does not cover retries,
additional cases, other models, or promotion of the router.

That authorization is now consumed: all six sessions completed. See the
[results and retained evidence](workflow-fidelity-results.md). No replacements
or additional live sessions are authorized by the command below.

`harnessmith.workflow_runtime` implements that bounded batch. GPT-6 Luna and low
reasoning are fixed, with one fresh session for each original/router case in the
approved order. There is no sample-count, model-override, resume or retry option.
Collection requires `--enabled` and a new output directory; existing attempt
markers and reports cannot be overwritten. Ordinary tests use a fake stdio
server and are labeled mock/offline-simulation.

```bash
python3 -m harnessmith.workflow_runtime --enabled \
  --output /tmp/opt004-workflow-luna-live-20261024 --timeout 180
```

That command consumes the six-session authorization; it is not a repeatable
benchmark example. Use an output directory outside the repository so ancestor
project discovery cannot add the original checkout to the sandbox. Retain the
finished bundle under gitignored local evidence afterward without rerunning it.

## Permission and lifecycle controls

The collector uses the installed CLI's generated protocol schema and
[official App Server documentation](https://learn.chatgpt.com/docs/app-server).
It verifies the returned model, reasoning effort, cwd, workspace roots, approval
policy, sandbox flags and absence of ambient instruction sources before starting
a model turn. It explicitly sends workspace-only write permission, network off,
no extra `/tmp` or environment-temp writable roots, and approval `never`.
Unrelated discovered skills are disabled; web search and multi-agent tools are
disabled. All case prompts and grading rules remain unchanged.

The local CLI's legacy sandbox schema does not expose the newer restricted-read
controls described in current documentation. Host reads remain OS-permitted;
the prompts restrict scope, and observed reads outside the fixture are rejected.
This is not an OS container or a claim that arbitrary host files are unreadable.
The local non-model sandbox preflight confirms allowed workspace writes and denied
outside-workspace writes, `/tmp` writes, and socket access. It uses synthetic
files and no credentials or model turns.

Authentication is copied into a private temporary Codex home outside the
workspace, with mode 0600, and removed after each attempt. User configuration is
not copied. Parent and tool descendants are terminated before final snapshots.
The collector stops immediately on server error/retry notices, model rerouting,
unexpected server requests, timeout or malformed protocol output; it never
starts a replacement session. Preflight failures also remain recorded and stop
the batch. Ordinary completed fidelity failures remain in the six-session batch.

## Evidence and interpretation

Each session retains its exclusive attempt record, raw JSONL, exact stdout and
stderr, original/final workspace snapshots and inventories, prompt, package and
fixture provenance, normalized observation, frozen checker results and final
result. Malformed stdout, partial answers and incomplete attempts are preserved.
Snapshots do not depend on successful normalization. The batch journal records
attempts and results, including any unattempted slots after a stop.

The environment record pins CLI/model/mode/instrumentation/configuration and
collector-source hashes. Underlying provider model snapshot remains unreported;
provider caches remain uncontrolled. Final cumulative token usage is used once,
with cached and uncached input separated; no billing or general efficiency claim
is inferred from six observations.

`harnessmith.workflow_trace` maps actual started/completed events to the frozen
observation contract. Whole bounded shell commands are parsed independently of
Codex's best-effort `commandActions` annotations. Recognized operations include
read commands, the exact synthetic setup/hook adapters, bounded directory/listing
operations, file-change events and literal quoted heredoc artifact writes.
Unknown commands, dynamic scripts, unsupported changes and unsuccessful operations
remain failures. Hook/setup/write overlap is checked against start and completion
indices. Neither model claims nor marker files alone prove execution.

No grading criteria are relaxed after viewing results. Content and raw-trace
reviews are recorded separately from automated checks. The frozen checker still
reports promotion eligibility false; live review cannot turn the router's
authored semantic changes into a content-preserving compiler transformation.
