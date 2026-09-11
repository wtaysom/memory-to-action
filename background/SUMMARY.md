# The correction arrived. Did the decision change?

We tested whether retrieved history helps an agent choose its next action. The test used ten simulated maintenance situations drawn from a persistent-memory project's history, two local 4B readers, and three seeds per situation. Higher scores mean more choices matching the predefined expected action.

| Context supplied | Correct choices / 60 | Relevant historical passage delivered |
|---|---:|---:|
| No memory | 40 | — |
| Designated full record | 50 | Supplied directly |
| Cognee text retrieval | 49 | 9/10 situations |
| Cognee graph retrieval | 44 | 8/10 situations |

Text retrieval improved ten trials and regressed one against no memory. Against the designated-record control, it improved four and regressed five. Similar totals conceal different decisions. Graph retrieval also improved over no memory overall, but produced fewer correct choices than text retrieval in this run.

**Where retrieval helped:** an old context-switching remedy contradicted current observations of an engine failure. Supplying it alone led one reader to fail all three trials. Text retrieval included a relevant engine-failure account, and that reader passed all three, matching its no-memory result. The additional account may have helped, but we did not isolate it from other packet differences.

**Where memory did not help:** a graph packet contained an explicit null-result passage, including p = 0.60. One reader nevertheless treated it as establishing a large effect in all three trials. The other reader interpreted the same packet correctly. Evidence can arrive without governing the answer.

The practical lesson is to measure both **what evidence reaches the decision** and **what the reader does with it**. Retrieval coverage alone misses evidence-use failures; a correct multiple-choice label alone can also hide a faulty explanation.

The run completed 32 records and left one partial ingestion attempt. Shared graph objects were touched during the failure. These are small-sample diagnostics, not a clean ranking of products or proof of long-horizon competence. Private source records and responses are withheld; the historical benchmark cannot be rerun from this package. Three local-adapter findings have separate, runnable offline synthetic reproductions.

Read the [full account](WRITEUP.md), [reported results](results/haystack-results.md), [paraphrased examples](EXAMPLES.md), and [adapter findings](COGNEE-NOTES.md).
