"""Explicit configuration for the synthetic probes; no private-workspace lookup."""
import importlib
import hashlib
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent

def configure():
    env = ROOT / '.env'
    if not env.is_file():
        raise SystemExit('Create probe/.env from env.example or env.local-example first.')
    load_dotenv(env, override=True)
    os.environ['TELEMETRY_DISABLED'] = 'true'
    os.environ['CACHING'] = 'false'
    if os.environ.get('LLM_PROVIDER') == 'openai':
        sys.path.insert(0, str(ROOT.parent / 'harness'))
        from local_guard import configure as local_configure
        local_configure(env, ROOT / '.probe-storage', os.environ.get('ACTUAL_MODEL'))
    else:
        key = os.environ.get('GEMINI_API_KEY')
        if os.environ.get('LLM_PROVIDER') == 'gemini' and key:
            os.environ.setdefault('LLM_API_KEY', key)
            os.environ.setdefault('EMBEDDING_API_KEY', key)
        os.environ['DATA_ROOT_DIRECTORY'] = str(ROOT / '.probe-storage' / 'data')
        os.environ['SYSTEM_ROOT_DIRECTORY'] = str(ROOT / '.probe-storage' / 'system')
    if not all(os.environ.get(k) for k in ('LLM_MODEL', 'LLM_API_KEY', 'EMBEDDING_API_KEY')):
        raise SystemExit('Set model and provider keys explicitly in probe/.env or environment.')
    return importlib.import_module('cognee')


def config_sha256():
    """Hash the explicit config without putting its keys into a protocol."""
    return hashlib.sha256((ROOT / '.env').read_bytes()).hexdigest()
