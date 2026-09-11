"""Haystack pipeline: ingest a JSONL corpus into a fresh Cognee dataset, freeze retrieval packets per
case for flat (RAG_COMPLETION) and graph (GRAPH_COMPLETION) retrieval, then hand them to trial.py.

  python haystack.py ingest   --corpus corpus.jsonl --out run/ --env env.local --actual-model gemma3:12b [--cutoff ISO-UTC]
  python haystack.py retrieve --cases cases.json --out run/
  python trial.py --cases cases.json --contexts run/contexts.jsonl --conditions rag,graph --out run/

Corpus rows: {"id": str, "type": str, "speaker": str, "created_at": str, "force": str, "content": str}.
Each record becomes one Cognee document whose text starts with its id, so packets can be audited for
which records arrived. Ingestion appends a receipt per record and stops between records at the
cutoff; a failed record stops the pipeline rather than silently skipping (partial graph state would
otherwise be unaccounted for). Retrieval uses only_context=True: the search's rendered context is
captured, never Cognee's own answer, so one reader sees every condition. Self-improvement and
feedback reweighting are off. Search may still update operational metadata.
"""
import argparse, asyncio, hashlib, json, random, time
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid5, NAMESPACE_URL


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p, v):
    Path(p).write_text(json.dumps(v, indent=2, ensure_ascii=False, default=str))


def append(p, v):
    with Path(p).open('a') as f:
        f.write(json.dumps(v, ensure_ascii=False, default=str) + '\n')


async def ingest(a):
    if a.out.exists() and any(a.out.iterdir()):
        raise SystemExit('Existing output may contain partial state; use a fresh --out.')
    rows = [json.loads(l) for l in a.corpus.read_text().splitlines() if l.strip()]
    if not rows or len({r['id'] for r in rows}) != len(rows):
        raise SystemExit('Corpus must be nonempty with unique record IDs.')
    from local_guard import configure
    identity = configure(a.env, a.out / 'storage', a.actual_model)
    import cognee
    from cognee.tasks.ingestion.data_item import DataItem
    a.out.mkdir(parents=True, exist_ok=True)
    pp = a.out / 'protocol.json'
    protocol = dict(created_at=datetime.now(timezone.utc).isoformat(), identity=identity,
                    dataset='haystack_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'),
                    corpus_sha256=sha(a.corpus), env_sha256=sha(a.env), planned_count=len(rows), cutoff=a.cutoff,
                    chunk_size=a.chunk_size, top_k=a.top_k,
                    search_types={'rag': 'RAG_COMPLETION', 'graph': 'GRAPH_COMPLETION'}, status='ingesting')
    save(pp, protocol)
    receipts = a.out / 'ingestion.jsonl'
    done = set()
    for i, row in enumerate(rows):
        if row['id'] in done:
            continue
        if a.cutoff and datetime.now(timezone.utc) >= datetime.fromisoformat(a.cutoff):
            break
        text = (f"Record {row['id']}. Type {row.get('type')}. Speaker {row.get('speaker')}. "
                f"Created {row.get('created_at')}. Force {row.get('force')}.\n" + row['content'])
        try:
            rid = UUID(str(row['id']))
        except ValueError:
            rid = uuid5(NAMESPACE_URL, str(row['id']))
        item = DataItem(data=text, label=str(row['id']), data_id=rid, external_metadata={'source_id': row['id']})
        t0 = time.monotonic(); print(f'INGEST {i+1}/{len(rows)} {row["id"]}', flush=True)
        try:
            result = await asyncio.wait_for(cognee.remember(item, dataset_name=protocol['dataset'], self_improvement=False,
                                                            chunk_size=a.chunk_size, raise_on_error=True), timeout=a.record_timeout)
            append(receipts, dict(record_id=row['id'], success=True, seconds=time.monotonic() - t0, result=str(result)))
            append(a.out / 'ingested-corpus.jsonl', row); done.add(row['id'])
        except Exception as exc:
            append(receipts, dict(record_id=row['id'], success=False, seconds=time.monotonic() - t0, error=f'{type(exc).__name__}: {exc}'))
            protocol['status'] = 'failed_partial_state'; save(pp, protocol); raise
    if not done:
        raise SystemExit('No completed records.')
    protocol.update(actual_count=len(done), completed_ids=[r['id'] for r in rows if r['id'] in done],
                    actual_corpus_sha256=sha(a.out / 'ingested-corpus.jsonl'),
                    freeze_reason='all_planned_completed' if len(done) == len(rows) else 'cutoff_between_records',
                    frozen_at=datetime.now(timezone.utc).isoformat(), status='ingested')
    save(pp, protocol); print('INGESTED', len(done), 'of', len(rows))


