"""Offline regression checks for receipt integrity and model identity."""
import asyncio
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'harness'))
import trial
import haystack
import local_guard
import audit

CASE = {'id': 'synthetic', 'task': 'Choose.', 'choices': ['a', 'b'], 'expected': 1,
        'memory': {'id': '12345678', 'content': 'Synthetic'}, 'contexts': {'text_target': 'Synthetic'}}

class ReceiptTests(unittest.TestCase):
    def response(self, choice):
        return io.BytesIO(json.dumps({'message': {'content': json.dumps({'tool': 'finish', 'choice': choice})}}).encode())

    def test_boolean_choice_is_not_integer_action(self):
        with patch('urllib.request.urlopen', return_value=self.response(True)):
            self.assertFalse(trial.trial(CASE, 'none', 'test', 11, '', 'http://localhost')['passed'])

    def test_integer_choice_is_scored(self):
        with patch('urllib.request.urlopen', return_value=self.response(1)):
            self.assertTrue(trial.trial(CASE, 'none', 'test', 11, '', 'http://localhost')['passed'])

    def test_resume_rejects_settings_changes_and_skips_completed(self):
        with tempfile.TemporaryDirectory() as d:
            cases = Path(d)/'cases.json';cases.write_text(json.dumps([CASE]));out = Path(d)/'run'
            args = ['trial.py', '--cases', str(cases), '--out', str(out), '--models', 'test', '--seeds', '11']
            with patch.object(sys, 'argv', args), patch.object(trial, 'trial', return_value={'case': 'synthetic','condition': 'none','model': 'test','seed': 11,'passed': True}) as run, redirect_stdout(io.StringIO()):
                trial.main();trial.main();self.assertEqual(run.call_count, 1)
            with patch.object(sys, 'argv', args + ['--models', 'other']), self.assertRaises(SystemExit), patch.object(trial,'trial') as run:
                trial.main()
            run.assert_not_called()
            with patch.object(sys, 'argv', args), patch.object(trial,'SYSTEM','changed'), self.assertRaises(SystemExit):
                trial.main()

    def test_duplicate_cases_rejected_before_inference(self):
        with tempfile.TemporaryDirectory() as d:
            cases=Path(d)/'cases.json';cases.write_text(json.dumps([CASE,CASE]))
            with patch.object(sys,'argv',['trial.py','--cases',str(cases),'--out',d]), self.assertRaises(SystemExit), patch.object(trial,'trial') as run:
                trial.main()
            run.assert_not_called()

    def test_duplicate_audit_cells_are_not_double_counted(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'trials.jsonl';f.write_text((json.dumps({'case':'x','condition':'none','model':'test','seed':11})+'\n')*2)
            with patch.object(sys,'argv',['audit.py','--trials',str(f)]),self.assertRaises(SystemExit):audit.main()

class RetrievalTests(unittest.TestCase):
    def test_interrupted_ingestion_refused_before_service_calls(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);(out/'protocol.json').write_text('{"status":"ingesting"}')
            with patch.object(local_guard,'configure') as conf,self.assertRaises(SystemExit):
                asyncio.run(haystack.ingest(SimpleNamespace(out=out)))
            conf.assert_not_called()

    def test_changed_cases_refused_before_service_calls(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);env=out/'env';env.write_text('synthetic');cases=out/'cases.json';cases.write_text('[]')
            (out/'protocol.json').write_text(json.dumps({'status':'ingested','env_sha256':haystack.sha(env),'cases_sha256':'old'}))
            with patch.object(local_guard,'configure') as conf,self.assertRaises(SystemExit):
                asyncio.run(haystack.retrieve(SimpleNamespace(out=out,env=env,cases=cases)))
            conf.assert_not_called()

    def test_changed_finished_context_refused(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);env=out/'env';env.write_text('synthetic');cases=out/'cases.json';cases.write_text('[]')
            (out/'contexts.jsonl').write_text('changed')
            (out/'protocol.json').write_text(json.dumps({'status':'retrieved','env_sha256':haystack.sha(env),'cases_sha256':haystack.sha(cases),'contexts_sha256':'old'}))
            with patch.object(local_guard,'configure') as conf,self.assertRaises(SystemExit):
                asyncio.run(haystack.retrieve(SimpleNamespace(out=out,env=env,cases=cases)))
            conf.assert_not_called()

class IdentityTests(unittest.TestCase):
    def check_identity(self, models, failure=None):
        with tempfile.TemporaryDirectory() as d:
            env=Path(d)/'env';env.write_text('LLM_MODEL=alias\nLLM_ENDPOINT=http://localhost:11434/v1\nEMBEDDING_ENDPOINT=http://localhost:8080/v1\nEMBEDDING_BATCH_SIZE=16\n')
            opener=SimpleNamespace(open=lambda *a,**k: io.BytesIO(json.dumps({'models':models,'max_client_batch_size':32}).encode()))
            if failure:
                def fail(*a,**k):raise failure
                opener.open=fail
            with patch.dict(os.environ,{},clear=True),patch.object(local_guard.socket,'getaddrinfo',return_value=[(0,0,0,'',('127.0.0.1',0))]),patch.object(local_guard.sys,'addaudithook'),patch.object(local_guard,'build_opener',return_value=opener):
                return local_guard.configure(env,Path(d)/'storage','actual')

    def test_absent_alias_and_actual_do_not_verify(self):
        with self.assertRaisesRegex(RuntimeError,'missing'):self.check_identity([])

    def test_matching_present_models_verify(self):
        r=self.check_identity([{'name':'alias:latest','digest':'abc'},{'name':'actual:latest','digest':'abc'}])
        self.assertEqual(r['llm_alias_digest'],'abc')

    def test_unavailable_identity_fails_when_declared(self):
        with self.assertRaisesRegex(RuntimeError,'Cannot verify'):self.check_identity([],OSError('offline'))

class PipelineTests(unittest.TestCase):
    def test_synthetic_ingest_retrieve_and_frozen_rerun(self):
        from types import ModuleType
        from enum import Enum
        class SearchType(str, Enum):
            RAG_COMPLETION = 'RAG_COMPLETION'
            GRAPH_COMPLETION = 'GRAPH_COMPLETION'
        fake = ModuleType('cognee'); fake.__path__ = []
        items = ModuleType('cognee.tasks.ingestion.data_item');items.DataItem = SimpleNamespace
        search_types = ModuleType('cognee.modules.search.types');search_types.SearchType = SearchType
        with tempfile.TemporaryDirectory() as d:
            root = Path(d);out = root/'run';env=root/'env';env.write_text('synthetic config')
            corpus=root/'corpus.jsonl';corpus.write_text(json.dumps({'id':'record-a','content':'Synthetic lesson'})+'\n')
            cases=root/'cases.json';cases.write_text(json.dumps([CASE]))
            seen=[]
            async def remember(item, **kwargs):
                seen.append(('ingest',item.data));return {'status':'ok'}
            async def search(**kwargs):
                protocol=json.loads((out/'protocol.json').read_text())
                self.assertEqual(protocol['cases_sha256'],haystack.sha(cases))
                seen.append(('search',kwargs['query_type'].value))
                return [{'context_result':'Record record-a: Synthetic lesson'}]
            fake.remember=remember;fake.search=search
            args=SimpleNamespace(out=out,env=env,corpus=corpus,cases=cases,actual_model='test',cutoff=None,chunk_size=512,top_k=5,record_timeout=1)
            modules={'cognee':fake,'cognee.tasks.ingestion.data_item':items,'cognee.modules.search.types':search_types}
            with patch.dict(sys.modules,modules),patch.object(local_guard,'configure',return_value={'actual_llm':'test','llm_alias_digest':'abc'}),redirect_stdout(io.StringIO()):
                asyncio.run(haystack.ingest(args))
                asyncio.run(haystack.retrieve(args))
                before=(out/'contexts.jsonl').read_bytes()
                asyncio.run(haystack.retrieve(args))
            self.assertEqual([x[0] for x in seen],['ingest','search','search'])
            self.assertEqual(before,(out/'contexts.jsonl').read_bytes())
            self.assertEqual(json.loads((out/'protocol.json').read_text())['status'],'retrieved')
            self.assertEqual(len(before.splitlines()),2)

if __name__ == '__main__':unittest.main()
