# OPT-004 O3 durable capture — November 3, 2026

Follow-up: the [transport and stage increment](opt-004-collection.md) now adds
continuous stream capture, durable mock scheduling and bounded Codex observation.
The foundation checkpoint below records the earlier increment; the linked
follow-up supersedes its pending shared-transport and scheduling statements.

Status: **retention foundation implemented and tested offline; O3 remains partial**.
The new [capture module](../harnessmith/native_capture.py) is additive. Historical
collectors, instruments and scores are unchanged. No native adapter is qualified
and no live session is authorized or launched by this work.

## Implemented boundary

`collect_mock_attempt` captures exactly one synthetic attempt in a new evidence
directory outside the workspace. It rejects disabled calls and native mode before
calling the source. It has no executable selection, provider credentials, native
transport, retry or batch loop. The source and decoder are trusted injected test
code; the mock flag is a provenance label, not a sandbox for arbitrary Python.

`AttemptJournal` exclusively creates the attempt directory and commits a start
record before invoking the source. Content-addressed blobs retain exact bytes;
blob writes and journal appends flush and fsync before returning, and newly
created directory entries are synced. Raw receive bytes are persisted before
calling the decoder, including malformed UTF-8/JSON. Send, stderr and controller
channels are retained separately. A future transport must record outbound bytes
before sending and continuously capture both output streams; this API alone does
not implement that transport. A send record proves intent, not host receipt.

Decoded records are retained before shape validation. Accepted events and usage
intervals retain the native contract's causal identities and baselines. Primary
raw references must identify the just-captured bytes; synthetic event timestamps
use the journal's monotonic clock and origins must remain mock. Invalid decoded
records remain evidence without entering the accepted trajectory. The decoder
receives bytes, their reference and elapsed time, without expected-answer input.
This interface is not qualification of invocation attribution: a reviewed host
normalizer must still establish invocation independently from native operations.

Before/after snapshots retain file bytes, permission modes, symlink targets and
empty directories. They do not follow symlinks or read special files. Observable
concurrent mutations fail closed. The workspace must be quiescent and isolated;
these are not atomic filesystem snapshots or OS file-access tracing. ACLs,
extended attributes and ownership are outside this snapshot format.

EOF ends capture, not behavior verification. Contract integrity findings remain
separate. Usage totals are unavailable when lifecycle/usage integrity fails,
when counters are unavailable, or when capture is incomplete/interrupted.
No missing measurement becomes zero and no expected response creates invocation
evidence. Resume/fork/compaction accounting policies remain unqualified.

## Failure and recovery

Timeout, keyboard interrupt and ordinary source/decoder exceptions are retained,
followed by a best-effort after snapshot, typed partial trajectory and terminal
record. The original exception is then re-raised. An existing attempt directory
cannot be reused, including after failure. A future batch controller must stop on
failure and count the consumed attempt before considering any next slot.

`recover_attempt` is read-only. It inspects the intact journal prefix, checks
sequence/time order and blob hashes/references (including snapshot file blobs),
and reports torn tails, corrupt/missing blobs and absent terminal records. It
never truncates or repairs evidence. A process killed after a committed raw
record leaves a recoverable incomplete attempt; no after snapshot or terminal
record is invented. Recovery is an integrity inspection, not a normalizer or
behavior regrade, and does not resume collection.

Storage failures can prevent subsequent error or terminal writes. They propagate
and must stop the future batch. Fsync provides the filesystem's durability
boundary, not a guarantee against hardware loss. Recovery assumes a private,
controller-owned evidence directory and is not an untrusted archive importer.

## Verification and remaining O3 work

The [12 capture tests](../tests/test_native_capture.py) cover raw-before-decoder
ordering, exact malformed bytes and stderr, unknown usage, causal failures,
partial source failures, keyboard interruption, timeout, an abruptly exiting
child process, damaged journal tails, missing/corrupt blobs, snapshot fidelity,
unsupported files, bad backing, disabled/native gates and attempt reuse.
Together with the 26 native-contract tests, **38 focused tests pass**. The offline
contract verifier also passes 19 contracts, 16 catalog entries, 11 regenerated
packages, all pins and unchanged stage ceilings.

```bash
python3 -m unittest discover -s tests -p 'test_native*.py' -v
python3 evaluations/opt-004/verify_contracts.py
```

Remaining O3 deliverables:

- Bind versioned native transports and normalizers for each retained host/case;
  establish invocation from native evidence and retain request/approval IDs.
- Qualify effective permissions, isolated native roots and lifecycle accounting
  against the O2 binding requirements before enabling native launch.
- Add continuous raw stream capture, deadline/process cleanup and partial result
  retention around the actual host transport, including transport startup errors.
- Pin normalization policies, complete usage backing, stage manifests and
  per-stage attempt ceilings; persist a batch slot before host launch and stop
  on collection failure. This single-attempt module is not that scheduler.
- Run O5 fake-server transport and permission controls plus independent review
  before seeking approval for any live stage. O4 operation verification remains
  a separate pending deliverable.
