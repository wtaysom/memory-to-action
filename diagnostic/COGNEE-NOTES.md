# Three local-adapter findings in Cognee 1.5.4

We encountered these during a local memory-retrieval evaluation. This note contains no private source records or generated responses from that evaluation. The accompanying reproduction uses synthetic text, mocked HTTP/completions, and Cognee's installed adapter code. Network access is blocked. It reproduces routing and error handling, not the private corpus or its model outputs.

Tested Python 3.12; Cognee 1.5.4, LiteLLM 1.96.2, OpenAI SDK 2.54.0, Pydantic 2.13.5, Tenacity 9.1.4, HTTPX 0.28.1. Original local services were Ollama serving Gemma3 and Hugging Face TEI 1.8.3 serving embeddinggemma-300m (768 dimensions). A different dependency version may change these behaviors.

## Reproduce without services or private data

In a disposable Python 3.12 environment:

```sh
python3.12 -m venv .venv
.venv/bin/pip install -r code/requirements-repro.txt
.venv/bin/python code/reproduce_adapters.py
```

Dependency installation requires network access; the reproduction itself does not. It writes `code/adapter-reproduction-results.json`. Expected: the two model names select different structured-output paths; both synthetic embedding validation errors produce two identical requests and end as a Cognee `EmbeddingException` with status 422. The reproduction deliberately shortens the retry stop to two attempts and removes waiting. Production backoff remains unchanged in the installed package.

The script calls a private adapter helper to isolate routing. It is version-specific diagnostic code, not an application API example. The capability table comes from installed LiteLLM data. HTTPX simulates the TEI rejections with the exact error bodies observed in the local run; synthetic long text is not asserted to tokenize to exactly 2,402 tokens under a live tokenizer.

## 1. Model-name capability gating bypasses an endpoint's schema capability

**Observed.** `_supports_native_schema()` delegates to `litellm.supports_response_schema(model=...)`, with lookup failure treated as false. In this environment `ollama/gemma3:12b` returns false and `gpt-4o` true. The adapter sends JSON-object mode with the schema embedded in prompt instructions on the former path; it passes the Pydantic response schema on the latter. The endpoint is not consulted for that routing decision. JSON-object mode can enforce JSON syntax without enforcing the requested schema.

**Reproduction.** The script supplies the same tiny Pydantic model and mocked valid response under those two names. Captured `response_format` values are `{"type":"json_object"}` versus the `TinyRecord` schema class. This demonstrates routing, not relative model quality.

**Original-run workaround.** A local Ollama alias named `gpt-4o` pointed to the same Gemma3 12B digest, and requests used the local OpenAI-compatible endpoint. This enabled the schema-native path and a complete one-record Cognee ingestion/retrieval check. The actual model was Gemma, not GPT-4o. Alias routing is a workaround; it can also bring inappropriate model-specific defaults. Native schema mode did not eliminate every later generation or validation problem.

**Suggested change.** Offer an explicit endpoint/schema-capability override, or a capability probe with a documented fallback. Preserve the real served-model identity in receipts. Do not assume every local model or server can enforce every schema.

Code: `cognee/infrastructure/llm/structured_output_framework/litellm_native/native_adapter.py`, `_supports_native_schema()` and `_acreate_structured()`.

## 2. Default embedding batch exceeds server capacity; fixed rejection is retried unchanged

**Observed.** Cognee's OpenAI-compatible embedding engine defaults to batch size 36. Our TEI server's `/info` reported `max_client_batch_size: 32`. A 36-input request returned:

```text
HTTP 413: batch size 36 > maximum allowed batch size 32
```

The adapter wrapped this as `EmbeddingException` (status 422). Its retry policy resent the unchanged invalid request. A fresh run with `EMBEDDING_BATCH_SIZE=16` and `EMBEDDING_MAX_CONCURRENT_DATA_POINTS=16` passed the previously failing record. The default batch is not inherently invalid for all servers; the capacity mismatch and unchanged retries are the problem.

**Reproduction.** The script constructs the actual embedding engine with its default batch, submits 36 synthetic strings, and uses HTTPX to return the observed TEI error. It asserts two identical outgoing request bodies and the final wrapped 422. No server is required.

**Suggested change.** Allow/configure server capacity explicitly, check advertised limits where available, and classify a fixed batch validation error separately from a transient failure. Either fail promptly with the upstream detail or split into permitted batches under an explicit policy. TEI's `/info` is provider-specific, not a universal OpenAI API requirement.

Code: `cognee/infrastructure/databases/vector/embeddings/config.py`, `OpenAICompatibleEmbeddingEngine.py`, and `cognee/tasks/storage/index_data_points.py`.

## 3. Oversized embedding text is not recognized by the context-error handler

**Observed.** The same TEI server reported `max_input_length: 2048`. Later embedding input produced:

```text
HTTP 413: Input validation error: `inputs` must have less than 2048 tokens. Given: 2402
```

The adapter recognizes phrases such as `context length`, `too long`, and `maximum tokens`; this TEI wording matches none of those branches. It became a generic 422 and was retried unchanged until our encompassing 480-second record timeout. That timeout included earlier processing: it was not 480 seconds spent solely retrying this request. Increasing the timeout would not resolve the fixed input-size rejection.

The ingestion requested 512-token chunks, but Cognee warned that it was using an approximate fallback tokenizer. Graph processing also embeds generated text. The private trace does not isolate which field produced the oversized embedding text, so this report does not claim a specific chunker or generated field caused it.

**Reproduction.** The second embedding test returns the exact observed input-limit message for synthetic input. It verifies that the actual adapter wraps and retries it rather than taking the context-window handling branch. This reproduces error classification, not live token counting.

**Suggested change.** Validate every embedding input with a matching tokenizer where feasible, including generated fields. Recognize structured/provider-specific fixed validation errors. Make splitting, pooling, or truncation explicit and test its retrieval consequences; do not silently discard text. Preserve upstream status and useful error detail in the public error.

**Partial-state consequence.** Our run completed 32 records before this failure. A read-only snapshot audit found shared graph objects with timestamps during the failed attempt, even though that record had no document/chunk index entry. We retained the incomplete-ingestion disclosure. Transactional behavior or a documented recovery/rollback procedure deserves a separate test; the synthetic reproducer here does not establish that behavior.

Code: `cognee/infrastructure/databases/vector/embeddings/OpenAICompatibleEmbeddingEngine.py`, `embed_text()`; shared policy in `embeddings/retry_config.py`.

## Scope

These findings concern the tested local configuration. The reproduction supports the routing and retry observations. It does not reproduce the historical benchmark, prove a graph-versus-text advantage, or establish behavior in every Cognee/provider/version combination.
