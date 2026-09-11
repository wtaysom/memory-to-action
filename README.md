# memory-to-action

**When a stored fact changes, does the agent's next action change?**

An evaluation harness built at the Data & AI Hackathon in San Francisco, 11 September 2026. We tested Cognee 1.5.4 retrieval with local models and found both missing-evidence and evidence-use failures. The correction can survive retrieval and still fail to govern the next action.

## What the historical run found

Ten simulated maintenance situations, two local 4B readers and three seeds produced 60 trials per condition. Higher scores mean more choices matching the predefined expected action. These are ten situations repeated across models and seeds, not 60 independent real-world tasks.

| Context supplied | Correct choices /60 | Relevant historical passage delivered |
|---|---:|---:|
| No memory | 40 | — |
| Designated full record, supplied directly | 50 | Supplied directly |
| Cognee text retrieval | 49 | 9/10 situations |
| Cognee graph retrieval | 44 | 8/10 situations |

Text retrieval improved ten trials and regressed one against no memory. Against the designated-record control, it improved four and regressed five. Graph retrieval improved over no memory overall but scored below text retrieval in this run.

**Where retrieval helped:** an old context-switching remedy conflicted with current observations of an engine failure. Supplying it alone led Qwen to fail all three trials. Text retrieval also supplied an engine-failure account, and Qwen passed all three, matching its no-memory result. The additional account may have helped, but packet contents, order and framing also differed; its causal contribution was not isolated.

**Where delivered evidence was misused:** a graph packet contained an explicit null result, including p = 0.60. Gemma nevertheless treated it as establishing a large effect in all three trials. Qwen interpreted the same packet correctly. Passage delivery and its use are separate measurements.

The run completed **32 of 108 planned records and left one partial ingestion attempt**. Shared graph objects were touched during that failure; their effect is unknown. These are diagnostics under incomplete ingestion, not a clean product ranking. The full-record and graph conditions each include one malformed-JSON failure, both Qwen, counted incorrect. Correct labels sometimes had faulty explanations.

[Detailed results](results/haystack-results.md), [method](docs/METHOD.md), [paraphrased examples](background/EXAMPLES.md), [full account](background/WRITEUP.md).

## What is runnable here

- `harness/`: a portable adaptation of the historical trial and retrieval code. Supply your own cases and corpus. It includes bounded simulated reads, frozen inputs, resumable reader receipts and paired-result auditing.
- `cases/`: the schema and two synthetic cases. These do not recreate the historical ten-case benchmark.
- `probe/`: six fictional situations with incremental updates and three context conditions. This is a separate exploratory probe, not the source of the 40/50/49/44 table.
- `diagnostic/`: three offline synthetic checks against the tested Cognee adapters, with mocked responses and network access blocked.
- `results/` and `background/`: reported historical measurements and their explanation. The private corpus, exact cases, retrieval packets and raw trial responses are withheld; **the historical benchmark cannot be independently rerun from this repository**.

## Run a two-case reader smoke test

From the repository root, with Ollama serving `gemma3:4b`:

```sh
python3 harness/trial.py --cases cases/example-cases.json --out smoke/ \
  --conditions none,text_target --models gemma3:4b --seeds 11
python3 harness/audit.py --trials smoke/trials.jsonl
```

This uses only Python's standard library and makes four model calls. The choices themselves provide clues, so a no-memory pass is possible. A four-call smoke test checks operation and illustrates possible behavior; it does not establish a robust effect. Use a fresh output directory if you change cases, settings or runner code.

## Run retrieval on your own corpus

Use Python 3.12. Install dependencies, start Ollama and an OpenAI-compatible embedding service, then configure their local addresses and actual models:

```sh
python3.12 -m venv .venv
.venv/bin/pip install -r diagnostic/requirements-repro.txt python-dotenv
cp probe/env.local-example harness/env.local
# Inspect/edit harness/env.local for your services; create the documented local alias.
.venv/bin/python harness/haystack.py ingest --corpus my-records.jsonl --out run/ \
  --env harness/env.local --actual-model gemma3:12b
.venv/bin/python harness/haystack.py retrieve --cases my-cases.json --out run/ --env harness/env.local
.venv/bin/python harness/trial.py --cases my-cases.json --out run/control/ --conditions none,text_target
.venv/bin/python harness/trial.py --cases my-cases.json --out run/retrieval/ \
  --contexts run/contexts.jsonl --conditions rag,graph
.venv/bin/python harness/audit.py --trials run/retrieval/trials.jsonl --baseline run/control/trials.jsonl \
  --contexts run/contexts.jsonl --evidence my-evidence-sets.json
```

The default readers are `qwen3.5:4b` and `gemma3:4b`; install them or pass `--models` explicitly. See the [case schema](cases/README.md). Ingestion requires a fresh output directory. A failed or interrupted ingestion may have partial storage and is refused on restart; a new run is required. Retrieval can resume with the same frozen cases and configuration. The public harness does not implement recovery or rollback of failed ingestion.

`local_guard.py` restricts Python socket calls to configured loopback/private-network endpoints. Private-network services may be other machines; this is not an OS sandbox. The reader uses the explicit `--ollama-url` (default localhost) and is not covered by that guard. Preserve your run's identity receipt and model versions.

## Run the separate synthetic probe

Using the environment above, from the repository root:

```sh
cp probe/env.example probe/.env  # configure Gemini keys explicitly
# For local services instead: cp probe/env.local-example probe/.env
.venv/bin/python probe/action_probe.py prepare --output receipts/demo
.venv/bin/python probe/action_probe.py run --output receipts/demo
.venv/bin/python probe/clarified_probe.py prepare
.venv/bin/python probe/clarified_probe.py run
```

The main probe makes 54 reader calls plus model-assisted ingestion; the clarified probe makes nine reader calls plus fresh ingestion. The latter examines an ambiguity in one original fixture, but graph construction and sampling also change, so it does not isolate wording as the cause. Local OpenAI-compatible and Gemini configuration paths are provided; support for arbitrary providers is not established. The probe stores synthetic receipts beneath `probe/receipts/` and refuses to overwrite an existing preparation directory.

**Alias workaround:** in the tested versions, LiteLLM's model-name lookup selected different structured-output paths for `ollama/gemma3:12b` and `gpt-4o`. An Ollama alias (`ollama cp gemma3:12b gpt-4o`) enabled the native-schema path for the same local weights. This is a routing workaround, not a guarantee of correct generation or a claim about every Ollama model. [Adapter findings](diagnostic/COGNEE-NOTES.md).

## Offline diagnostic and regression checks

```sh
.venv/bin/python diagnostic/reproduce_adapters.py
.venv/bin/python -m unittest discover -s tests -v
```

The diagnostic requires the pinned dependencies above but no live services or keys. It reproduces model-name routing and two fixed embedding rejections retried unchanged. It does not reproduce the historical model outcomes. Regression tests use mocked services and synthetic fixtures.

Sponsor technology in the measured memory experiment: Cognee only. No five-technology integration or `.pipe` submission is claimed here. Other hackathon configuration work is separate from these reported measurements.

William Taysom, with Sili Astra (Codex) and Sili Fable (Claude Code).
