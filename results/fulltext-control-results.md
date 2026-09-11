# text_target control: the complete record, same everything else

Sixty trials used the same ten frozen cases, reader function, simulated tools, three-response budget, temperature 0.3 and seeds 11/29/47 as the delivery comparison. The designated full record replaced the repaired 500-character preview. Readers were Qwen3.5 4B and Gemma3 4B. Local inference shared a machine with extraction work, so timings are not comparable. One JSON parse failure counts as incorrect. Exact private fixtures and trial responses are withheld.

## Totals (including the earlier delivery conditions for comparison)

| Model | none | baseline | transport | repaired | **text_target** |
|---|---:|---:|---:|---:|---:|
| Qwen3.5 4B | 24/30 (378 tok) | 25/30 (493) | 25/30 (455) | 26/30 (1,490) | **23/30 (782)** |
| Gemma3 4B | 16/30 (454) | 23/30 (875) | 24/30 (708) | 21/30 (799) | **27/30 (1,518)** |
| Both | 40/60 | 48/60 | 49/60 | 47/60 | **50/60** |

Tokens are mean prompt tokens summed over a trial's turns.

## Paired against `transport` (same case, model, seed)

Improved 3, regressed 2, unchanged 55 of 60 pairs.

| Case | transport /6 | text_target /6 |
|---|---:|---:|
| context-flip | 3 | **6** |
| changed-engine | 4 | **3** |
| corrected-count | 6 | 5 |
| stop-loop | 0 | **0** |
| the other six | 6 each | 6 each |

## What it settles

**Missing preview text alone does not explain these stop-loop failures.** The full record contains the corrective implementation, but both models selected the failed mechanism in all six trials. Qwen's reasons treated the historical failure as a recommendation; Gemma's reasons were more generic. The correction's presence did not ensure its use.

**More text raises Gemma's score and lowers Qwen's in this run.** Gemma's gain is
context-flip (0/3→3/3 for Gemma; 3/6→6/6 across both readers). Qwen loses one decision
on changed-engine (1/3→0/3): the fuller old remedy is applied
against current observations that say the context is already orbstack. That is the same
shape as the overnight repaired-condition result and the 27B row: an intact old lesson can
be the wrong lesson when circumstances changed.

Qwen's other lost score is corrected-count, seed 47: its response reaches the 200-token
output cap with an unterminated JSON reason. Its partial output names choice 0, but is
not a valid finish response and stays failed under the existing protocol. Therefore
the two-point reduction must not be described as two wrong remedy choices. This is
one concrete action regression plus one output-format/budget failure.

**Right index, wrong reason, again.** Gemma passed changed-engine 3/3 with reasons that name
a context flip as the root cause, which is the option it did not choose. Action labels
overstate understanding on this case; the receipts are there for anyone who wants to
score reasons.

## What it does not settle

Selection was held fixed: the reader received the designated record. Whether retrieval finds it or a more relevant alternative is evaluated separately in the [haystack comparison](haystack-results.md).
