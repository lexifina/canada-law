"""Checks the acts appended from Justice Canada's XML repository against that source, as check_repo.py checks the
point-in-time acts against the site's pages:

    python -X utf8 scripts/canada-law/check_xml.py --xml <laws-lois-xml clone> --repo ../canada-law --acts C-46,I-3.3

1. File by file: every version of each act (each consolidation in the XML history, and each version rebuilt between two
   of them from the provisions' in-force days), read back from git with tools/on_date.py on the day it took effect, is
   exactly the files the build's parser makes from it.
2. Word for word: for each consolidation, the whole act printed by on_date.py, its markdown marks removed, has the same
   words in the same order as all the text of the consolidation's HTML (the repository's transform), read without the
   build's parser (check_repo.official_words).
"""
import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lawtext as B  # noqa: E402
import check_repo as K  # noqa: E402
import xmlsource as S  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xml', required=True)
    ap.add_argument('--upto', default='HEAD')
    ap.add_argument('--repo', required=True)
    ap.add_argument('--acts', required=True)
    ap.add_argument('--regulations', action='store_true')
    ap.add_argument('--today', required=True)
    ap.add_argument('--record', default=None, help='write the result to this JSON file')
    args = ap.parse_args()
    B.TOLERANT = True
    src = S.Source(Path(args.xml), args.upto)
    sys.path.append(str(Path(args.repo) / 'tools'))
    import on_date
    folder = 'eng/regulations' if args.regulations else 'eng/acts'
    total = {'versions': 0, 'files': 0, 'mismatches': 0, 'wordcheck': 0, 'words': 0, 'word_mismatches': 0,
             'per_act': {}}
    for ident in [a for a in args.acts.split(',') if a]:
        rel = f'{folder}/{ident}.xml'
        vs = [v for v in S.versions(src, rel, []) if v['from'] <= args.today]
        raws = {s['commit']: s['raw'] for s in src.states(rel)}
        cwd = os.getcwd()
        tasks = []
        for v in vs:
            os.chdir(args.repo)
            try:
                tasks.append((v, on_date.commit_on(v['from'], ident)))
            finally:
                os.chdir(cwd)

        def one(t):
            v, commit = t
            want = {B.file_name(k): u['text'] for k, u in v['units'].items()}
            got = K.files_at(args.repo, commit, ident) if commit else {}
            if not v['snapshot']:
                return v, want, got, None, None
            whole = K.tool(args.repo, v['from'], ident)
            ow = K.official_words(src.html(raws[v['commit']], 'x'))
            return v, want, got, ow, K.repo_words(whole.stdout) if whole.returncode == 0 else None
        res = [one(t) for t in tasks]
        n = bad = wn = wbad = words = 0
        for v, want, got, ow, rw in res:
            n += 1
            total['files'] += len(want)
            if got != want:
                bad += 1
                print(f'MISMATCH {ident} {v["from"]}: {sorted(f for f in set(got) | set(want) if got.get(f) != want.get(f))[:5]}')
            if ow is not None:
                wn += 1
                words += len(ow)
                if ow != rw:
                    wbad += 1
                    rw = rw or []
                    i = next((i for i, (a, b) in enumerate(zip(ow, rw)) if a != b), min(len(ow), len(rw)))
                    print(f'WORDS {ident} {v["from"]}: official {len(ow)} vs repo {len(rw)}; at {i}: '
                          f'{" ".join(ow[max(0, i - 6):i + 6])!r} / {" ".join(rw[max(0, i - 6):i + 6])!r}')
        print(f'{ident}: {n} versions ({sum(1 for v in vs if not v["snapshot"])} rebuilt), {bad} mismatches; '
              f'{wn} word for word ({words} words), {wbad} mismatches')
        total['versions'] += n
        total['mismatches'] += bad
        total['wordcheck'] += wn
        total['words'] += words
        total['word_mismatches'] += wbad
        total['per_act'][ident] = n
    print(json.dumps({k: v for k, v in total.items() if k != 'per_act'}))
    if args.record:
        Path(args.record).write_text(json.dumps(total, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    raise SystemExit(1 if total['mismatches'] or total['word_mismatches'] else 0)


if __name__ == '__main__':
    main()
