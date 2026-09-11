# memory-to-action

**When a stored fact changes, does the agent's next action change?** A small, runnable evaluation
harness for memory systems, built in one day at the Data & AI Hackathon (AWS Builder Loft,
San Francisco, 11 September 2026). Retrieval under test: Cognee 1.5.4, run fully local.

The event theme, "From Memory to Muscle Memory," says most agents are smart once and forgetful
forever. This project tests the claim at its weakest link. Storing a correction is easy. Getting it
to govern the next decision passes through four more links (selection, delivery, uptake, action),
and each can fail on its own.

## What is in the box

| Directory | What it is | Runs where |
|---|---|---|
| `harness/` | The method, corpus-agnostic: `trial.py` (bounded decision trials with a tool budget, frozen inputs, resumable receipts), `haystack.py` (ingest a JSONL corpus into Cognee, freeze flat and graph retrieval packets per case), `local_guard.py` (fail-closed local-only runtime with an identity receipt), `audit.py` (coverage two ways, paired counts, budget pressure) | any machine with Ollama and a Cognee-compatible embedder; bring your own corpus |
| `cases/` | The case schema, two synthetic example cases, an example evidence-set file | read, then write your own |
| `probe/` | A self-contained synthetic probe: six fictional situations in which a fact changes, three context conditions (stale records, current source text, Cognee graph retrieval), repeated reads, scored on the action chosen | any OpenAI-compatible endpoint, Gemini, or local Ollama |
| `diagnostic/` | Offline reproductions of three Cognee 1.5.4 defects found on the way, mocked servers, network blocked | anywhere, no keys |
| `results/` | Aggregate results from the private run on a real memory store (5,725 records, 32-record haystack, two local 4B readers) | read only |
| `docs/METHOD.md` | The five links between storage and action, and the design rules that keep the numbers honest | read |
| `background/` | The story, the joint summary, paraphrased examples | read |

## Run the harness on your own corpus

```bash
pip install cognee==1.5.4 python-dotenv
cp probe/env.local-example harness/env.local        # alias a local model; see the note below
cd harness
python haystack.py ingest   --corpus my-records.jsonl --out run/ --env env.local --actual-model gemma3:12b
python haystack.py retrieve --cases my-cases.json --out run/
python trial.py --cases my-cases.json --out run/            --conditions none,text_target
python trial.py --cases my-cases.json --out run/retrieval/ --contexts run/contexts.jsonl --conditions rag,graph
python audit.py --trials run/retrieval/trials.jsonl --baseline run/trials.jsonl \
                --contexts run/contexts.jsonl --evidence my-evidence-sets.json
```

`cases/README.md` gives the schema; `cases/example-cases.json` runs as-is against Ollama for a
smoke test (`python trial.py --cases ../cases/example-cases.json --out smoke/ --conditions none,text_target`).
Smoke receipt, 2026-09-11 15:15 PDT, Gemma3 4B, seed 11: `date-moved` correct with and without
the record; `old-remedy` correct with no memory and **wrong once handed the old lesson**, which is
the changed-circumstances effect from the real run reproduced on two synthetic cases in four calls.

## Run the probe

```bash
cd probe && python -m venv .venv && .venv/bin/pip install cognee==1.5.4 litellm python-dotenv
cp env.example .env            # Gemini, or edit for any OpenAI-compatible endpoint
# fully local instead: cp env.local-example .env   (see the alias note below)
.venv/bin/python action_probe.py    # 54 reader calls; receipts land in receipts/
.venv/bin/python clarified_probe.py # the disambiguated fixture, 9 calls
```

Each run writes a frozen protocol, the retrieved contexts, and every reader response, so the
score can be audited rather than trusted.

**The local alias note.** Cognee enforces its output schema only when litellm believes the model
supports it, which no Ollama-named model does; local extraction then falls to a prompt-only JSON
fallback that small models fail. Aliasing the local model under an OpenAI model name
(`ollama cp gemma3:12b gpt-4o`) and pointing Cognee at Ollama's `/v1` endpoint routes the same
weights through a name litellm accepts, and Ollama enforces the schema by grammar. Nothing leaves
the machine. Details and the two embedding-limit defects: `diagnostic/COGNEE-NOTES.md`.

## What the private run found

Same harness, real store, ten decision cases drawn from real corrections, two small local readers,
three seeds, 60 trials per row. Only what the reader is handed changes.

| The reader is handed | Correct / 60 | Passage present in packet |
|---|---:|---:|
| nothing | 40 | n/a |
| the right record, hand-picked, complete | 50 | by construction |
| Cognee flat retrieval over the haystack (top 5 chunks) | 49 | 9 of 10 cases |
| Cognee graph completion, same haystack | 44 | 8 of 10 cases |

Two receipts matter more than the totals. Where the hand-picked record was the *wrong* lesson for
changed circumstances, one reader given only that record chose the old remedy 0 of 3; retrieval,
whose packet also carried a neighbor record describing the present failure, brought it back to
3 of 3, the same as with no memory at all. The neighbor's role is plausible, not isolated. And
where the right passage did arrive in a graph packet, one reader still misread it 3 of 3.
**The correction can survive retrieval and still fail to govern the next action.**

Full tables, paired counts and limits: `results/`. Private record text is excluded; the synthetic
probe in `probe/` is the runnable stand-in.

## Against the event's five layers

| Layer | Here |
|---|---|
| Structure | records carry speaker, force and supersession; Cognee extracts a graph from them |
| Memory | Cognee ingestion and retrieval, local |
| Insight | frozen retrieval packets audited for passage delivery, not just id mention |
| Motion | a bounded action choice per case, scored on the action taken, not the prose |
| Muscle memory | the harness itself: paired trials that changed what shipped (a richer memory presentation stayed opt-in because the numbers said so) |

Sponsor technology used: Cognee only. Not used: HydraDB, hotdata, RocketRide, Modiqo. No
`.pipe` files. This is an evaluation harness with receipts, not a five-technology application.

## Who

William Taysom, with two AI coding agents (one on Codex, one on Claude Code) sharing one repository
and one memory store. Contact: wtaysom@gmail.com.
