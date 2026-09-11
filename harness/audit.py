"""Coverage of frozen retrieval packets and paired reader results.

  python audit.py --contexts out/contexts.jsonl --evidence cases/evidence-sets.json \
                  --trials out/trials.jsonl [--baseline other/trials.jsonl]

Coverage is reported two ways per condition: the designated target's id present in the packet,
and target-or-valid-alternative present. An id mention is not proof that the decision-relevant
passage arrived; do a passage-level read for the cases that matter. Paired counts compare each
(case, model, seed) across conditions, which is the honest unit when seeds are few.
"""
import argparse, collections, json
from pathlib import Path


def load(p):
    return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--trials', required=True)
    ap.add_argument('--baseline', help='trials.jsonl holding control conditions (none, text_target) to pair against')
    ap.add_argument('--contexts')
    ap.add_argument('--evidence', help='{"cases": {id: {"target": id, "alternative_valid": [ids]}}}')
    a = ap.parse_args()
    rows = load(a.trials) + (load(a.baseline) if a.baseline else [])
    conds = sorted({r['condition'] for r in rows}, key=lambda c: (c != 'none', c))
    tot, n, tok, err = (collections.Counter() for _ in range(4))
    for r in rows:
        k = (r['model'], r['condition']); tot[k] += r['passed']; n[k] += 1
        tok[k] += sum((s.get('prompt_tokens') or 0) for s in r['steps']); err[k] += bool(r.get('error'))
    models = sorted({r['model'] for r in rows})
    print('| Model | ' + ' | '.join(conds) + ' |'); print('|---|' + '---:|' * len(conds))
    for m in models:
        print(f'| {m} | ' + ' | '.join(
            f"{tot[(m,c)]}/{n[(m,c)]} ({tok[(m,c)]//max(1,n[(m,c)])} tok{', '+str(err[(m,c)])+' err' if err[(m,c)] else ''})"
            if n[(m, c)] else '—' for c in conds) + ' |')
    by = collections.defaultdict(dict)
    for r in rows:
        by[(r['case'], r['model'], r['seed'])][r['condition']] = r['passed']
    print('\nPaired (same case, model, seed):')
    for c in conds:
        for base in conds:
            if base == c or base not in ('none', 'text_target'):
                continue
            imp = sum(1 for d in by.values() if c in d and base in d and d[c] and not d[base])
            reg = sum(1 for d in by.values() if c in d and base in d and d[base] and not d[c])
            same = sum(1 for d in by.values() if c in d and base in d and d[c] == d[base])
            print(f'  {c} vs {base}: improved {imp}, regressed {reg}, unchanged {same}')
    if a.contexts and a.evidence:
        ev = json.loads(Path(a.evidence).read_text())['cases']
        cov = collections.defaultdict(lambda: [0, 0, 0])
        for row in load(a.contexts):
            e = ev[row['case']]; ctx = row['context']
            t = str(e['target'])[:8] in ctx
            alt = any(str(x)[:8] in ctx for x in e.get('alternative_valid', []))
            cov[row['condition']][0] += t; cov[row['condition']][1] += (t or alt); cov[row['condition']][2] += 1
        print('\nCoverage by id prefix (target / target-or-alternative / cases):')
        for c, (t, ta, k) in sorted(cov.items()):
            print(f'  {c}: {t}/{k} target, {ta}/{k} target-or-alternative')
    hot = [(r['model'], r['case'], r['condition']) for r in rows
           if r['steps'] and max((s.get('prompt_tokens') or 0) for s in r['steps']) > 7000]
    print('\nBudget pressure (>7000 prompt tokens in one turn):', hot or 'none')


if __name__ == '__main__':
    main()
