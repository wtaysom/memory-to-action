# Three decision examples

These are public paraphrases of measured cases. Names, private record text and internal identifiers are omitted. They explain the results; they are not the exact frozen prompts and must not be used to claim reproduction of the reported scores.

## 1. Which past failure resembles this one?

**Present:** Docker's context is already correct, but the engine socket is unresponsive.

**History A:** An earlier problem was fixed by switching Docker contexts.

**History B:** Another incident had the correct context and an unresponsive engine. It eventually recovered after investigation.

**Decision:** Reapply the context switch, investigate the engine/socket problem, or assume the earlier recovery means this incident is already resolved?

The expected direction is to investigate the current engine/socket problem. For Qwen, no memory scored 3/3; History A supplied directly scored 0/3; text retrieval containing both accounts scored 3/3; graph retrieval also containing both accounts scored 0/3. The packets differed beyond these accounts. This suggests testing how present observations select among competing histories; it does not prove that one added record caused recovery.

## 2. Did the negative result constrain the conclusion?

**Evidence:** A recorded experiment reports no supported effect and a permutation-test p-value of 0.60.

**Decision:** Preserve that negative finding, or treat the p-value as establishing a large effect?

Gemma answered correctly in 3/3 full-record trials. The graph packet contained the relevant passage, but Gemma answered incorrectly in 3/3. Qwen answered correctly from that graph packet in 3/3. Passage delivery succeeded while one reader's inference failed. This motivates testing the same passage with and without its generated summary and neighboring text.

## 3. Is a record of failure an instruction?

**History:** A mechanism intended to preserve information also triggered another turn, producing an unwanted loop. The record includes a correction: write the information separately and let a later user prompt retrieve it; do not manufacture another turn.

**Decision:** Repeat the mechanism that caused the loop, or use the corrected separation?

Neither retriever delivered the relevant correction, and each condition scored 0/6. The complete-record control delivered it but also scored 0/6. These are different failures: selection can miss a lesson, while a reader can receive it and still adopt the failed mechanism. An earlier delivery condition produced some correct labels, so failure here is not a universal limitation.

See [reported per-case results](results/haystack-results.md) and the [method and limitations](WRITEUP.md).
