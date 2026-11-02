"""Versions of consolidated federal Acts and regulations from Justice Canada's XML repository
(github.com/justicecanada/laws-lois-xml), read into the same files build.py makes from the point-in-time pages.

Each commit of that repository is a snapshot of the whole consolidation. A file's states in its history are its
consolidated versions; the root element's `lims:lastAmendedDate` is the day the version applies from (for every state of
A-1 and P-8.6 since 2021 it is the "From" day of the point-in-time version with the same text). The text goes through the
repository's own transform (xslt/LIMS2HTML.xsl, a modified copy of the one that makes the Justice Laws Website's pages,
with the four layout differences below put right) and then through build.read_version, so a version gives exactly the
files its point-in-time page gives (checked on every state of A-1 and P-8.6).

Snapshots are days or weeks apart, so two versions of an act can fall between two snapshots. Every provision in the XML
carries the day it came into force in its current form (`lims:inforce-start-date`); a provision changed between two
snapshots is dated by the latest such day in it when that day falls after the earlier snapshot's version, and the
version of that day is rebuilt from the provisions changed by then ("Dated-by" trailer). Standard library and lxml.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

from lxml import etree, html as lhtml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lawtext as B  # noqa: E402

GITHUB = 'https://github.com/justicecanada/laws-lois-xml'
LIMS = '{http://justice.gc.ca/lims}'
XSL_PATH = 'xslt/LIMS2HTML.xsl'
# The transform as published differs from the site's pages in the chapter line: 'R.S.C, 1985' and 'S.C 2000' for
# 'R.S.C., 1985' and 'S.C. 2000', and an unofficial consolidated number '(P-8.6)' after an annual chapter.
XSL_PATCHES = [
    ('<xsl:text>R.S.C, 1985, c. </xsl:text>', '<xsl:text>R.S.C., 1985, c. </xsl:text>'),
    ('<xsl:text>R.S.C </xsl:text>', '<xsl:text>R.S.C., </xsl:text>'),
    ('<xsl:text>S.C </xsl:text>', '<xsl:text>S.C. </xsl:text>'),
    ('      <xsl:apply-templates select="preceding-sibling::ConsolidatedNumber"/>\n', ''),
]
PARSE_VERSION = 'fix-1'   # change whenever fix() or html() changes
DAY = re.compile(r'(?<![0-9])([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})(?![0-9])')


def xgit(xrepo: Path, *args: str, binary: bool = False):
    out = subprocess.run(['git', *args], cwd=xrepo, capture_output=True)
    if out.returncode:
        raise SystemExit(f'git {" ".join(args)} failed: {out.stderr.decode(errors="replace")}')
    return out.stdout if binary else out.stdout.decode('utf-8')


class Source:
    def __init__(self, xrepo: Path, upto: str = 'HEAD'):
        self.repo = Path(xrepo)
        self.upto = xgit(self.repo, 'rev-parse', upto).strip()
        xsl = xgit(self.repo, 'show', f'{self.upto}:{XSL_PATH}').replace('\r\n', '\n')
        for a, b in XSL_PATCHES:
            if xsl.count(a) != 1:
                raise SystemExit(f'the transform changed: {a!r} occurs {xsl.count(a)} times')
            xsl = xsl.replace(a, b)
        self.xsl_sha = hashlib.sha256(xsl.encode('utf-8')).hexdigest()
        self.xslt = etree.XSLT(etree.fromstring(xsl.encode('utf-8')))
        # The parse cache key: the transform, the parser (lawtext.py) and the layout fixes (PARSE_VERSION).
        self.code = self.xsl_sha + hashlib.sha256((HERE / 'lawtext.py').read_bytes()).hexdigest() + PARSE_VERSION +             str(B.TOLERANT)

    def states(self, rel: str) -> list[dict]:
        """Every commit that changed the file, oldest first: commit, its day, the blob."""
        log = xgit(self.repo, 'log', '--reverse', '--format=%H %cs', self.upto, '--', rel).split('\n')
        rows = [line.split() for line in log if line]
        # One `git cat-file --batch` for every state, not one process per state.
        q = subprocess.run(['git', 'cat-file', '--batch'], cwd=self.repo, capture_output=True,
                           input=''.join(f'{h}:{rel}' + chr(10) for h, _ in rows).encode()).stdout
        out, pos = [], 0
        for h, day in rows:
            nl = q.index(bytes([10]), pos)
            head = q[pos:nl].split()
            if head[-1] == b'missing':
                pos = nl + 1
                continue
            size = int(head[2])
            raw = q[nl + 1:nl + 1 + size]
            pos = nl + 1 + size + 1
            if raw:
                out.append({'commit': h, 'day': day, 'raw': raw, 'url': f'{GITHUB}/blob/{h}/{rel}'})
        return out

    def parsed(self, raw: bytes) -> dict:
        """build.read_version of the state, kept in a local cache keyed by the state and the code that reads it."""
        import pickle
        key = hashlib.sha256(raw + self.code.encode()).hexdigest()
        path = HERE / '.tmp' / 'parsed' / key[:2] / key
        if path.exists():
            return pickle.loads(path.read_bytes())
        out = B.read_version(self.html(raw, 'x'))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(pickle.dumps(out))
        return out

    def html(self, raw: bytes, info: str) -> bytes:
        doc = etree.fromstring(raw, etree.XMLParser(huge_tree=True, resolve_entities=False, no_network=True))
        # The list of recent amending Acts some states end with is not part of the text the site prints.
        for e in doc.findall('RecentAmendments'):
            doc.remove(e)
        page = lhtml.fromstring(str(self.xslt(etree.ElementTree(doc))))
        body = page.xpath('//div[@id="docCont"]')[0]
        wrap = lhtml.fromstring('<html><body><div id="wb-cont"><section><div class="wb-txthl"></div></section></div>'
                                '</body></html>')
        top = wrap.xpath('//div[@class="wb-txthl"]')[0]
        d = lhtml.Element('div')
        d.set('class', 'info')
        d.text = info
        top.append(d)
        for c in list(body):
            top.append(c)
        fix(top)
        return lhtml.tostring(wrap, encoding='utf-8')


def cls(e) -> list[str]:
    return (e.get('class') or '').split() if isinstance(e.tag, str) else []


def fix(top):
    """Where the transform's HTML differs from the site's pages in layout only."""
    # The point-in-time pages print neither 'Related Provisions' nor 'Amendments Not in Force'.
    for d in top.xpath('./section/div[contains(concat(" ",@class," ")," ScheduleRP ") or '
                       'contains(concat(" ",@class," ")," ScheduleNIF ")]'):
        sec = d.getparent()
        sec.remove(d)
        if not [x for x in sec if isinstance(x.tag, str)]:
            sec.getparent().remove(sec)
    # Days in the opening lines are printed padded on the site (2000-04-13), not 2000-4-13.
    for p in top.xpath('.//p[@class="AssentedTo" or @class="RegistrationDate"]'):
        for e in p.iter():
            for attr in ('text', 'tail'):
                v = getattr(e, attr)
                if v and not (e is p and attr == 'tail'):
                    setattr(e, attr, DAY.sub(lambda m: f'{m[1]}-{int(m[2]):02d}-{int(m[3]):02d}', v))
    for c in top:
        # A section with subsections: the site marks its list 'Section ProvisionList'.
        if isinstance(c.tag, str) and c.tag == 'ul' and cls(c) == ['ProvisionList'] and \
                c.xpath('./li[1]//a[contains(concat(" ",@class," ")," sectionLabel ")]'):
            c.set('class', 'Section ProvisionList')
    for h in top.xpath('.//div[contains(concat(" ",@class," ")," HistoricalNote ")]'):
        # The transform closes a historical note with a full stop after its list; the site does not print it.
        for u in h:
            if u.tag == 'ul' and (u.tail or '').strip() == '.':
                u.tail = None


def root_attrs(raw: bytes) -> dict:
    head = raw[:4000].decode('utf-8', 'replace')
    m = re.search(r'<(Statute|Regulation)\b([^>]*)>', head)
    if not m:
        raise SystemExit('no Statute or Regulation root')
    attrs = dict(re.findall(r'([\w:-]+)="([^"]*)"', m.group(2)))
    attrs['_root'] = m.group(1)
    return attrs


def unit_days(raw: bytes) -> dict[str, str]:
    """{unit key: the latest lims:inforce-start-date in the provision and the headings just before it}."""
    doc = etree.fromstring(raw, etree.XMLParser(huge_tree=True, resolve_entities=False, no_network=True))
    out: dict[str, str] = {}

    def latest(els) -> str:
        days = [x.get(f'{LIMS}inforce-start-date') for e in els for x in e.iter() if isinstance(x.tag, str)]
        return max((d for d in days if d), default='')
    body = doc.find('Body')
    if body is not None:
        pending = []
        for c in body:
            if not isinstance(c.tag, str):
                continue
            if c.tag == 'Heading':
                pending.append(c)
                continue
            if c.tag == 'Section':
                label = B.clean(''.join(c.find('Label').itertext())) if c.find('Label') is not None else ''
                num = re.sub(r'\s+(to|and)\s+', r'_\1_', label)
                try:
                    key = B.section_key(num)
                except SystemExit:
                    key = None
                if key:
                    out[key] = latest(pending + [c])
                pending = []
    for s in doc.iter('Schedule'):
        lab = s.find('.//ScheduleFormHeading/Label')
        label = B.clean(''.join(lab.itertext())) if lab is not None else 'SCHEDULE'
        try:
            out.setdefault(B.schedule_key(label), latest([s]))
        except SystemExit:
            pass
    return out


def versions(src: Source, rel: str, problems: list[str]) -> list[dict]:
    """The file's consolidated versions, oldest first, with the provisions' own in-force days between snapshots."""
    snaps = []
    for st in src.states(rel):
        a = root_attrs(st['raw'])
        day = a.get('lims:lastAmendedDate') or a.get('lims:pit-date')
        if not day:
            problems.append(f'{rel} {st["commit"][:8]}: no lastAmendedDate or pit-date; state skipped')
            continue
        try:
            parsed = src.parsed(st['raw'])
        except SystemExit as exc:
            raise SystemExit(f'{rel} {st["commit"][:8]} ({day}): {exc}')
        if sorted(parsed['order'], key=B.unit_order) != parsed['order']:
            raise SystemExit(f'{rel} {day}: the file order differs from the order in the text')
        texts = {k: u['text'] for k, u in parsed['units'].items()}
        snap = {'from': day, 'url': st['url'], 'commit': st['commit'], 'units': parsed['units'], 'texts': texts,
                'sha256': hashlib.sha256(st['raw']).hexdigest(), 'raw': st['raw'], 'in_force': a.get('in-force', ''),
                'snapshot': True}
        if snaps and snaps[-1]['texts'] == texts and snaps[-1]['from'] == day:
            continue   # the same version again (a later snapshot; nothing in the English text changed)
        if snaps and day < snaps[-1]['from']:
            problems.append(f'{rel} {st["commit"][:8]}: version from {day} after one from {snaps[-1]["from"]}; held')
            continue
        if snaps and day == snaps[-1]['from']:
            # The publisher re-issued the version of the same day with a different text: the later one stands.
            problems.append(f'{rel} {day}: re-issued in {st["commit"][:8]} with a different text; the later one is used')
            snaps[-1] = snap
            continue
        snaps.append(snap)
    out = []
    for i, s in enumerate(snaps):
        if i == 0:
            out.append(s)
            continue
        prev = out[-1]
        p, c = prev['from'], s['from']
        changed = [k for k in set(prev['texts']) | set(s['texts']) if prev['texts'].get(k) != s['texts'].get(k)]
        days = unit_days(s['raw'])
        when = {}
        for k in changed:
            d = days.get(k, '') if k in s['texts'] else ''
            when[k] = d if p < d < c else c
        for d in sorted(set(when.values()) - {c}):
            units = dict(prev['units'])
            for k in changed:
                if when[k] <= d:
                    if k in s['units']:
                        units[k] = s['units'][k]
                    else:
                        units.pop(k, None)
            units = {k: units[k] for k in sorted(units, key=B.unit_order)}
            out.append({'from': d, 'url': s['url'], 'commit': s['commit'], 'units': units,
                        'texts': {k: u['text'] for k, u in units.items()}, 'snapshot': False})
            prev = out[-1]
        out.append(s)
    for v in out:
        v.pop('raw', None)
    return out
