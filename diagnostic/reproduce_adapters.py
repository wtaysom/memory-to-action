"""Offline synthetic reproductions for Cognee 1.5.4 adapter behavior.
No private corpus, credentials, live services, or LLM inference are used.
"""
import os
os.environ['TELEMETRY_DISABLED']='true'
os.environ['CACHING']='false'
os.environ['LITELLM_LOCAL_MODEL_COST_MAP']='True'
import asyncio
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys
# Mock transports below do not require sockets. Fail closed on accidental egress.
def deny_network(event,args):
    if event in ('socket.getaddrinfo','socket.connect'):
        raise PermissionError('Offline reproduction forbids network access')
sys.addaudithook(deny_network)
import httpx
from openai import AsyncOpenAI
import litellm
from pydantic import BaseModel
from tenacity import stop_after_attempt,wait_none
from cognee.infrastructure.llm.structured_output_framework.litellm_native.native_adapter import NativeLiteLLMAdapter,_supports_native_schema
from cognee.infrastructure.databases.vector.embeddings.OpenAICompatibleEmbeddingEngine import OpenAICompatibleEmbeddingEngine

class TinyRecord(BaseModel):
    name:str

async def schema_routing():
    captured=[]
    async def completion(**kwargs):
        fmt=kwargs['response_format']
        captured.append({'model':kwargs['model'],'format':fmt if isinstance(fmt,dict) else fmt.__name__})
        return litellm.ModelResponse(choices=[{'message':{'role':'assistant','content':'{"name":"synthetic example"}'}}])
    for model in ['ollama/gemma3:12b','gpt-4o']:
        adapter=NativeLiteLLMAdapter(api_key='synthetic',model=model,max_completion_tokens=100,endpoint='http://localhost:11434/v1')
        with patch('litellm.acompletion',new=completion):
            result=await adapter._acreate_structured('A synthetic example.','Return a record.',TinyRecord,model=model,api_key='synthetic',endpoint='http://localhost:11434/v1',api_version=None)
            assert result.name=='synthetic example'
    assert captured[0]['format']=={'type':'json_object'}
    assert captured[1]['format']=='TinyRecord' or captured[1]['format'].get('type')=='json_schema'
    return {'capabilities':{m:_supports_native_schema(m) for m in ['ollama/gemma3:12b','gpt-4o']},'requests':captured,'meaning':'Model-name routing reproduced with mocked completion; no claim about output quality or live server enforcement.'}

async def validation_retry(kind):
    calls=[]
    message=('batch size 36 > maximum allowed batch size 32' if kind=='batch' else
             'Input validation error: `inputs` must have less than 2048 tokens. Given: 2402')
    async def handle(request):
        body=json.loads(request.content)
        calls.append({'input_count':len(body['input']),'request_sha256':hashlib.sha256(request.content).hexdigest()})
        # Simulate TEI's exact validation error; synthetic text is not asserted
        # to tokenize to 2,402 under a real tokenizer.
        return httpx.Response(413,json={'message':message,'code':413,'type':'Validation'},request=request)
    with patch.object(OpenAICompatibleEmbeddingEngine,'get_tokenizer',return_value=SimpleNamespace()):
        engine=OpenAICompatibleEmbeddingEngine(model='synthetic-embedding-model',dimensions=3,endpoint='http://localhost:8080/v1',api_key='synthetic')
    await engine._client.close()
    engine._client=AsyncOpenAI(api_key='synthetic',base_url='http://localhost:8080/v1',max_retries=0,http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle)))
    inputs=['synthetic sentence']*36 if kind=='batch' else ['synthetic long text '*2500]
    # Keep the package's retry predicate and error mapping, but bound the
    # reproduction to two attempts and remove delays (production uses backoff).
    bounded=OpenAICompatibleEmbeddingEngine.embed_text.retry_with(stop=stop_after_attempt(2),wait=wait_none())
    try:
        await bounded(engine,inputs)
        raise AssertionError('Expected validation rejection')
    except Exception as exc:
        status=getattr(exc,'status_code',None)
        assert len(calls)==2 and len({x['request_sha256'] for x in calls})==1
        assert status==422,(type(exc).__name__,status)
        result={'case':kind,'configured_default_batch':engine.get_batch_size(),'upstream_status':413,'upstream_message':message,'wrapped_exception':type(exc).__name__,'wrapped_status':status,'attempts':len(calls),'identical_request_retried':True,'meaning':'Real Cognee/OpenAI-SDK error handling; mocked server validation, retry stop shortened to two attempts.'}
    finally:await engine._client.close()
    return result

async def main():
    report={'versions':{p:version(p) for p in ['cognee','litellm','openai','pydantic','tenacity','httpx']},'network':'blocked by socket audit hook','schema_routing':await schema_routing(),'embedding_validation':[await validation_retry('batch'),await validation_retry('input')]}
    dest=Path(__file__).with_name('adapter-reproduction-results.json')
    dest.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':asyncio.run(main())
