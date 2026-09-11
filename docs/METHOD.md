# Method: measuring whether memory changes the action

The claim under test is not "the store has the fact" but "the fact governs the next action."
Between the two sit five links, and each can fail alone:

1. **Storage.** The correction was written down.
2. **Selection.** The retriever surfaces it, or something as good, among plausible neighbors.
3. **Delivery.** What was selected arrives intact in the reader's context.
4. **Uptake.** The reader reads it as what it is (a correction, a failure report, a null result).
5. **Action.** The chosen action changes accordingly.

## Design rules that made the day's numbers trustworthy

- **Score the action, not the prose.** Each case is a bounded choice with one expected index.
  Reasons are kept for inspection. Twice today a reader picked the right index for a wrong reason;
  action totals therefore overstate understanding, and the receipts say so.
- **Freeze before inference.** Cases, contexts and settings are hashed; the runner refuses to
  append trials from changed inputs. Resume never repeats a completed trial.
- **Pair everything.** With three seeds, the honest unit is the (case, model, seed) pair across
  conditions: improved, regressed, unchanged. Totals hide opposite movements.
- **Isolate one link per condition.** `none` (task and choices), `text_target` (the right record,
  complete, hand-picked: selection held perfect), retrieval conditions (selection under test with
  delivery and reader fixed). Compare `text_target` with a truncated rendering to test delivery alone.
- **Use small readers on purpose.** A 27B model solved nine of ten cases from the choices; a 4B
  model leaves headroom, so differences in what it is handed show up as differences in what it does.
  The cost is a reader-limited case (stop-loop) that no condition solves; mark it as such.
- **Audit coverage two ways.** Designated target present, and target-or-valid-alternative present,
  because a haystack can hold a better record than the one you designated. Then read the packets
  for the cases that matter: an id mention is not the passage.
- **Keep retrieval and answering apart.** `only_context=True`; the same reader sees every condition.
- **Nothing learns from the run.** Self-improvement and feedback reweighting off, fresh dataset.
- **Fully local when the corpus is private.** A socket audit hook that blocks every non-local host,
  and an identity receipt proving which weights sat behind the model alias.
- **Report what stopped.** A cutoff or a failure freezes a partial corpus that is reported as such,
  never padded.

## What today's run could and could not say

Could: retrieval over 32 records matched the hand-picked record (49 vs 50 of 60); graph completion
lost mostly on rendering and reading; one changed-circumstances case showed retrieval undoing the
damage the hand-picked old lesson had done. Could not: isolate the neighbor's causal role (no
ablation), rank products (one corpus size, three seeds, two readers), or claim anything about
long-horizon autonomy. The ablation that would settle the first is one run: remove the neighbor
record from the haystack and rerun the case.
