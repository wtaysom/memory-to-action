# Scale row: Gemma3 27B on the frozen cases

One local Gemma3 27B reader used the same frozen cases, seeds and four conditions as the 4B delivery comparison. There were 120 trials, none dropped. Timing is wall-clock on a shared machine. Exact fixtures and raw responses remain private.

| Condition | Correct / 30 | Median seconds | Mean prompt tokens |
|---|---:|---:|---:|
| none | 27 | 7.7 | 505 |
| baseline (original hook) | 26 | 10.6 | 855 |
| transport (preview intact) | 26 | 9.3 | 816 |
| repaired (metadata + guidance) | 27 | 12.2 | 921 |

Paired against baseline: transport 0 improved, 0 regressed; repaired 1 improved, 0
regressed (changed-engine, seed-level).

Per scenario (correct of 3): every scenario is 3/3 in every condition except
**stop-loop** (0/3 in all four 27B conditions) and **changed-engine** (none 3,
baseline 2, transport 2, repaired 3). The latter is consistent with an old remedy
interfering with current evidence. The richer condition changes metadata and
guidance together; this comparison does not isolate guidance as the cause.

## What this says

1. At 27B the frozen cases are mostly solvable from the task and choices alone. The
   benchmark is near its ceiling without memory. In this battery the two 4B readers
   collectively improved from none 40/60 to transport 49/60, while this 27B reader
   showed no net benefit. This is not a general causal claim about model size.
2. Memory can still hurt at scale: an intact old lesson reapplied to a changed
   situation (changed-engine) coincided with one fewer correct decision out of three.
   The richer presentation recovered that one decision; guidance was not isolated.
3. stop-loop is 0/3 in every 27B condition. In the original 4B trials, Gemma's
   baseline scored 2/3, while all other model/condition combinations scored 0/3.
   Those two label-passing reasons do not explain the corrective implementation.
   The later [full-record control](fulltext-control-results.md) also failed this case, so preview truncation alone cannot explain it.
4. For the Cognee haystack comparison, the discriminating cases are the ones a 4B
   model fails without memory (gemma3:4b none column: stop-loop 0/3, corrected-count
   0/3, unsupported-preference 0/3, context-flip 0/3, rename 1/3) and the two
   changed-circumstances cases. Running the graph comparison on 27B would mostly
   measure the ceiling. Retain all ten cases in the primary score; a subgroup
   selected using these earlier failures is exploratory, not a newly weighted
   primary evaluation.

See [delivery results](delivery-trials-results.md) for the small readers. These tables report private-data results rather than a publicly rerunnable benchmark.
