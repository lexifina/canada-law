"""Checks the git repository against the official text: every point-in-time version of every act on the Justice Laws
Website, read back from git with tools/on_date.py on the day it took effect, must equal that version's text.

    python -X utf8 scripts/canada-law/check_repo.py [--repo ../canada-law] [--no-record]

Two checks per version, from the cached HTML (no network):
1. File by file: the act's files in git on that day are exactly the files the build's parser makes from that version's
   page (same set of files, same bytes).
2. Word for word: the whole act printed by on_date.py, with its markdown marks removed, has the same words in the same
   order as the whole official text, read independently of the parser: every text node of the version's text block
   (`div.wb-txthl`), except the line naming the version's dates (`div.info`), the definition-term index (`dt`, whose
   term each definition repeats) and the text shown only to screen readers (`wb-invisible`).
The result is written to verification.json next to this script (unless --no-record), for REPRODUCE.md.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from lxml import html as lhtml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lawtext  # noqa: E402  (the parser; build.py, for the point-in-time pages, only in main())

TOKEN = re.compile(r'\w+|[^\w\s]')
BLOCKS = {'div', 'br', 'p', 'td', 'th', 'tr', 'table', 'li', 'ul', 'dl', 'dd', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
          'section', 'header', 'figure', 'figcaption'}
HEADING_PARTS = {'HLabel1', 'HLabel2', 'HLabel3', 'HLabel4', 'HTitleText1', 'HTitleText2', 'HTitleText3', 'HTitleText4',
                 'scheduleLabel', 'OriginatingRef', 'scheduleTitleText'}


def official_words(raw: bytes) -> list[str]:
    doc = lhtml.fromstring(raw.decode('utf-8'))
    top = doc.get_element_by_id('wb-cont').xpath('./section/div[contains(concat(" ", @class, " "), " wb-txthl ")]')[0]

    def text(e) -> str:
        if not isinstance(e.tag, str):
            return e.tail or ''
        cls = (e.get('class') or '').split()
        if (e.tag == 'dt' and 'FormulaTerm' not in cls) or 'wb-invisible' in cls or 'info' in cls:
            return e.tail or ''
        # Inline elements join the words around them as the page shows them; block elements (and the spans that
        # hold a heading's label and title, shown on lines of their own) separate words.
        gap = ' ' if e.tag in BLOCKS or HEADING_PARTS & set(cls) else ''
        return gap + (e.text or '') + ''.join(text(c) for c in e) + gap + (e.tail or '')
    top.tail = None
    return TOKEN.findall(text(top).replace('­', ''))


def repo_words(text: str) -> list[str]:
    lines = []
    for l in text.split('\n'):
        if l.strip() == 'History:':
            continue
        l = re.sub(r'^\s*(#+ |- )', '', l)
        l = re.sub(r'^Marginal note: ', '', l)
        lines.append(l.replace(' | ', ' '))
    return TOKEN.findall(' '.join(lines))


def tool(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, 'tools/on_date.py', *args], cwd=repo, capture_output=True, text=True,
                          encoding='utf-8')


def files_at(repo: str, commit: str, slug: str) -> dict[str, str]:
    """The act's files at a commit, read with one ls-tree and one cat-file --batch (not one git show per file)."""
    out = subprocess.run(['git', 'ls-tree', '-r', commit, f'{slug}/'], cwd=repo, capture_output=True,
                         text=True, encoding='utf-8').stdout.split('\n')
    blobs = []
    for line in out:
        if not line:
            continue
        info, f = line.split('\t', 1)
        if f.endswith('.md') and not f.endswith('/README.md'):
            blobs.append((f[len(slug) + 1:], info.split()[2]))
    if not blobs:
        return {}
    data = subprocess.run(['git', 'cat-file', '--batch'], cwd=repo, input=''.join(f'{sha}\n' for _, sha in blobs).encode(),
                          capture_output=True).stdout
    res, pos = {}, 0
    for name, _ in blobs:
        nl = data.index(b'\n', pos)
        size = int(data[pos:nl].split()[2])
        res[name] = data[nl + 1:nl + 1 + size].decode('utf-8')
        pos = nl + 1 + size + 1
    return res


def main():
    ap = argparse.ArgumentParser()
    import build  # the point-in-time pages (needs the pages, read once by build.py)
    ap.add_argument('--repo', default=str(build.ROOT.parent / 'canada-law'))
    ap.add_argument('--no-record', action='store_true')
    args = ap.parse_args()
    versions = files = bad = words = wbad = 0
    nwords = 0
    per_act = {}
    sys.path.insert(0, str(Path(args.repo) / 'tools'))
    import on_date
    import os
    cwd = os.getcwd()
    tasks = []
    for act in build.ACTS:
        slug = act['id']
        for v in build.history(act, offline=True):
            os.chdir(args.repo)
            try:
                commit = on_date.commit_on(v['from'], slug)
            finally:
                os.chdir(cwd)
            tasks.append((slug, v, commit))

    def one(t):
        slug, v, commit = t
        raw = build.fetch(v['url'], offline=True)
        parsed = build.read_version(raw)
        expected = {build.file_name(k): u['text'] for k, u in parsed['units'].items()}
        got = files_at(args.repo, commit, slug) if commit else {}
        whole = tool(args.repo, v['from'], slug)
        return slug, v, expected, got, whole, official_words(raw), repo_words(whole.stdout)

    results = [one(t) for t in tasks]
    for slug, v, expected, got, whole, ow, rw in results:
        versions += 1
        per_act[slug] = per_act.get(slug, 0) + 1
        files += len(expected)
        if got != expected:
            bad += 1
            diff = sorted(set(got) ^ set(expected)) or [k for k in expected if got.get(k) != expected[k]]
            print(f'MISMATCH {slug} {v["from"]}: {diff[:5]}')
        words += 1
        nwords += len(ow)
        if whole.returncode or ow != rw:
            wbad += 1
            i = next((i for i, (a, b) in enumerate(zip(ow, rw)) if a != b), min(len(ow), len(rw)))
            print(f'WORDS {slug} {v["from"]}: official {len(ow)} vs repo {len(rw)} words; first difference at '
                  f'{i}: {" ".join(ow[max(0, i - 6):i + 6])!r} / {" ".join(rw[max(0, i - 6):i + 6])!r}')
    print(f'{versions} versions checked ({files} files), {bad} mismatches; {words} versions word for word '
          f'({nwords} words), {wbad} mismatches')
    print('per act:', per_act)
    if not args.no_record:
        p = HERE / 'verification.json'
        rec = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
        rec['check'] = {'versions': versions, 'files': files, 'mismatches': bad, 'wordcheck': words,
                        'words': nwords, 'word_mismatches': wbad, 'per_act': per_act}
        p.write_text(json.dumps(rec, indent=1, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    raise SystemExit(1 if bad or wbad else 0)


if __name__ == '__main__':
    main()
