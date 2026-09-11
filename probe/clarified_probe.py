"""Post-hoc fixture-clarity check requested by Fable; original receipts untouched."""
import argparse
import asyncio
import hashlib
import json
import os
import time
from datetime import datetime, timezone

import action_probe as base

OUT = base.ROOT / 'receipts/action_probe_clarified'


async def prepare():
    base.setup()
    from cognee.modules.search.types import SearchType
    OUT.mkdir(parents=True, exist_ok=False)
    cases = [c for c in base.fixtures() if c['id']=='unblocked-1']
    case = cases[0]
    old = 'Sam wants to use the hackathon visit to build a memory-system demo.'
    new = ('Sam wants to use the Atlas workshop, in the city, to build a memory-system demo. '
           'The September 16–30 travel is a separate trip, unrelated to attending any hackathon.')
    case['documents'] = [d.replace(old,new) for d in case['documents']]
    case['stale_documents'] = [d.replace(old,new) for d in case['stale_documents']]
    base.dump(OUT/'cases.json',cases)
    protocol = dict(created_at=datetime.now(timezone.utc).isoformat(), config_sha256=base.config_sha256(),
                    conditions=['stale','direct','cognee'],repetitions=[0,1,2],
                    system=base.SYSTEM, reader_model=os.environ['LLM_MODEL'], reader_endpoint=os.environ.get('LLM_ENDPOINT'),
                    temperature=0.3,max_tokens=4096,
                    cases_sha256=hashlib.sha256((OUT/'cases.json').read_bytes()).hexdigest(),
                    scope='Post-hoc clarification sensitivity check, one case with three repeats. '
                          'Original cases and receipts unchanged. Fresh ingestion is stochastic, '
                          'so comparison does not isolate wording from graph construction variation.',
                    change={'old':old,'new':new})
    base.dump(OUT/'protocol.json',protocol)
    dataset='clarified_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    start=time.monotonic()
    await base.cognee.remember(case['stale_documents'],dataset_name=dataset,self_improvement=False)
    await base.cognee.remember(case['added'],dataset_name=dataset,self_improvement=False)
    ingest_seconds=time.monotonic()-start
    start=time.monotonic()
    raw=await base.cognee.recall(query_text=case['task'],datasets=[dataset],
                                query_type=SearchType.GRAPH_COMPLETION,
                                auto_route=False,only_context=True,top_k=15)
    serialized=[r.model_dump(mode='json') for r in raw]
    row=dict(case=case['id'],dataset=dataset,ingest_seconds=ingest_seconds,
             retrieval_seconds=time.monotonic()-start,raw=serialized,
             contexts=dict(stale='\n\n'.join(case['stale_documents']),
                           direct='\n\n'.join(case['documents']),
                           cognee='\n\n'.join(r['text'] or '' for r in serialized)))
    (OUT/'contexts.jsonl').write_text(json.dumps(row,ensure_ascii=False)+'\n')
    protocol['contexts_sha256']=hashlib.sha256((OUT/'contexts.jsonl').read_bytes()).hexdigest()
    base.dump(OUT/'protocol.json',protocol)
    print('Clarified case frozen.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','run'])
    args=parser.parse_args()
    asyncio.run(prepare() if args.mode=='prepare' else base.run(OUT))
