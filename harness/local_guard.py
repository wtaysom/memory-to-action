"""Python socket allowlist for configured loopback/private-network Cognee endpoints.

Loads a dotenv config, refuses any endpoint that resolves outside loopback/private ranges, installs a
Python audit hook that blocks DNS and connections to every other host, strips cloud API keys and
proxies, and returns an identity receipt (which local weights actually sit behind the model alias,
which embedder, its declared limits) so a frozen protocol can prove what ran.

Model-name lookup can select a different structured-output path for an alias. See
../diagnostic/COGNEE-NOTES.md for the tested names and limits. Private-network endpoints
may be other machines. This Python audit hook is not an OS sandbox and does not
constrain arbitrary native libraries or subprocesses.
"""
import ipaddress, json, os, socket, sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import build_opener, ProxyHandler

from dotenv import dotenv_values


def configure(env_file, storage_root, actual_model=None):
    if not Path(env_file).is_file():
        raise RuntimeError(f'Missing explicit configuration: {env_file}')
    values = {k: v for k, v in dotenv_values(env_file).items() if v is not None}
    for key, value in values.items():
        os.environ[key] = value
    for key in ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'ANTHROPIC_API_KEY', 'OPENAI_API_KEY',
                'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']:
        os.environ.pop(key, None)
    os.environ['OPENAI_API_KEY'] = values.get('LLM_API_KEY', 'local')
    os.environ['OPENAI_BASE_URL'] = values['LLM_ENDPOINT']
    os.environ['TELEMETRY_DISABLED'] = 'true'
    os.environ['CACHING'] = 'false'
    os.environ.setdefault('COGNEE_SKIP_CONNECTION_TEST', 'true')  # the 30 s preflight times out on a busy local GPU
    os.environ['DATA_ROOT_DIRECTORY'] = str(Path(storage_root).resolve() / 'data')
    os.environ['SYSTEM_ROOT_DIRECTORY'] = str(Path(storage_root).resolve() / 'system')
    hosts = {'localhost', '127.0.0.1', '::1'}
    for key in ('LLM_ENDPOINT', 'EMBEDDING_ENDPOINT'):
        hosts.add(urlparse(values[key]).hostname)
    os.environ['NO_PROXY'] = os.environ['no_proxy'] = ','.join(sorted(hosts))
    allowed, addresses = set(hosts), {}
    for host in hosts:
        addresses[host] = sorted({r[4][0] for r in socket.getaddrinfo(host, None)})
        for addr in addresses[host]:
            ip = ipaddress.ip_address(addr)
            if not (ip.is_private or ip.is_loopback):
                raise RuntimeError(f'{host} resolves outside the private network: {addr}')
        allowed.update(addresses[host])

    def audit(event, args):
        if event == 'socket.getaddrinfo':
            host = args[0].decode('ascii') if isinstance(args[0], bytes) else args[0]
            if host is not None and str(host) not in allowed:
                raise PermissionError('local-only runtime blocked DNS for ' + str(host))
        if event == 'socket.connect' and isinstance(args[1], tuple) and str(args[1][0]) not in allowed:
            raise PermissionError('local-only runtime blocked connection to ' + str(args[1][0]))
    sys.addaudithook(audit)

    opener = build_opener(ProxyHandler({}))
    identity = dict(llm_alias=values['LLM_MODEL'], llm_endpoint=values['LLM_ENDPOINT'],
                    embedding_endpoint=values['EMBEDDING_ENDPOINT'], allowed_addresses=addresses,
                    guard='Python socket audit hook blocks DNS/connections outside the listed local endpoints.')
    try:  # Ollama: prove which weights sit behind the alias
        base = values['LLM_ENDPOINT'].rsplit('/v1', 1)[0]
        with opener.open(base + '/api/tags', timeout=10) as r:
            models = {m['name']: m['digest'] for m in json.load(r)['models']}
        alias = values['LLM_MODEL'] if ':' in values['LLM_MODEL'] else values['LLM_MODEL'] + ':latest'
        identity['llm_alias_digest'] = models.get(alias)
        if actual_model:
            identity['actual_llm'] = actual_model
            actual_tag = actual_model if ':' in actual_model else actual_model + ':latest'
            if not models.get(actual_tag) or not models.get(alias):
                raise RuntimeError('Declared model or alias missing from Ollama tags.')
            if models[actual_tag] != models[alias]:
                raise RuntimeError('Alias digest differs from the declared actual model.')
    except OSError as exc:
        if actual_model:
            raise RuntimeError('Cannot verify the requested model identity.') from exc
        identity['llm_alias_digest'] = 'unavailable (not Ollama?)'
    try:  # text-embeddings-inference: declared limits, so batches and inputs can be bounded
        with opener.open(values['EMBEDDING_ENDPOINT'].rsplit('/v1', 1)[0] + '/info', timeout=10) as r:
            info = json.load(r)
        identity['embedding_info'] = info
        batch = int(values.get('EMBEDDING_BATCH_SIZE', '36'))
        if batch > info.get('max_client_batch_size', batch):
            raise RuntimeError('EMBEDDING_BATCH_SIZE exceeds the server maximum; Cognee will retry a 413 unchanged.')
    except OSError:
        identity['embedding_info'] = 'unavailable (no /info endpoint)'
    return identity
