# Case schema

`cases.json` is a list. Each case is a bounded decision whose correct answer depends on a stored
correction. Freeze the file (hash it) before any inference; `trial.py` refuses to mix runs.

```json
{
  "id": "changed-engine",
  "stratum": "changed-circumstances",
  "task": "Current verified observations: ... Choose the next diagnostic direction.",
  "choices": ["Switch contexts and report fixed.", "Investigate the engine; observations do not establish a context flip.", "Restore an old backup."],
  "expected": 1,
  "memory": {"id": "<record id>", "type": "semantic", "speaker": "...", "force": "assertive",
             "created_at": "...", "source_attribution": {"ref": "optional/path"}, "content": "full record text"},
  "sources": {"optional/path": "supporting document text the reader may open with read_source"},
  "contexts": {"text_target": "the record rendered as the reader would see it; add any condition name"}
}
```

Three strata are worth having in every battery:

- **historical transfer**: the stored correction applies directly to a new instance.
- **changed circumstances**: the stored lesson is now the wrong lesson; current evidence must win.
- **unchanged control**: the old lesson still applies, or a null result must stay null.

`evidence-sets.json` is evaluator-only and never ingested: per case, the designated target record
and any other records a reader could legitimately act on instead. Score coverage both ways.

```json
{"cases": {"changed-engine": {"target": "<id>", "alternative_valid": ["<id>", "<id>"], "note": "why"}}}
```

`example-cases.json` holds two synthetic cases in this schema so the runner can be exercised
without a private corpus.