async def retrieve(a):
    from local_guard import configure
    protocol = json.loads((a.out / 'protocol.json').read_text())
    if protocol['status'] not in ('ingested', 'retrieved'):
        raise SystemExit('Ingestion incomplete or failed; automatic recovery is unsupported. Use a new run.')
    if protocol.get('env_sha256') != sha(a.env):
        raise SystemExit('Configuration changed or was not frozen; use a new run.')
    cases_hash = sha(a.cases)
    if protocol.get('cases_sha256') not in (None, cases_hash):
        raise SystemExit('Cases changed after retrieval started; use a new run.')
    target = a.out / 'contexts.jsonl'
    if protocol.get('status') == 'retrieved':
        if not target.exists() or sha(target) != protocol.get('contexts_sha256'):
            raise SystemExit('Frozen contexts changed.')
        print('Already retrieved; frozen cases and contexts verified.')
        return
    if target.exists() and not protocol.get('cases_sha256'):
        raise SystemExit('Existing contexts have no frozen cases.')
    protocol['cases_sha256'] = cases_hash
    save(a.out / 'protocol.json', protocol)  # freeze before the first query
    identity = configure(a.env, a.out / 'storage', protocol['identity'].get('actual_llm'))
    if identity.get('llm_alias_digest') != protocol['identity'].get('llm_alias_digest'):
        raise SystemExit('Extractor identity changed since ingestion.')
    import cognee
    from cognee.modules.search.types import SearchType
    cases = json.loads(a.cases.read_text())
    existing = list(map(json.loads, target.read_text().splitlines())) if target.exists() else []
    done = {(r['case'], r['condition']) for r in existing}
    expected = {(c['id'], k) for c in cases for k in protocol['search_types']}
    if len({c['id'] for c in cases}) != len(cases) or len(done) != len(existing) or not done <= expected:
        raise SystemExit('Duplicate cases/contexts or out-of-grid contexts.')
    jobs = [(c, k) for c in cases for k in protocol['search_types']]
    random.Random(20260911).shuffle(jobs)
    for case, cond in jobs:
        if (case['id'], cond) in done:
            continue
        t0 = time.monotonic()
        raw = await cognee.search(query_text=case['task'], datasets=[protocol['dataset']],
                                  query_type=SearchType(protocol['search_types'][cond]), only_context=True,
                                  verbose=True, top_k=protocol['top_k'], include_references=True, feedback_influence=0.0)
        context = '\n\n'.join((r.get('context_result') or '') for r in raw)
        if not context.strip():
            raise SystemExit(f'Empty retrieval context for {case["id"]} {cond}')
        append(target, dict(case=case['id'], condition=cond, context=context, retrieval_seconds=time.monotonic() - t0, raw=raw))
        print('RETRIEVED', case['id'], cond, len(context), flush=True)
    protocol.update(contexts_sha256=sha(target), status='retrieved'); save(a.out / 'protocol.json', protocol)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mode', choices=['ingest', 'retrieve'])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--env', type=Path, default=Path('env.local'))
    ap.add_argument('--corpus', type=Path)
    ap.add_argument('--cases', type=Path)
    ap.add_argument('--actual-model', help='Ollama model the alias must resolve to (digest check)')
    ap.add_argument('--cutoff', help='UTC ISO datetime; stop starting new records after it')
    ap.add_argument('--chunk-size', type=int, default=512)
    ap.add_argument('--top-k', type=int, default=5)
    ap.add_argument('--record-timeout', type=int, default=900)
    a = ap.parse_args()
    if (a.mode == 'ingest' and not a.corpus) or (a.mode == 'retrieve' and not a.cases):
        ap.error('ingest requires --corpus; retrieve requires --cases')
    if a.cutoff and datetime.fromisoformat(a.cutoff).tzinfo is None:
        ap.error('--cutoff must include a timezone, e.g. +00:00')
    asyncio.run(ingest(a) if a.mode == 'ingest' else retrieve(a))


if __name__ == '__main__':
    main()
