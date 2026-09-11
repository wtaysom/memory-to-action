# From remembering a correction to using it

A memory system can retain a correction while an agent continues acting on the old understanding. We wanted to locate where that happens: in delivery, in retrieval, or in the reader's use of the evidence. This account combines an overnight delivery repair with a Cognee evaluation conducted on 11 September 2026.

## Start with a mechanical fault

A newline-based parser was cutting off recalled memory previews. Across a 5,725-record snapshot, it lost 377,622 of 2,668,458 intended preview characters: 14.2%. Some continuations contained corrections. A repaired parser preserved all intended previews exactly.

We then tested decisions, rather than assuming byte preservation guaranteed better behavior. Ten simulated maintenance situations, two local 4B readers, three seeds and four delivery conditions produced 240 trials. Correct choices out of 60 were: no memory 40, original delivery 48, repaired transport 49, richer framing 47. The richer framing changed metadata and historical-context guidance together, so their individual effects were not isolated. The small transport fix was retained; the richer presentation remained opt-in.

A separate Gemma3 27B run scored 27/30 without memory and 26/30 with either original or repaired transport. Most choices were already solvable from the task alone at that size. That is a limitation of this battery, not a general finding that larger models do not need memory. [Delivery results](../results/delivery-trials-results.md), [27B results](../results/scale-27b-results.md).

## Separate delivery from selection

The first trials handed the reader a designated historical record. They could measure rendering and uptake, but could not show whether a retriever would find useful history.

A complete-record control scored 50/60, compared with 49/60 for the repaired 500-character preview. Three paired decisions improved and two regressed. One regression was a wrong remedy; the other was malformed JSON at the output cap. The fuller history helped one reader and hurt the other overall. In one persistent failure case, the corrective passage was fully present but both readers still chose incorrectly. Preview truncation alone could not explain that failure. [Full-record control](../results/fulltext-control-results.md).

We next used Cognee 1.5.4 to select context from a larger set. The planned ingestion held eight distinct designated source records and 100 keyword-selected neighbors. The source set was deliberately target-rich. Some supposed distractors were actually better evidence than the designated record for a changed situation.

Local Gemma3 12B performed extraction; a local embeddinggemma model supplied embeddings. We used the same task query and top-k setting for text and graph retrieval, then froze the returned packets before running the readers. Both conditions used the original readers, seeds, choices, tool simulation and response budget. The no-memory and full-record controls were reused from earlier runs.

## What Cognee contributed

| Reader | No memory /30 | Designated record /30 | Text retrieval /30 | Graph retrieval /30 |
|---|---:|---:|---:|---:|
| Qwen3.5 4B | 24 | 23 | 27 | 23 |
| Gemma3 4B | 16 | 27 | 22 | 21 |
| Combined /60 | 40 | 50 | 49 | 44 |

Text retrieval improved ten trials and regressed one against no memory. Graph retrieval improved ten and regressed six. Against the designated-record control, text retrieval improved four and regressed five; graph improved none and regressed six. These are paired changes on the same case, model and seed.

The relevant historical passage was present in nine of ten text packets and eight of ten graph packets. Those judgments came from passage inspection before inspecting action outcomes. Counting source IDs alone underestimated coverage: some graph packets contained the passage without naming its source in the expected place.

Three examples make the numbers useful. They are paraphrased in [EXAMPLES.md](EXAMPLES.md); these are explanations of the measured cases, not substitute fixtures that generated the scores.

**Competing old remedies.** The current task described an unresponsive Docker engine while its context was already correct. An old context-switching lesson led Qwen to choose incorrectly in all three full-record trials. Text retrieval also supplied an account of an engine wedge, and Qwen chose correctly in all three. But no memory also passed all three. This was recovery from misleading history rather than an improvement over current observations alone. Graph retrieval contained the same neighbor's raw text but Qwen failed all three; surrounding material, summary and ordering differed. We cannot attribute the difference solely to finding the neighbor.

**Delivered evidence, wrong inference.** A graph packet contained an explicit null-result passage, including p = 0.60. Gemma treated it as establishing a large effect in all three trials, despite interpreting the full-record control correctly in all three. Qwen handled the graph packet correctly. Missing evidence cannot explain that failure; the reader's response to the packet matters.

**A failed mechanism read as a recipe.** In a stop-loop case, neither retrieval method found the needed correction, and both scored 0/6. Supplying the full record also scored 0/6. Qwen's explanations adopted the recorded failed mechanism as a recommendation; Gemma's explanations were less specific. The four main conditions all failed this case, but an earlier delivery condition did produce two correct labels. We therefore do not claim that every presentation or model must fail.

The largest observed prompt in the new reader trials was 2,718 tokens against an 8,192-token context setting. Initial context overflow does not explain these results. The graph condition and reused full-record control each contain one malformed-JSON failure, both Qwen, counted incorrect. Correct action labels sometimes coexisted with faulty explanations, so these counts do not establish sound reasoning or successful operations. [Detailed results](../results/haystack-results.md).

## The ingestion failure limits the comparison

The build completed 32 records: all eight designated sources and 24 neighbors. The next attempt encountered embedding input beyond the server's limit and eventually reached the enclosing record timeout. Seventy-five planned records were never attempted.

The failed attempt had no document/chunk index entry, but 13 shared graph nodes and two edges had update timestamps during it. Four graph packets referenced touched nodes. Without a pre-failure snapshot, we cannot isolate whether their contents changed or affected decisions. The frozen result is therefore a diagnostic under incomplete ingestion. It is not a clean 32-record product benchmark, and adding records could introduce helpful evidence as well as difficulty.

Along the way we reproduced three local-adapter issues: schema routing based on model-name capability lookup, an embedding batch beyond server capacity, and an oversized embedding input whose error was retried unchanged. The [adapter report](../diagnostic/COGNEE-NOTES.md) distinguishes observed behavior, workarounds, suggested fixes and the limits of its synthetic reproduction.

## What we would build next

A useful memory must help discriminate the present situation: which old remedy applies, which apparent instruction records a failure, and which correction invalidates an earlier assumption. That gives “a more refined disposition to act” a testable meaning without claiming these trials demonstrate a human capacity for responsibility.

The next test should keep a packet fixed and change one thing: remove the competing record, change the summary, or change ordering. Score the next action and its explanation, then extend to actual tool consequences and held-out situations. We have candidate failure mechanisms, not their isolated causes.

Publicly this package provides aggregate historical results, paraphrased cases and offline synthetic adapter checks. Private source records, exact historical fixtures, retrieval packets and raw responses remain withheld. The adapter checks can be rerun here; the historical benchmark cannot. The central finding is narrower and useful: **the correction can survive retrieval and still fail to govern the next action.**
