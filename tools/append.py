"""Grows the published repository append-only with Acts and regulations from Justice Canada's XML repository.

    python -X utf8 append.py --xml <clone of justicecanada/laws-lois-xml> --repo <clone of lexifina/canada-law>
                             --acts C-46,I-3.3 [--regulations] [--dry-run]

Nothing published is rewritten. Each act main does not hold yet goes on top as one block: its first version, then one
commit per amending law per in-force day, then changes credited to no single law, exactly as build.py makes them
(build.analyse, build.change_message). An act main already holds gets only versions after its newest In-force day, and
only if every version it already has reads back from main unchanged; anything else is a correction and stops the run.

Author date: noon in Ottawa on the in-force day, as in build.py. Committer date: the published head's committer time plus
one second per appended commit, so the same head and the same source give the same hashes. Tags already on main are
never moved; act tags are '<act>/<day>', law tags '<law>/<day>' (or the bare '<law>' form main already uses).
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import subprocess
import sys
from pathlib import Path

from lxml import etree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lawtext as B  # noqa: E402
import xmlsource as S  # noqa: E402

ANNUAL = 'annual-statutes-lois-annuelles/en'
LAWS_LOIS = 'https://laws-lois.justice.gc.ca'


def git(repo: Path, *args: str, input: bytes | None = None) -> str:
    out = subprocess.run(['git', *args], cwd=repo, capture_output=True, input=input)
    if out.returncode:
        raise SystemExit(f'git {" ".join(args)} failed: {out.stderr.decode(errors="replace")}')
    return out.stdout.decode('utf-8')


# ---------------------------------------------------------------- the act and the laws that amend it

def act_info(src: S.Source, rel: str, ident: str) -> dict:
    raw = S.xgit(src.repo, 'cat-file', 'blob', f'{src.upto}:{rel}', binary=True)
    doc = etree.fromstring(raw, etree.XMLParser(huge_tree=True, resolve_entities=False, no_network=True))
    idn = doc.find('Identification')

    def txt(path):
        e = idn.find(path) if idn is not None else None
        return B.clean(''.join(e.itertext())) if e is not None else ''
    short = txt('ShortTitle') or txt('LongTitle') or txt('TitleText') or ident
    own = []
    cn = idn.find('Chapter/ConsolidatedNumber') if idn is not None else None
    asid = idn.find('Chapter/AnnualStatuteId') if idn is not None else None
    if asid is not None:
        n, y = B.clean(asid.findtext('AnnualStatuteNumber') or ''), B.clean(asid.findtext('YYYY') or '')
        own.append(f'{"R.S.C." if asid.get("revised-statute") == "yes" else "S.C."} {y}, c. {n}')
    elif cn is not None and cn.get('official') == 'yes':
        own.append(f'R.S.C. 1985, c. {B.clean(cn.text or "")}')
    inst = txt('InstrumentNumber')
    if inst:
        own.append(inst.replace(' ', ''))
    return {'id': ident, 'short': short, 'own': own, 'rel': rel, 'kind': doc.tag}


class Laws:
    """Titles and days of Royal Assent of the amending statutes (from 2001), in this order: the published laws.csv;
    the --titles file (data/law-titles.json: each statute's Annual Statutes page on the Justice Laws Website, read as
    build.law_meta reads it, the source of every title of P-8.6 and A-1); else the Annual Statute in the XML repository
    (the short title, else the long title, and the day of assent). Older statutes and regulations keep only their
    citation."""

    def __init__(self, src: S.Source, repo: Path, titles: Path | None):
        self.src = src
        self.files = {}
        for f in S.xgit(src.repo, 'ls-tree', '-r', '--name-only', src.upto, ANNUAL).splitlines():
            m = re.search(r'/(\d{4})-c(\d+)_[Ee]\.xml$', f)
            if m:
                self.files[(int(m.group(1)), int(m.group(2)))] = f
        self.known = {}
        for r in csv.DictReader(io.StringIO(git(repo, 'show', 'main:laws.csv'))):
            self.known.setdefault(r['law'], {'key': r['law'], 'label': r['law'], 'title': r['title'],
                                             'assented': r['assented'], 'url': r['source'], 'kind': r['kind']})
        self.titles = json.loads(titles.read_text(encoding='utf-8')) if titles else {}
        self.missing: list[str] = []
        self.used_titles: dict[str, dict] = {}
        self.from_xml: list[str] = []

    def annual(self, year: int, chapter: int) -> dict | None:
        f = self.files.get((year, chapter))
        if not f:
            return None
        raw = S.xgit(self.src.repo, 'cat-file', 'blob', f'{self.src.upto}:{f}', binary=True)
        doc = etree.fromstring(raw, etree.XMLParser(huge_tree=True, resolve_entities=False, no_network=True,
                                                    load_dtd=False))
        idn = doc.find('Identification')
        t = idn.find('ShortTitle') if idn.find('ShortTitle') is not None else idn.find('LongTitle')
        d = idn.find('BillHistory/Stages[@stage="assented-to"]/Date')
        return {'title': B.clean(''.join(t.itertext())) if t is not None else '',
                'assented': f'{int(d.findtext("YYYY")):04d}-{int(d.findtext("MM")):02d}-{int(d.findtext("DD")):02d}'
                if d is not None else ''}

    def meta(self, k: str) -> dict:
        if k in self.known:
            return self.known[k]
        m = re.fullmatch(r'S\.C\. (\d{4}), c\. (\d+)', k)
        if not (m and int(m.group(1)) >= 2001):
            kind = 'Statutory instrument' if k.startswith('SI/') else \
                'Regulation (SOR)' if k.startswith('SOR/') else 'Act of Parliament'
            return {'key': k, 'label': k, 'title': '', 'assented': '', 'url': '', 'kind': kind}
        url = f'{LAWS_LOIS}/eng/AnnualStatutes/{m.group(1)}_{m.group(2)}/'
        a = None
        if k in self.titles:
            a = self.titles[k]
            self.used_titles[k] = a
        else:
            a = self.annual(int(m.group(1)), int(m.group(2)))
            if a is not None:
                self.from_xml.append(k)
        if a is None:
            self.missing.append(k)
            return {'key': k, 'label': k, 'title': '', 'assented': '', 'url': '', 'kind': 'Act of Parliament'}
        return {'key': k, 'label': k, 'title': a['title'], 'assented': a['assented'], 'url': url,
                'kind': 'Act of Parliament'}


# ---------------------------------------------------------------- what main already holds

def published(repo: Path) -> dict:
    head = git(repo, 'rev-parse', 'main').strip()
    origin = git(repo, 'rev-parse', 'origin/main').strip()
    if head != origin:
        raise SystemExit(f'main {head[:12]} is not origin/main {origin[:12]}')
    if git(repo, 'status', '--porcelain', '--untracked-files=no').strip():
        raise SystemExit(f'{repo} has uncommitted changes')
    ct, tz = git(repo, 'log', '-1', '--format=%ct %ci', 'main').split()[0::3]
    acts = {}
    for line in git(repo, 'ls-tree', '-d', '--name-only', 'main').split('\n'):
        if line and line not in ('data', 'tools'):
            acts[line] = ''
    out = git(repo, 'log', '--format=%H%x09%(trailers:key=In-force,valueonly,separator=)', '--name-only', 'main')
    cur = ''
    for line in out.split('\n'):
        if '\t' in line:
            cur = line.split('\t')[1].strip()
        elif '/' in line:
            a = line.split('/', 1)[0]
            if a in acts and cur > acts[a]:
                acts[a] = cur
    tags = set(git(repo, 'tag', '--list').split())
    return {'head': head, 'ct': int(ct), 'tz': tz, 'acts': acts, 'tags': tags}


def check_held(repo: Path, act: str, vs: list[dict], last: str) -> list[str]:
    """Every version main already holds must read back exactly."""
    import check_repo as K  # the builder's (next to this script)
    sys.path.append(str(repo / 'tools'))
    import on_date
    import os
    bad = []
    cwd = os.getcwd()
    for v in vs:
        if v['from'] > last:
            break
        os.chdir(repo)
        try:
            h = on_date.commit_on(v['from'], act)
        finally:
            os.chdir(cwd)
        got = K.files_at(str(repo), h, act) if h else {}
        want = {B.file_name(k): u['text'] for k, u in v['units'].items()}
        if got != want:
            bad.append(f'{act} {v["from"]}: {sorted(f for f in set(got) | set(want) if got.get(f) != want.get(f))[:4]}')
    return bad


# ---------------------------------------------------------------- messages

def start_message(b: dict) -> tuple[tuple[str, str], list[str], list[str]]:
    v = b['versions'][0]
    day = v['from']
    kind = 'regulation' if b['act'].get('kind') == 'Regulation' else 'act'
    msg = [f'{b["act"]["id"]}: {b["title"]}, as consolidated on {day}', '',
           f'The text of the earliest consolidated version in Justice Canada\'s XML repository of the consolidated Acts',
           f'and regulations, in force from {day}. It is the {kind} as enacted and amended up to then; the repository has',
           'no earlier versions, so the lines of this commit are credited to the publisher, not to a law. The historical',
           'note of each section lists the laws that made it.', '']
    trailers = [f'In-force: {day}', 'Kind: first published version (publisher)', f'Consolidated: {v["url"]}']
    return B.PUBLISHER, msg, trailers


def dated_by(item: dict) -> list[str]:
    """For a commit whose day is a version rebuilt between two snapshots."""
    out = []
    for b, ch in item['parts']:
        if ch is not None and not ch['cur'].get('snapshot', True):
            out.append('Dated-by: the in-force day the consolidated XML gives the changed provisions '
                       '(lims:inforce-start-date); no consolidation of this day is in the source')
            break
    return out


# ---------------------------------------------------------------- the append

def law_tag(law: str, day: str, tags: set[str], new: dict) -> str | None:
    base = B.tag_of(law)
    if base in tags or base in new:
        return None   # a bare tag of this law exists; a '<law>/<day>' tag cannot sit beside it
    name = f'{base}/{day}'
    return None if name in tags or name in new else name


def run(args) -> dict:
    repo, xr = Path(args.repo), Path(args.xml)
    B.TOLERANT = True
    src = S.Source(xr, args.upto)
    pub = published(repo)
    laws_src = Laws(src, repo, Path(args.titles) if args.titles else None)
    folder = 'eng/regulations' if args.regulations else 'eng/acts'
    ids = [a for a in args.acts.split(',') if a]
    built, problems, corrections, skipped = [], [], [], []
    for ident in ids:
        rel = f'{folder}/{ident}.xml'
        act = act_info(src, rel, ident)
        probs: list[str] = []
        vs = S.versions(src, rel, probs)
        vs = [v for v in vs if v['from'] <= args.today]
        problems += probs
        if not vs:
            skipped.append(f'{ident}: no versions')
            continue
        if ident in pub['acts']:
            last = pub['acts'][ident]
            bad = check_held(repo, ident, vs, last)
            if bad:
                corrections += bad
                continue
            held = [v for v in vs if v['from'] <= last]
            new = [v for v in vs if v['from'] > last]
            if not new:
                skipped.append(f'{ident}: main already holds every version (to {last})')
                continue
            act['based'] = True
            vs = held[-1:] + new
        b = B.analyse(act, vs)
        b['unreadable'] = list(B.UNREADABLE)
        B.UNREADABLE.clear()
        built.append(b)
    keys = sorted({l for b in built for ch in b['changes'] for l in ch['laws'] + ch['candidates']}, key=B.law_order)
    laws = {k: laws_src.meta(k) for k in keys}
    summary = {'head': pub['head'], 'acts': [b['act']['id'] for b in built], 'skipped': skipped,
               'corrections': corrections, 'problems': problems, 'laws_without_title': laws_src.missing,
               'titles_from_xml': laws_src.from_xml,
               'unreadable': {b['act']['id']: b['unreadable'][:20] for b in built if b['unreadable']}}
    if corrections:
        summary['stopped'] = 'corrections'
        return summary
    stream = io.BytesIO()
    mark = 0
    ct = pub['ct']
    parent = pub['head']
    newtags: dict[str, int] = {}
    log = []
    seq = [0]
    for b in built:
        for item in B.plan_commits([b]):
            if item['kind'] == 'start' and b['act'].get('based'):
                continue
            day = item['day']
            if item['kind'] == 'start':
                author, msg, trailers = start_message(b)
                writes = [(b, k, u) for k, u in b['versions'][0]['units'].items()]
            else:
                author, msg, trailers, writes = B.change_message(item, laws)
                trailers = trailers + dated_by(item)
            text = '\n'.join(msg).rstrip('\n') + '\n\n' + '\n'.join(trailers) + '\n'
            mark += 1
            ct += 1
            body = text.encode('utf-8')
            stream.write(f'commit refs/heads/main\nmark :{mark}\n'
                         f'author {author[0]} <{author[1]}> {B.commit_date(day, seq)[1:]}\n'
                         f'committer {B.COMMITTER[0]} <{B.COMMITTER[1]}> {ct} {pub["tz"]}\n'.encode('utf-8'))
            stream.write(b'data %d\n' % len(body) + body + b'\n')
            stream.write((f'from {parent}\n' if mark == 1 else f'from :{mark - 1}\n').encode())
            for bb, k, u in sorted(writes, key=lambda w: (w[0]['act']['id'], B.unit_order(w[1]))):
                path = f'{bb["act"]["id"]}/{B.file_name(k)}'
                if u is None:
                    stream.write(f'D {path}\n'.encode('utf-8'))
                else:
                    d = u['text'].encode('utf-8')
                    stream.write(f'M 100644 inline {path}\n'.encode('utf-8') + b'data %d\n' % len(d) + d + b'\n')
            stream.write(b'\n')
            t = f'{b["act"]["id"]}/{day}'
            if t not in pub['tags'] and t not in newtags:
                newtags[t] = mark
            if item['kind'] == 'law':
                lt = law_tag(item['law'], day, pub['tags'], newtags)
                if lt:
                    newtags[lt] = mark
            log.append({'mark': mark, 'act': b['act']['id'], 'day': day, 'kind': item['kind'],
                        'law': item.get('law'), 'author': author[0], 'files': len(writes)})
    summary.update({'commits': len(log), 'tags': len(newtags),
                    'per_act': {b['act']['id']: {'versions': len(b['versions']),
                                                 'from': b['versions'][0]['from'], 'to': b['versions'][-1]['from'],
                                                 'commits': sum(1 for e in log if e['act'] == b['act']['id']),
                                                 'not_one_law': len(b['problems'])} for b in built}})
    if args.dry_run or not log:
        return summary
    # The documentation commit, last.
    args.used_titles = laws_src.used_titles
    docs = docs_files(repo, built, laws, log, src, args)
    ct += 1
    mark += 1
    when = B.commit_date(args.docs_date, [0])[1:]
    msg = (f'Documentation and tables for {len(built)} more act{"s" if len(built) != 1 else ""}\n\n'
           f'Appended {len(log)} commits to {pub["head"][:12]}. No law text changes in this commit.\n\n'
           f'In-force: {args.docs_date}\nKind: documentation\n').encode('utf-8')
    stream.write(f'commit refs/heads/main\nmark :{mark}\n'
                 f'author {B.COMMITTER[0]} <{B.COMMITTER[1]}> {when}\n'
                 f'committer {B.COMMITTER[0]} <{B.COMMITTER[1]}> {ct} {pub["tz"]}\n'.encode('utf-8'))
    stream.write(b'data %d\n' % len(msg) + msg + b'\n')
    stream.write(f'from :{mark - 1}\n'.encode())
    for path in sorted(docs):
        d = docs[path].encode('utf-8')
        stream.write(f'M 100644 inline {path}\n'.encode('utf-8') + b'data %d\n' % len(d) + d + b'\n')
    stream.write(b'\n')
    for name in sorted(newtags):
        stream.write(f'reset refs/tags/{name}\nfrom :{newtags[name]}\n\n'.encode('utf-8'))
    out = subprocess.run(['git', 'fast-import', '--quiet', '--date-format=raw', '--done'], cwd=repo,
                         input=stream.getvalue() + b'done\n', capture_output=True)
    if out.returncode:
        raise SystemExit(f'git fast-import failed: {out.stderr.decode(errors="replace")}')
    git(repo, 'checkout', '-q', '-f', 'main')
    new = git(repo, 'rev-parse', 'main').strip()
    if subprocess.run(['git', 'merge-base', '--is-ancestor', pub['head'], new], cwd=repo).returncode:
        raise SystemExit('internal: the published head is not an ancestor of the new main')
    summary.update({'main': new, 'new_tags': sorted(newtags)})
    (HERE / '.tmp').mkdir(exist_ok=True)
    (HERE / '.tmp' / f'append-{new[:12]}.json').write_text(json.dumps({**summary, 'log': log}, indent=1), encoding='utf-8')
    return summary


def docs_files(repo: Path, built: list[dict], laws: dict, log: list[dict], src: S.Source, args) -> dict[str, str]:
    """Per-act tables for the new acts, laws.csv grown by their rows, corpus.json, and the docs in --docs."""
    out: dict[str, str] = {}
    # Every XML state each version came from, with its sha256, as data/versions.json lists the pages of P-8.6 and A-1.
    try:
        xv = json.loads(git(repo, 'show', 'main:data/xml-versions.json'))
    except SystemExit:
        xv = {'source': S.GITHUB, 'transform': S.XSL_PATH, 'transform_sha256_after_patches': src.xsl_sha,
              'acts': {}}
    for b in built:
        xv['acts'][b['act']['id']] = [
            {'from': v['from'], 'commit': v['commit'], 'file': b['act']['rel'], 'sha256': v.get('sha256', ''),
             'kind': 'consolidation' if v['snapshot'] else 'rebuilt from the provisions\' in-force days'}
            for v in b['versions']]
    xv['read_up_to'] = src.upto
    out['data/xml-versions.json'] = json.dumps(xv, indent=1, ensure_ascii=False) + '\n'
    # ACTS.md: every Act in the record and the period it covers.
    acts_rows = []
    try:
        acts_rows = [r for r in csv.DictReader(io.StringIO(git(repo, 'show', 'main:data/acts.csv')))]
    except SystemExit:
        acts_rows = [{'act': 'P-8.6', 'title': 'Personal Information Protection and Electronic Documents Act',
                      'source': 'Justice Laws Website point-in-time versions', 'from': '2003-01-01', 'to': '2025-03-04',
                      'versions': '17', 'appended': '2026-10-28'},
                     {'act': 'A-1', 'title': 'Access to Information Act',
                      'source': 'Justice Laws Website point-in-time versions', 'from': '2002-12-31', 'to': '2026-06-14',
                      'versions': '124', 'appended': '2026-10-28'}]
    for b in built:
        acts_rows = [r for r in acts_rows if r['act'] != b['act']['id']]
        acts_rows.append({'act': b['act']['id'], 'title': b['act']['short'],
                          'source': 'Justice Canada XML repository (laws-lois-xml)',
                          'from': b['versions'][0]['from'], 'to': b['versions'][-1]['from'],
                          'versions': str(len(b['versions'])), 'appended': args.docs_date})
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(acts_rows[0]), lineterminator='\n')
    w.writeheader()
    w.writerows(acts_rows)
    out['data/acts.csv'] = buf.getvalue()
    md = ['# The Acts in this record', '',
          'Each Act, the source of its versions, the first and last day a version of it applies from, and the day it was',
          'added. Nothing before the first day is in the record.', '',
          '| Act | Title | Source | From | Latest version | Versions | Added |', '| --- | --- | --- | --- | --- | ---: | --- |']
    for r in acts_rows:
        md.append(f'| [{r["act"]}]({r["act"]}/README.md) | {r["title"]} | {r["source"]} | {r["from"]} | {r["to"]} | '
                  f'{r["versions"]} | {r["appended"]} |')
    out['ACTS.md'] = '\n'.join(md) + '\n'
    # Per-act README tables, as build.write_tables makes them, but naming the XML source.
    for b in built:
        act = b['act']
        last = b['versions'][-1]
        counts: dict[str, int] = {}
        lastday: dict[str, str] = {}
        for ch in b['changes']:
            for ks in ch['groups'].values():
                for k in ks:
                    counts[k] = counts.get(k, 0) + 1
                    lastday[k] = ch['from']
        kind = 'regulations' if act.get('kind') == 'Regulation' else 'acts'
        lines = [f'# {b["title"]} ({act["id"]})', '', f'<{LAWS_LOIS}/eng/{kind}/{act["id"]}/>', '',
                 f'{len(b["versions"])} consolidated versions in Justice Canada\'s XML repository, from '
                 f'{b["versions"][0]["from"]} (the latest from {last["from"]}).', '',
                 '| Provision | File | Changes | Last changed |', '| --- | --- | ---: | --- |']
        for k in sorted(last['units'], key=B.unit_order):
            u = last['units'][k]
            lines.append(f'| {u["label"]} | [{B.file_name(k)}]({B.file_name(k)}) | {counts.get(k, 0)} | '
                         f'{lastday.get(k, "")} |')
        out[f'{act["id"]}/README.md'] = '\n'.join(lines) + '\n'
    rows = list(csv.DictReader(io.StringIO(git(repo, 'show', 'main:laws.csv'))))
    for b in built:
        for ch in b['changes']:
            for law in ch['laws']:
                lm = laws[law]
                n = len(ch['groups'].get(law, []))
                rows.append({'act': b['act']['id'], 'law': law, 'title': lm['title'], 'kind': lm['kind'],
                             'assented': lm['assented'], 'in_force': ch['from'], 'provisions': str(n),
                             'note': '' if n else 'cited only in provisions changed together with another law',
                             'source': lm['url']})
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator='\n')
    w.writeheader()
    w.writerows(rows)
    out['laws.csv'] = buf.getvalue()
    corpus = json.loads(git(repo, 'show', 'main:corpus.json'))
    for b in built:
        if b['act']['id'] not in corpus['acts']:
            corpus['acts'].append(b['act']['id'])
    corpus['name'] = 'Canadian federal law: consolidated Acts of Parliament'
    corpus['record_to'] = max([corpus.get('record_to', '')] + [b['versions'][-1]['from'] for b in built])
    corpus['checked_on'] = args.docs_date
    corpus['record_note'] = ('Checked against the official source on ' + args.docs_date + ': every version, file by '
                             'file and word for word. English text only.')
    corpus['sources'] = ['Justice Laws Website point-in-time versions (P-8.6, A-1)',
                         'Justice Canada, consolidated Acts and regulations in XML (github.com/justicecanada/laws-lois-xml)']
    corpus['path_pattern'] = corpus['path_pattern']
    out['corpus.json'] = json.dumps(corpus, indent=2, ensure_ascii=False) + '\n'
    # Titles and days of assent read from the Annual Statutes pages (statutes the XML repository does not hold), so a
    # rebuild can pass this file as --titles.
    try:
        lt = json.loads(git(repo, 'show', 'main:data/law-titles.json'))
    except SystemExit:
        lt = {}
    lt.update(getattr(args, 'used_titles', {}) or {})
    if lt:
        out['data/law-titles.json'] = json.dumps(dict(sorted(lt.items(), key=lambda kv: B.law_order(kv[0]))),
                                                 indent=1, ensure_ascii=False) + '\n'
    for p in sorted(Path(args.docs).rglob('*')) if args.docs else []:
        if p.is_file():
            out[str(p.relative_to(args.docs)).replace('\\', '/')] = p.read_text(encoding='utf-8').replace('\r\n', '\n')
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--xml', required=True)
    ap.add_argument('--upto', default='HEAD', help='the commit of the XML repository to read up to')
    ap.add_argument('--repo', required=True)
    ap.add_argument('--acts', required=True, help='comma-separated identifiers (file names without .xml)')
    ap.add_argument('--regulations', action='store_true')
    ap.add_argument('--today', required=True, help='versions in force after this day are left for a later run')
    ap.add_argument('--docs-date', required=True)
    ap.add_argument('--docs', default=None, help='a folder of documentation files to write in the docs commit')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--titles', default=None,
                    help='JSON {citation: {title, assented}} for statutes the XML repository does not hold')
    print(json.dumps(run(ap.parse_args()), indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
