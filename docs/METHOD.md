# Method: measuring whether memory changes the action

We distinguish five stages: storing a correction, selecting relevant history, delivering it intact, interpreting its force, and choosing an action. This is a diagnostic framework; today's experiment did not isolate every stage causally.

## Design and scoring

- **Score the selected action and inspect the explanation.** Each case has a predefined expected index. All errors stay in the denominator. A correct label can have a faulty reason, so the score does not establish understanding or successful real-world operations.
- **Freeze inputs and settings.** Reader runs compare case/context hashes, settings, system prompt and runner identity before resuming. Retrieval records the case hash before querying, checks configuration, and verifies finished context hashes. Keep model versions/digests separately: a fixed model name alone does not freeze weights. Avoid concurrent writers to one output directory.
- **Pair case, model and seed.** Report improvements, regressions and unchanged decisions together with their denominator. Three seeds are repetitions, not independent situations.
- **Separate record supply from retrieval.** `text_target` supplies the designated record directly. Selection is fixed, not perfect: the designated old lesson can be inappropriate now. Retrieval changes several aspects of the context at once, including content and ordering. It does not isolate graph structure or summaries.
- **Report reader dependence.** The 27B reader scored 27/30 without memory; the two 4B readers left more room for differences. Stop-loop failed in the four main 4B comparison conditions, but an earlier delivery condition produced two correct labels. Avoid universal claims about what no reader or condition can solve.
- **Audit coverage at multiple levels.** The supplied audit reports ID-prefix presence and target-or-alternative presence. Those are routing checks, not proof of passage delivery or truth. Manually inspect the relevant passages as a separate measurement, preferably before inspecting reader outcomes.
- **Keep retrieval and answering separate.** Cognee uses `only_context=True`, with self-improvement disabled and feedback influence zero. This does not guarantee that search leaves every byte of storage unchanged.
- **Describe network scope accurately.** The Python socket guard allows only configured loopback/private-network addresses; it is not a full process sandbox. An explicit actual-model declaration must match a present Ollama alias digest. Reader endpoint configuration is separate.
- **Disclose incomplete ingestion.** Failed/interrupted ingestion can leave partial state. The public runner refuses to resume it automatically; it does not reproduce the historical manual snapshot/audit/recovery procedure.

The simulated `read_memory` tool can open the case's designated record if the reader supplies its full ID or a prefix of at least eight characters; `read_source` can open supplied supporting text by path. These tools are available across conditions, including no initially supplied memory. Thus `none` means no memory in the initial prompt, not an enforced prohibition on subsequent evidence access. Tool results are recorded.

## Findings and limits

Text retrieval scored 49/60 versus 50/60 for the designated record, with four paired improvements and five regressions. That is not established equivalence. Graph retrieval scored 44/60; its regressions include missing-evidence and evidence-use failures. Neither summary wording nor ordering was isolated as the cause.

The historical run completed 32 records, then one failed partial attempt touched shared graph objects. Ten cases, two readers and three seeds do not support a general product ranking or a claim about long-horizon autonomy. Historical raw fixtures and responses are withheld; public code is a portable adaptation and includes separate synthetic examples.

To test the competing-record explanation, first hold a retrieved packet fixed and remove or replace only that record's passage. Repeat across seeds/readers and inspect reasons as well as choices. Removing a record from the corpus and rebuilding the graph changes extraction and retrieval too; that is a different, broader intervention.
