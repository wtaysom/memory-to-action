"""Bounded decision trials: does what the reader is handed change the action it takes?

One trial = one case, one condition (a rendering of memory, or nothing), one model, one seed.
The reader gets the task and its choices, plus the condition's context, and may spend up to
MAX_TURNS JSON actions: read_memory (the full record), read_source (a supporting document, if the
case supplies one), or finish with a zero-based choice. Scoring is the chosen index against the
case's expected index. Prose is kept for inspection and never scored.

Inputs:
  cases.json      list of cases; see cases/README.md for the schema
  contexts.jsonl  optional: {"case": id, "condition": name, "context": text} rows that add or
                  override a condition's context per case (retrieval packets, for example)
Outputs (in --out):
  trials.jsonl    one receipt per trial, appended; reruns skip completed (case, condition, model, seed)
  freeze.json     sha256 of the case file and the run settings, written once; later runs must match

Reader endpoint: Ollama's /api/chat by default (OLLAMA_URL), any model Ollama serves.
"""
import argparse, hashlib, json, os, random, time, urllib.request
from pathlib import Path

SYSTEM = '''You are making a bounded decision in a simulated maintenance task.
Return ONE JSON object. Available actions:
{"tool":"read_memory","id":"full UUID or its unique prefix"} opens the entire historical record.
{"tool":"read_source","path":"source path shown in context"} opens its supporting document if available.
{"tool":"finish","choice":0,"reason":"brief evidence-based reason"} selects an option (zero-based).
You have at most three responses, including your final choice. You may decide immediately if evidence is sufficient.
Use current verified observations when they differ from old records. Do not invent evidence.
Historical context may be incomplete. You have no other tools or conversation history.'''

MAX_TURNS = 3
OPTIONS = dict(temperature=0.3, num_ctx=8192, num_predict=200)


def trial(case, condition, model, seed, context, ollama_url):
    prompt = case['task'] + '\nOptions:\n' + '\n'.join(f'{i}: {s}' for i, s in enumerate(case['choices']))
    if context:
        prompt += '\n\n' + context
    messages = [dict(role='system', content=SYSTEM), dict(role='user', content=prompt)]
    receipt = dict(case=case['id'], stratum=case.get('stratum'), condition=condition, model=model,
                   seed=seed, input=list(messages), steps=[], passed=False)
    started = time.monotonic()
    for _ in range(MAX_TURNS):
        body = dict(model=model, messages=messages, stream=False, format='json', think=False,
                    options=dict(seed=seed, **OPTIONS))
        req = urllib.request.Request(ollama_url, data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'})
        try:
            resp = json.load(urllib.request.urlopen(req, timeout=180))
            content = resp['message']['content']
            step = dict(output=content, prompt_tokens=resp.get('prompt_eval_count'),
                        output_tokens=resp.get('eval_count'), duration_ns=resp.get('total_duration'))
            receipt['steps'].append(step)
            action = json.loads(content)
            messages.append(dict(role='assistant', content=content))
            tool = action.get('tool')
            if tool == 'finish':
                receipt['choice'] = action.get('choice')
                receipt['passed'] = type(action.get('choice')) is int and action['choice'] == case['expected']
                break
            if tool == 'read_memory':
                mid = action.get('id', '')
                ok = isinstance(mid, str) and len(mid) >= 8 and str(case['memory']['id']).startswith(mid)
                result = json.dumps(case['memory'], ensure_ascii=False) if ok else 'No matching supplied memory.'
            elif tool == 'read_source':
                result = case.get('sources', {}).get(action.get('path'), 'No such supplied source.')
            else:
                result = 'Invalid tool. Choose read_memory, read_source, or finish.'
            step['tool_result'] = result
            messages.append(dict(role='user', content='Tool result:\n' + result))
        except Exception as exc:
            receipt['error'] = type(exc).__name__ + ': ' + str(exc)
            break
    receipt['elapsed_seconds'] = round(time.monotonic() - started, 3)
    return receipt


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cases', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--contexts', type=Path, help='contexts.jsonl adding/overriding per-case conditions')
    ap.add_argument('--conditions', default='none', help='comma list; "none" is always task+choices only')
    ap.add_argument('--models', default='qwen3.5:4b,gemma3:4b')
    ap.add_argument('--seeds', default='11,29,47')
    ap.add_argument('--ollama-url', default=os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/chat'))
    a = ap.parse_args()
    cases = json.loads(a.cases.read_text())
    conditions = [c.strip() for c in a.conditions.split(',')]
    models = [m.strip() for m in a.models.split(',')]
    seeds = [int(s) for s in a.seeds.split(',')]
    if len({c['id'] for c in cases}) != len(cases):
        raise SystemExit('Duplicate case IDs.')
    for values in (conditions, models, seeds):
        if not values or len(values) != len(set(values)) or '' in values:
            raise SystemExit('Conditions, models and seeds must be nonempty and unique.')
    for c in cases:
        if type(c['expected']) is not int or not 0 <= c['expected'] < len(c['choices']):
            raise SystemExit(f'Invalid expected action for {c["id"]}')
    extra = {}
    if a.contexts:
        for row in map(json.loads, a.contexts.read_text().splitlines()):
            key = (row['case'], row['condition'])
            if key in extra:
                raise SystemExit(f'Duplicate context: {key}')
            extra[key] = row['context']
    a.out.mkdir(parents=True, exist_ok=True)
    freeze = dict(cases_sha256=hashlib.sha256(a.cases.read_bytes()).hexdigest(),
                  contexts_sha256=hashlib.sha256(a.contexts.read_bytes()).hexdigest() if a.contexts else None,
                  models=models, seeds=seeds, conditions=conditions, max_turns=MAX_TURNS, options=OPTIONS,
                  ollama_url=a.ollama_url, system_sha256=hashlib.sha256(SYSTEM.encode()).hexdigest(),
                  runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    fp = a.out / 'freeze.json'
    if fp.exists():
        prior = json.loads(fp.read_text())
        if prior != freeze:
            raise SystemExit('Inputs, settings or runner differ from the frozen run in --out; use a new directory.')
    else:
        if (a.out / 'trials.jsonl').exists():
            raise SystemExit('Existing trials lack a freeze; use a new output directory.')
        fp.write_text(json.dumps(freeze, indent=2))
    dest = a.out / 'trials.jsonl'
    prior_rows = list(map(json.loads, dest.read_text().splitlines())) if dest.exists() else []
    done = {(r['case'], r['condition'], r['model'], r['seed']) for r in prior_rows}
    expected_grid = {(c['id'], cond, model, seed) for c in cases for cond in conditions
                     for model in models for seed in seeds}
    if len(done) != len(prior_rows) or not done <= expected_grid:
        raise SystemExit('Duplicate or out-of-grid trial receipts.')
    for model in models:
        jobs = [(c, cond, s) for c in cases for cond in conditions for s in seeds]
        random.Random(20260911).shuffle(jobs)
        for c, cond, s in jobs:
            if (c['id'], cond, model, s) in done:
                continue
            ctx = '' if cond == 'none' else extra.get((c['id'], cond), c.get('contexts', {}).get(cond, ''))
            if cond != 'none' and not ctx:
                raise SystemExit(f'No context for case {c["id"]} condition {cond}')
            r = trial(c, cond, model, s, ctx, a.ollama_url)
            with dest.open('a') as f:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
            print(model, c['id'], cond, s, r['passed'], r.get('error', ''), flush=True)


if __name__ == '__main__':
    main()
