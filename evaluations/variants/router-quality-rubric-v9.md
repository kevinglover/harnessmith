# Fidelity rubric v9 — discovery attribution and command boundaries

Prospective rules for authored router v7, checker/collector v8 and normalizer v7
(observation schema 7, report schema 8). All hard gates from
[v8](router-quality-rubric-v8.md) and promotion requirements from
[v2](router-quality-rubric-v2.md) remain. The [v7 result](../../docs/workflow-fidelity-v7-results.md)
stays frozen at **0/1** full automated and complete reviewed gates. No historical
trace is replayed or regraded.

## Bounded terminal-discovery attribution

A successful terminal `rg --files LITERAL_DIRECTORY`, alone or following only
literal full `cat` reads separated by newlines, semicolons or `&&`, may receive
a discovery certificate. Require matching successful lifecycle endpoints and
source/cwd/scope, a verified pinned inventory, a safe existing visible directory,
exact ordered read-output prefix and the complete unique visible file listing.
The listing order may vary. No extra flags, redirects, pipelines, fallbacks,
dynamic expressions, hidden roots, symlink components, missing roots or unknown
output gain this certificate. Prior mutation, failed/unknown operations, scope
conflicts and overlapping/open lifecycles also prevent proof. These constraints
are prospective attribution rules, not proof of OS file access or shell behavior.

Only the specifically proven terminal unknown and its associated artificial
fidelity issues may be replaced. Existing bounded standalone/`&&` discoveries
also require this proof; malformed output cannot retain older credit. Actual
failed commands and unrelated issues remain failures. Captured commands are
never executed for interpretation. Other previously supported grammar retains
its existing bounds; this is not a general shell parser.

## Command-separation gates

`extension-check-isolated-from-other-operations` requires a successful,
lifecycle-backed extension config read or pinned absence certificate in its own
command envelope, without discovery, unrelated reads, setup, hooks, writes or
unknown operations. Corroborated read-only cache-warning diagnostics may accompany
the proof. Absence labels alone cannot satisfy it.

`context-reads-isolated-from-discovery-and-mutation` requires every required
context path to have successful, lifecycle-backed read evidence. Each such
envelope, and every other observed read envelope including template, optional
context and package reads, may contain only successful reads and explicitly recognized passive
literal-label/read-only cache diagnostics. A newline or semicolon does not create
a separate action. A fully attributed mixed read/discovery command still fails
this workflow gate. Unknown or missing evidence never creates a vacuous pass.

`discovery-isolated-from-other-operations` allows discovery only alongside other
successful discovery and the same narrow passive diagnostics, all with unique
matching successful lifecycle records. Reads, extension checks, setup, hooks,
writes and unknowns in that envelope fail. Discovery itself is optional; its
absence does not establish coverage of discovery grammar.

## Report dimensions separately

| Dimension | Passing requirement |
| --- | --- |
| Content correctness | Three distinct traceable requirements-quality questions: measurable expiration, expired/reused outcomes and retention. No invented policy; separate semantic review. |
| Formatting | Unchecked CHK008–010, question/bracket syntax, template structure and accurate final path/count/append/focus/depth/reviewer reporting. |
| Reference behavior | Full pinned generation reference completes before any project action; only task-relevant references loaded. |
| Workflow fidelity | All inherited gates, plus all three command-boundary gates. Extension evidence before separate setup; full context; exact original prefix and checkbox states; separate complete postwrite read; factual commentary/final narration, including Git claims. Real failed discovery remains disclosed and failed. |
| Efficiency | Input/cache/output/latency/read counts descriptive only. No matched baseline or replication: efficiency not evaluated. |

Preserve anonymous semantic-first packets and disclose reviewer identity/prior
exposure before viewing grades, traces or usage. Then inspect complete raw actions
and material narration. Bounded lexical screens do not establish truthful narration.
Retain pending grades and review sidecars separately. One passing append sample
cannot establish reliability, hooks coverage for router v7, efficiency, compiler
equivalence, promotion or OPT-004 completion. Leave inline remains the default.

The [v8 proposal](../../docs/workflow-fidelity-pilot-v8.md) is exactly one fresh
GPT-6 Luna low append session, one turn, no retry/replacement/expansion or extra
judge. It is not authorized or launched. A different valid model-selected command
does not establish live coverage of the new parser grammar.
