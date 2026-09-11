# Haystack comparison: none / text_target / rag / graph, 4B readers

Reader run by Fable 2026-09-11 14:03–14:13 PDT on Astra's frozen contexts (frozen context hashes verified privately). Corpus: 32 records ingested of 108 planned (8 designated targets, 24 keyword
neighbors; no random records), plus one partially ingested record (a rename-related neighbor, with no document/chunk entry but shared graph updates during its failed attempt), frozen after a deterministic embedding-input-limit
failure; see [public protocol](protocol-public.json). Extractor Gemma3 12B local; embedder local.
Readers: Qwen3.5 4B and Gemma3 4B, seeds 11/29/47, the original `trial()` with the same tools and
three-turn budget. `none` and `text_target` rows are the existing controls, not rerun.

## Totals (correct actions / trials, mean prompt tokens per trial)

| Reader | none | text_target | rag (top_k 5 chunks) | graph (GRAPH_COMPLETION) |
|---|---:|---:|---:|---:|
| Qwen3.5 4B | 24/30 (378) | 23/30 (782; 1 malformed JSON) | **27/30** (1,534) | 23/30 (1,484; 1 malformed JSON) |
| Gemma3 4B | 16/30 (454) | 27/30 (1,518) | 22/30 (1,924) | 21/30 (1,886) |
| Both | 40/60 | 50/60 | **49/60** | 44/60 |

Paired by case, model, seed: rag vs none improved 10, regressed 1; graph vs none improved 10,
regressed 6; rag vs text_target improved 4, regressed 5; graph vs text_target improved 0,
regressed 6. No trial exhausted its turn budget; the largest observed prompt was 2,718 tokens
against the 8,192-token context setting. The one new error was Qwen graph corrected-count
seed 47: malformed JSON at the output cap. The full-text control has a separate
malformed-JSON row at that same case/model/seed.

## Evidence delivered in the frozen contexts

| Method | Target UUID in text | Target source in references | Relevant historical passage present |
|---|---:|---:|---:|
| rag | 9/10 | 9/10 | 9/10 |
| graph | 6/10 | 7/10 | 8/10 |

The first two measures are mechanical presence checks; the last is Astra's manual
passage audit, completed before inspecting action outcomes. Exact excerpts and offsets are retained privately. Both modes lack stop-loop evidence; graph
also lacks unsupported-preference evidence. Requested-actual and corrected-count
graph packets contain the needed text despite omitting source UUIDs. Voice-null
graph contains the actual null-result passage despite its absence from the source
reference list. Thus the earlier ID-prefix coverage interpretation was incorrect.

## Per case

| Case | none | text_target | rag | graph |
|---|---:|---:|---:|---:|
| changed-engine | 6/6 | 3/6 | **6/6** | 3/6 |
| context-flip | 3/6 | 6/6 | 3/6 | 6/6 |
| rename | 4/6 | 6/6 | 4/6 | 6/6 |
| changed-rename | 6/6 | 6/6 | 6/6 | 6/6 |
| stop-loop | 0/6 | 0/6 | 0/6 | 0/6 |
| misquote | 6/6 | 6/6 | 6/6 | 6/6 |
| unsupported-preference | 3/6 | 6/6 | 6/6 | 3/6 |
| requested-actual | 6/6 | 6/6 | 6/6 | 6/6 |
| corrected-count | 0/6 | 5/6 | 6/6 | 5/6 |
| voice-null | 6/6 | 6/6 | 6/6 | 3/6 |

## What the receipts say

**Similar totals hide different decisions.** RAG scores 49/60 versus 50/60 with the
designated full record, with four paired improvements and five regressions. Three
improvements are Qwen changed-engine; the fourth avoids a malformed-JSON failure
in the full-text corrected-count control. Regressions are Gemma rename (two seeds)
and context-flip (three). Both those RAG packets contain the relevant old lesson.
This is not evidence that retrieval is equivalent to direct record selection.

**A competing record can help, but its causal effect was not isolated.** In
changed-engine, no memory scores 6/6, the designated old context-flip record scores
3/6, RAG scores 6/6, and graph scores 3/6. The RAG packet includes an engine-wedge
neighbor whose situation matches the current observation: context already correct,
socket unresponsive. This accompanies recovery from harm induced by the designated
record, not an improvement over the no-memory control. We did not hold the packet
fixed and remove only that neighbor. Other text, order and framing also differ.

Both retrieval packets include the neighbor's raw text, including its false-alarm
and eventual-recovery account. Graph additionally includes a generated summary.
Qwen RAG seed29 correctly explains the matching engine-wedge pattern; seed11 chooses
correctly but muddles the explanation. Qwen graph seed29 says the context flip is
not the issue yet selects the context-flip action. Other graph seeds import the
historical recovery into the current situation. These are uptake and action-selection
failures despite delivered evidence, not simply missing text.

**Graph's six regressions against full text are all Gemma, in two cases.** Three
are unsupported-preference, where the specific corrective evidence is absent. Three
are voice-null, where the null result and p=0.60 are present. Gemma then claims that
p=0.60 establishes a large effect. Qwen passes all three graph voice-null trials.
A coverage-only explanation is therefore wrong; model response to the packet matters.

**Stop-loop remains 0/6 in each of these four conditions.** Neither retriever
delivers the sidecar/UserPromptSubmit lesson. The full-record control delivers it
but also scores 0/6, so retrieval failure and failure to use the record are distinct.
These fixtures cannot attribute all failures to one stage of the system.

**Changed-rename remains 6/6 in every condition.** The current task explicitly
provides completed-check receipts. This case shows no memory improvement here.

## Limits and reproducibility

Thirty-two completed records is a small, deliberately target-rich corpus. One
additional record failed; 75 planned records were not attempted. The partial
attempt updated shared graph/vector objects. Thirteen graph nodes and two edges
have timestamps during it; four graph contexts reference touched nodes (stop-loop,
rename, changed-rename, unsupported-preference). No pre-failure snapshot exists,
so we cannot isolate any change in their contents or effect on decisions. This is
a diagnostic under incomplete ingestion, not a clean product ranking.

The ten cases and three seeds per model are not 60 independent real-world situations.
Reader weights were not trained. Equal top_k does not equalize retrieval objects or
context budgets; no ablation isolated graph structure, summaries, order or the neighbor.

A separate local audit verified the full 120-cell new grid, exact context suffixes, source hashes, pass labels and pairings. The raw receipts contain private text and remain withheld. This report and [aggregate results](aggregate-results.json) disclose the measurements, but cannot independently reproduce the historical benchmark without that data.
