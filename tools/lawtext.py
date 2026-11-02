"""The text and the history of Canadian federal law in git: the parts that read a consolidated version and make the
commits, shared by build.py (the point-in-time versions of the Justice Laws Website) and append.py (Justice Canada's
XML repository). Reads nothing from the network.

Every function here was in build.py until 2026-11-02; build.py now imports them from this module, unchanged.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from lxml import html as lhtml

HERE = Path(__file__).resolve().parent

ROOT = HERE.parents[1]
BASE = 'https://laws-lois.justice.gc.ca'
COMMITTER = ('Lexifina', 'canada-law@lexifina.com')
PUBLISHER = ('Justice Laws Website (Department of Justice Canada)', 'justice-laws@laws-lois.invalid')

# The acts in the record: the consolidated number (the site's identifier, also the folder) and a short name.
# 'own' are the citations of the act itself: the consolidators cite the enacting act in each section's note (and, for
# A-1, the 1980-81-82-83 Act it was revised from), and re-cite it when they rewrite a note; that is never an amendment.
ACTS = [
    {'id': 'P-8.6', 'short': 'PIPEDA', 'own': ['S.C. 2000, c. 5']},
    {'id': 'A-1', 'short': 'Access to Information Act', 'own': ['R.S.C. 1985, c. A-1', 'S.C. 1980-81-82-83, c. 111']},
]


def clean(s: str) -> str:
    """Soft hyphens go; runs of white space (spaces, line breaks, tabs, no-break and other Unicode spaces) become one
    space. Nothing else changes."""
    return re.sub(r'\s+', ' ', s.replace('­', '')).strip()


# ---------------------------------------------------------------- the act's versions

PIT = re.compile(r"<a href='(\d{8})/P1TT3xt3\.html'>From (\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})</a>")


# ---------------------------------------------------------------- reading one version

def classes(e) -> list[str]:
    return (e.get('class') or '').split() if isinstance(e.tag, str) else []


INLINE_SKIP = {'script', 'style'}
BLOCKS = {'p', 'li', 'ul', 'ol', 'dl', 'dt', 'dd', 'div', 'figure', 'figcaption', 'table', 'header', 'hgroup',
          'section', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'thead', 'tbody', 'tr', 'td', 'th', 'blockquote', 'footer',
          'aside'}


def inline_text(e) -> str:
    """All the text of an element as the page shows it, block boundaries as spaces."""
    parts = []

    def walk(x):
        if not isinstance(x.tag, str) or 'wb-invisible' in classes(x):
            return
        if x.tag == 'br' or x.tag in BLOCKS:
            parts.append(' ')
        parts.append(x.text or '')
        for c in x:
            walk(c)
            parts.append(c.tail or '')
        if x.tag in BLOCKS:
            parts.append(' ')
    parts.append(e.text or '')
    for c in e:
        walk(c)
        parts.append(c.tail or '')
    return clean(''.join(parts))


def table_lines(t, depth: int) -> list[tuple[int, str]]:
    """A table as one line per row, the cells separated by ' | ' (empty cells dropped)."""
    out = []
    for tr in t.iter('tr'):
        cells = [inline_text(td) for td in tr if isinstance(td.tag, str) and td.tag in ('td', 'th')]
        row = ' | '.join(c for c in cells if c)
        if row:
            out.append((depth, row))
    return out


def marginal_text(e) -> str:
    def walk(x):
        out = []
        if isinstance(x.tag, str) and 'wb-invisible' in classes(x):
            return ''
        out.append(x.text or '')
        for c in x:
            out.append(walk(c))
            out.append(c.tail or '')
        return ''.join(out)
    return clean(walk(e))


def flow(e, depth: int) -> list[tuple[int, str]]:
    """A block of a provision as (depth, text) lines. A list (ul) or definition list (dl) puts its items one level
    deeper; paragraphs (p) and other leaf blocks are one line each; a marginal note inside a section is a line of its
    own, 'Marginal note: ...'; definition terms (dt, an index of the term the definition repeats) are skipped; tables
    are one line per row."""
    out: list[tuple[int, str]] = []
    buf: list[str] = []

    def flush(d):
        t = clean(''.join(buf))
        buf.clear()
        if t:
            out.append((d, t))

    def walk(x, d):
        if not isinstance(x.tag, str) or x.tag in INLINE_SKIP:
            return
        cls = classes(x)
        if x.tag == 'dt':
            # A formula's term ('A', 'B') is not an index of a defined term: the definition does not repeat it.
            if TOLERANT and 'FormulaTerm' in cls:
                t = clean(inline_text_keep(x))
                if t:
                    out.append((d, t))
            return
        if x.tag == 'table':
            out.extend(table_lines(x, d))
            return
        if x.tag == 'p' and 'MarginalNote' in cls:
            out.append((d, f'Marginal note: {marginal_text(x)}'))
            return
        if x.tag in ('ul', 'ol', 'dl'):
            for c in x:
                if isinstance(c.tag, str):
                    walk(c, d + 1)
            return
        if x.tag in BLOCKS:
            flush(d)
            buf.append(x.text or '')
            for c in x:
                if isinstance(c.tag, str) and (c.tag in BLOCKS or c.tag == 'br'):
                    flush(d)
                    if c.tag != 'br':
                        walk(c, d)
                else:
                    buf.append(inline_text_keep(c))
                buf.append(c.tail or '')
            flush(d)
            return
        buf.append(inline_text_keep(x))

    walk(e, depth)
    flush(depth)    # an inline element on its own ('[Repealed, 2005, c. 22, s. 37]' as a schedule's only content)
    return out


def inline_text_keep(x) -> str:
    """An inline element's text, unnormalised (the caller cleans the whole line). Text only for screen readers
    (class wb-invisible: 'Footnote', 'Return to footnote') is left out, as the page does not show it."""
    if not isinstance(x.tag, str) or 'wb-invisible' in classes(x):
        return ''
    parts = [x.text or '']
    for c in x:
        parts.append(inline_text_keep(c))
        parts.append(c.tail or '')
    return ''.join(parts)


def render(lines: list[tuple[int, str]]) -> str:
    out = []
    for d, t in lines:
        if d < 0:
            out.append('#' * (-d) + ' ' + t)
        elif d == 0:
            out.append(t)
        else:
            out.append('  ' * (d - 1) + '- ' + t)
    return '\n\n'.join(out) + '\n'


HEADING_LEVEL = {'h2': 2, 'h3': 3, 'h4': 4, 'h5': 5, 'h6': 6}


def heading_text(h) -> str:
    """A heading's parts (its label, 'PART 1', and its title, which the page shows on lines of their own) joined by a
    space."""
    parts = [h.text or '']
    for c in h:
        if isinstance(c.tag, str) and 'wb-invisible' not in classes(c):
            parts.append(inline_text_keep(c))
        parts.append(c.tail or '')
    return clean(' '.join(p for p in parts if p.strip()))


def section_key(num: str) -> str:
    """'4.01' -> 's-004.01': the section number, its whole part padded to three digits so files sort in order."""
    m = re.fullmatch(r'(\d+)((?:\.\d+)*)(?:_(to|and)_(\d+)((?:\.\d+)*))?', num)
    if not m:
        raise SystemExit(f'unexpected section number {num!r}')
    key = f's-{int(m.group(1)):03d}{m.group(2)}'
    if m.group(3):   # a group of sections printed as one ('52 to 57 [Amendments]')
        key += f'-{m.group(3)}-{int(m.group(4)):03d}{m.group(5)}'
    return key


def schedule_key(label: str) -> str:
    """'SCHEDULE I' -> 'schedule-i', 'SCHEDULE 1' -> 'schedule-1', 'SCHEDULE' -> 'schedule'."""
    m = re.fullmatch(r'SCHEDULE(?: ([0-9A-Z.]+))?', clean(label).upper())
    if not m and TOLERANT:
        # 'SCHEDULE TO PART XX.1' -> 'schedule-to-part-xx.1'; 'FORM 1' -> 'form-1' (other acts and regulations)
        s = re.sub(r'[^a-z0-9.]+', '-', clean(label).lower()).strip('-')
        if s:
            return s if s.startswith('schedule') else f'schedule-{s}'
    if not m:
        raise SystemExit(f'unexpected schedule label {label!r}')
    return 'schedule' + (f'-{m.group(1).lower()}' if m.group(1) else '')


def history_lines(e) -> list[tuple[int, str]]:
    """A historical note: a line 'History:' and one list item per citation, as the page lists them."""
    items = [inline_text(li) for li in e.iter('li') if 'HistoricalNoteSubItem' in classes(li)]
    items = [i for i in items if i]
    return [(0, 'History:')] + [(1, i) for i in items] if items else []


def read_version(raw: bytes) -> dict:
    """One version as units in document order: the opening (title, chapter, assent, long title, enacting words), each
    section with the headings that begin with it, its marginal note and its historical note, and each schedule."""
    doc = lhtml.fromstring(raw.decode('utf-8'))
    cont = doc.get_element_by_id('wb-cont')
    tops = cont.xpath('./section/div[contains(concat(" ", @class, " "), " wb-txthl ")]')
    if len(tops) != 1:
        raise SystemExit('page layout changed: no single wb-txthl block')
    top = tops[0]
    units: dict[str, dict] = {}
    order: list[str] = []
    pending: list[tuple[int, str]] = []
    info = ''
    cur: dict | None = None

    def unit(key: str, label: str, kind: str) -> dict:
        if key in units:
            raise SystemExit(f'duplicate unit {key}')
        u = {'key': key, 'label': label, 'kind': kind, 'lines': [], 'history': []}
        units[key] = u
        order.append(key)
        return u

    def opening() -> dict:
        return units['intro'] if 'intro' in units else unit('intro', 'Title and long title', 'intro')

    for c in top:
        if not isinstance(c.tag, str):
            continue
        cls = classes(c)
        if c.tag == 'div' and 'info' in cls:
            info = clean(c.text_content())
            continue
        if c.tag == 'section' and 'intro' in cls:
            u = opening()
            u['lines'].extend(flow(c, 0))
            continue
        if c.tag == 'div' and 'Enacts' in cls:
            opening()['lines'].extend(flow(c, 0))
            continue
        if c.tag in HEADING_LEVEL:
            pending.append((-HEADING_LEVEL[c.tag], heading_text(c)))
            continue
        if c.tag == 'p' and ('MarginalNote' in cls or 'MarginalNoteDefinedTerm' in cls):
            pending.append((0, f'Marginal note: {marginal_text(c)}'))
            continue
        if 'Section' in cls:
            labels = c.xpath('.//a[contains(concat(" ", @class, " "), " sectionLabel ")]/@id')
            if TOLERANT and not labels and c.tag == 'div' and cur is not None and not pending:
                cur['lines'].extend(flow(c, 0))     # a formula block continuing the section before it
                continue
            if TOLERANT and labels and labels[0].startswith('s-') and not re.match(r'[0-9]', labels[0][2:]):
                pending.extend(flow(c, 0))          # 'Preamble' printed as a section: it goes with the next section
                continue
            if not labels or not labels[0].startswith('s-'):
                raise SystemExit(f'section without a label: {inline_text(c)[:80]}')
            num = labels[0][2:]
            cur = unit(section_key(num), f's. {num}' if '_' not in num else f'ss. {num.replace("_", " ")}', 'section')
            cur['lines'] = pending[:] + flow(c, -1 if c.tag == 'ul' else 0)
            pending.clear()
            continue
        if c.tag == 'div' and 'HistoricalNote' in cls:
            if cur is None or pending:
                raise SystemExit('historical note outside a section')
            cur['history'] = history_lines(c)
            continue
        if TOLERANT and c.tag == 'section' and not c.xpath('./div[contains(concat(" ", @class, " "), " Schedule ")]'):
            opening()['lines'].extend(pending + flow(c, 0))    # an act's preamble ('section.order')
            pending.clear()
            continue
        if c.tag == 'section':
            for s in c:
                if not isinstance(s.tag, str):
                    continue
                if 'Schedule' not in classes(s):
                    raise SystemExit(f'unexpected element in a schedule section: {s.tag} {classes(s)}')
                lab = s.xpath('.//span[contains(concat(" ", @class, " "), " scheduleLabel ")]')
                label = clean(lab[0].text_content()) if lab else 'SCHEDULE'
                u = unit(schedule_key(label), re.sub(r'^SCHEDULE', 'Schedule', label), 'schedule')
                u['lines'] = pending[:]
                pending.clear()
                for x in s:
                    if not isinstance(x.tag, str):
                        continue
                    if x.tag == 'div' and 'HistoricalNote' in classes(x):
                        u['history'] = history_lines(x)
                    elif x.tag == 'header':
                        for h in x:
                            if isinstance(h.tag, str) and h.tag in HEADING_LEVEL:
                                u['lines'].append((-HEADING_LEVEL[h.tag], heading_text(h)))
                    elif x.tag in HEADING_LEVEL:
                        u['lines'].append((-HEADING_LEVEL[x.tag], heading_text(x)))
                    else:
                        u['lines'].extend(flow(x, 0))
            cur = None
            continue
        # Anything else (a list of paragraphs or definitions after a section's opening words, words continuing a
        # section) belongs to the section before it.
        if TOLERANT and pending and c.tag == 'p':
            pending.extend(flow(c, 0))              # the paragraphs of a preamble printed before a section
            continue
        if cur is None or pending:
            raise SystemExit(f'unexpected element outside a section: {c.tag} {cls}')
        cur['lines'].extend(flow(c, 0))
    if pending:
        raise SystemExit('headings with no section after them')
    for k in order:
        u = units[k]
        u['text'] = render(u['lines'] + u['history'])
        u['cites'] = cites_of(u)
    return {'units': units, 'order': order, 'info': info}


# ---------------------------------------------------------------- citations

SUPP = r'(?: \((?:\d+(?:st|nd|rd|th)) Supp\.\))?'


TOLERANT = False      # append.py sets it: notes of the other acts use forms the two original acts never print
UNREADABLE: list[str] = []


def parse_citation(item: str) -> list[tuple[str, str]]:
    try:
        return parse_citation_strict(item)
    except SystemExit:
        if not TOLERANT:
            raise
    out = []
    s = clean(item).replace('–', '-').rstrip('.')
    if s.startswith('['):     # '[NOTE: Application provisions are not included ...]': not a citation
        return out
    s = re.sub(r'\bc\.(?=[0-9A-Z])', 'c. ', s)          # '2012, c.1, s. 160': a missing space
    for part in s.split('; '):
        try:
            out += parse_citation_strict(part)
            continue
        except SystemExit:
            pass
        # 'c. 42 (4th Supp.), s. 7': a chapter of a supplement, which only the Revised Statutes of 1985 have.
        m = re.fullmatch(r'c\. (\d+) ?\((\d+(?:st|nd|rd|th)) Supp\.\)(?:, (.+))?', part)
        if m:
            out.append((f'R.S.C. 1985, c. {m.group(1)} ({m.group(2)} Supp.)', m.group(3) or ''))
            continue
        # The Revised Statutes of 1970, cited 'R.S., c. B-2, s. 1', 'R.S., c. 2(1st Supp.)', 'R.S.C. 1970, c. Q-1'.
        m = re.fullmatch(r'R\.S\.(?:C\.)?,? (?:1970, )?c\. ([0-9A-Z][0-9A-Za-z.-]*?) ?(\(\d+(?:st|nd|rd|th) Supp\.\))?'
                         r'(?:, (.+))?', part.rstrip('.'))
        if m:
            out.append((f'R.S.C. 1970, c. {m.group(1)}{" " + m.group(2) if m.group(2) else ""}', m.group(3) or ''))
            continue
        UNREADABLE.append(part)
    return out


def parse_citation_strict(item: str) -> list[tuple[str, str]]:
    """A citation in a historical note as (law, provision) pairs. 'R.S., 1985, c. A-1, s. 2' -> [('R.S.C. 1985, c. A-1',
    's. 2')]; '2015, c. 32, s. 3, c. 36, s. 164' -> [('S.C. 2015, c. 32', 's. 3'), ('S.C. 2015, c. 36', 's. 164')];
    'SOR/91-234, 235' -> [('SOR/91-234', ''), ('SOR/91-235', '')]."""
    s = clean(item).replace('–', '-').rstrip('.')
    m = re.fullmatch(r'(SOR|SI)/(\d{2,4})-(\d+)((?:, \d+)*)(?:, (s\. .+))?', s)
    if m:
        regs = [m.group(3)] + re.findall(r'\d+', m.group(4) or '')
        return [(f'{m.group(1)}/{m.group(2)}-{n}', m.group(5) or '') for n in regs]
    m = re.fullmatch(r'(R\.S\., )?(\d{4}(?:-\d{2})*), (c\. .+)', s)
    if not m:
        raise SystemExit(f'unreadable citation {item!r}')
    series = 'R.S.C.' if m.group(1) else 'S.C.'
    out = []
    for part in re.split(r', (?=c\. )', m.group(3)):
        pm = re.fullmatch(r'c\. ([0-9A-Z][0-9A-Za-z.-]*' + SUPP + r')(?:, (.+))?', part)
        if not pm:
            raise SystemExit(f'unreadable citation part {part!r} in {item!r}')
        out.append((f'{series} {m.group(2)}, c. {pm.group(1)}', pm.group(2) or ''))
    return out


def cites_of(u: dict) -> set[tuple[str, str]]:
    """Every (law, provision) pair in a unit's historical note, and in any '[Repealed, ...]' text."""
    pairs = set()
    for d, t in u['history']:
        if d == 1:
            pairs.update(parse_citation(t))
    for d, t in u['lines']:
        for m in re.finditer(r'\[Repealed, ((?:R\.S\., )?\d{4}[^\]]*|SOR/[^\]]*)\]', t):
            try:
                pairs.update(parse_citation(m.group(1)))
            except SystemExit:
                pass
    return pairs


def law_order(k: str) -> tuple:
    """Laws in order: the Revised Statutes and their supplements, then statutes by year and chapter, then
    regulations by year and number."""
    m = re.fullmatch(r'(R\.S\.C\.|S\.C\.) (\d{4})(?:-\d{2})*, c\. ([0-9]*)([^ ]*)(.*)', k)
    if m:
        return (0, int(m.group(2)), int(m.group(3) or 0), m.group(4) + m.group(5))
    m = re.fullmatch(r'(SOR|SI)/(\d{2,4})-(\d+)', k)
    y = int(m.group(2))
    return (1, y + (1900 if y >= 50 and y < 100 else 2000 if y < 50 else 0), int(m.group(3)), m.group(1))


def law_slug(k: str) -> str:
    """'S.C. 2019, c. 18' -> 'sc-2019-c18'; 'R.S.C. 1985, c. 1 (4th Supp.)' -> 'rsc-1985-c1-4th-supp';
    'SOR/2006-123' -> 'sor-2006-123'."""
    s = k.lower().replace('r.s.c.', 'rsc').replace('s.c.', 'sc').replace('c. ', 'c').replace('supp.', 'supp')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


# ---------------------------------------------------------------- one act: versions, changes, causes

def unit_order(key: str) -> tuple:
    if key == 'intro':
        return (0, 0, ())
    m = re.fullmatch(r's-(\d+)((?:\.\d+)*)(?:-(?:to|and)-.*)?', key)
    if m:
        return (1, int(m.group(1)), tuple(m.group(2).split('.')[1:]))
    if key.startswith('schedule'):
        rest = key[len('schedule'):].lstrip('-')
        roman = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10}
        if rest.isdigit() or rest in roman or not rest or re.fullmatch(r'[0-9a-z.]+', rest):
            n = int(rest) if rest.isdigit() else roman.get(rest, 0)
            return (2, n, (rest,))
        return (2, 1000 + other_rank(rest), natural(rest))
    return (3, 0, (key,))


ROMAN = re.compile(r'(?=[ivxlcdm])m*(c[md]|d?c{0,3})(x[cl]|l?x{0,3})(i[xv]|v?i{0,3})')


def other_rank(rest: str) -> int:
    """Schedules with other labels (other acts and regulations): those to a Part, then the rest, then forms."""
    return 0 if rest.startswith('to-part') else 2 if rest.startswith('form') else 1


def natural(rest: str) -> tuple:
    """'form-5.0031' -> words in order, numbers by value (decimal parts as written), Roman numerals by value."""
    vals = {'i': 1, 'v': 5, 'x': 10, 'l': 50, 'c': 100, 'd': 500, 'm': 1000}
    out = []
    for t in re.findall(r'[0-9]+(?:\.[0-9]+)*|[a-z]+', rest):
        if t[0].isdigit():
            whole, _, frac = t.partition('.')
            out.append((0, int(whole), frac))
        elif ROMAN.fullmatch(t):
            n = 0
            for a, b in zip(t, t[1:] + ' '):
                n += -vals[a] if b != ' ' and vals[b] > vals[a] else vals[a]
            out.append((0, n, ''))
        else:
            out.append((1, 0, t))
    return tuple(out)


def file_name(key: str) -> str:
    return f'{key}.md'


def analyse(act: dict, versions: list[dict]) -> dict:
    """The changes between consecutive versions (each with 'from', 'url' and parsed 'units'), and their causes."""
    changes = []
    problems = []
    own = set(act['own'])
    seen: dict[str, set[str]] = {}   # every text each file has had in the versions before the previous one
    for i, (prev, cur) in enumerate(zip(versions, versions[1:])):
        if i:
            for k, u in versions[i - 1]['units'].items():
                seen.setdefault(k, set()).add(u['text'])
        allkeys = sorted(set(prev['units']) | set(cur['units']), key=unit_order)
        changed = [k for k in allkeys if (prev['units'].get(k) or {}).get('text') != (cur['units'].get(k) or {}).get('text')]
        new: dict[str, set[str]] = {}
        added: dict[str, list[str]] = {}
        for k in changed:
            p, c = prev['units'].get(k), cur['units'].get(k)
            pc = p['cites'] if p else set()
            cc = c['cites'] if c else set()
            new[k] = {law for law, _ in cc - pc}
            if new[k] - own:
                new[k] -= own
            added[k] = [t for d, t in (c['history'] if c else []) if d == 1 and t not in
                        {t2 for d2, t2 in (p['history'] if p else []) if d2 == 1}]
        L = sorted({law for k in changed for law in new[k]}, key=law_order)
        cause: dict[str, str] = {}
        why: dict[str, str] = {}
        for k in changed:
            c = cur['units'].get(k)
            if len(new[k]) == 1:
                cause[k], why[k] = next(iter(new[k])), 'citation'
            elif len(new[k]) > 1:
                cause[k], why[k] = 'candidates', 'the note gains citations of two or more laws'
            elif len(L) == 1:
                cause[k], why[k] = L[0], 'date only'
            elif L:
                cause[k], why[k] = 'candidates', 'no new citation in its note; two or more laws are new that day'
            else:
                cause[k], why[k] = 'unexplained', 'no new citation in its note or anywhere in the version'
            if c and c['text'] in seen.get(k, ()) and why[k] != 'citation':
                why[k] += '; the text equals an earlier version of it'
        for k in changed:
            if cause[k] in ('unexplained', 'candidates'):
                problems.append(f'{cur["from"]} {k} ({why[k]})')
        groups: dict[str, list[str]] = {}
        for k in changed:
            groups.setdefault(cause[k], []).append(k)
        cand = sorted({law for k in groups.get('candidates', []) for law in (new[k] or set(L))}, key=law_order)
        changes.append({'from': cur['from'], 'url': cur['url'], 'laws': L, 'groups': groups, 'why': why,
                        'new': new, 'added': added, 'candidates': cand, 'prev': prev, 'cur': cur})
    first = versions[0]['units']['intro']['text']
    title = first.split('\n\n')[0].lstrip('# ').strip()
    return {'act': act, 'versions': versions, 'changes': changes, 'problems': problems, 'title': title}


# ---------------------------------------------------------------- the git repository

def git(repo: Path, *args: str, env: dict | None = None, input: str | None = None) -> str:
    out = subprocess.run(['git', *args], cwd=repo, capture_output=True, text=True, encoding='utf-8', env=env, input=input)
    if out.returncode:
        raise SystemExit(f'git {" ".join(args)} failed: {out.stderr}')
    return out.stdout


def nth_sunday(year: int, month: int, n: int) -> dt.date:
    d = dt.date(year, month, 1)
    d += dt.timedelta(days=(6 - d.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)


def last_sunday(year: int, month: int) -> dt.date:
    d = (dt.date(year, month + 1, 1) if month < 12 else dt.date(year + 1, 1, 1)) - dt.timedelta(days=1)
    return d - dt.timedelta(days=(d.weekday() + 1) % 7)


def ottawa_offset(day: dt.date) -> int:
    """Hours from UTC at noon on a day in Ottawa (written out, because this machine has no tz database). Eastern
    Standard Time, UTC-5; daylight time, UTC-4, from the second Sunday in March to the first Sunday in November since
    2007, and from the first Sunday in April to the last Sunday in October from 1987 to 2006. Clocks change at 2:00, so
    noon on the first day is daylight time and noon on the last day is standard time."""
    y = day.year
    if y >= 2007:
        start, end = nth_sunday(y, 3, 2), nth_sunday(y, 11, 1)
    elif y >= 1987:
        start, end = nth_sunday(y, 4, 1), last_sunday(y, 10)
    else:
        start, end = last_sunday(y, 4), last_sunday(y, 10)
    return -4 if start <= day < end else -5


def commit_date(day: str, seq: list[int]) -> str:
    """Noon in Ottawa on the day. Git cannot record a time before 1970, so a day before then would be dated
    1 January 1970 (UTC), one second apart in order; the real day is in the In-force trailer."""
    d = dt.date.fromisoformat(day)
    if d.year < 1970:
        seq[0] += 1
        return f'@{seq[0]} +0000'
    off = ottawa_offset(d)
    stamp = int(dt.datetime(d.year, d.month, d.day, 12, tzinfo=dt.timezone(dt.timedelta(hours=off))).timestamp())
    return f'@{stamp} -0{-off}00'


def author_of(law: str) -> tuple[str, str]:
    return law, f'{law_slug(law)}@laws-lois.invalid'


def tag_of(law: str) -> str:
    """'S.C. 2019, c. 18' -> 'sc/2019-c18'; 'SOR/2006-123' -> 'sor/2006-123'."""
    s = law_slug(law)
    head, _, rest = s.partition('-')
    return f'{head}/{rest}'


def change_kind(prev: dict | None, cur: dict | None) -> str:
    if prev is None:
        return 'Added'
    if cur is None:
        return 'Removed from the consolidation'
    if cur['text'].split('\n\n')[-1:] and re.search(r'\[Repealed', cur['text']) and not re.search(r'\[Repealed', prev['text']):
        return 'Repealed'
    return 'Amended'


def write_unit(repo: Path, slug: str, key: str, unit: dict | None):
    path = repo / slug / file_name(key)
    if unit is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(unit['text'], encoding='utf-8', newline='\n')


def plan_commits(built: list[dict]) -> list[dict]:
    """Every commit, in the order the changes took effect. On a day: the first version of each act; then one commit
    per amending law (laws in order of citation), covering every act of the record it changed that day; then changes
    with two candidate laws, and changes nothing explains, per act."""
    items: dict[tuple, dict] = {}
    for ai, b in enumerate(built):
        day0 = b['versions'][0]['from']
        items[(day0, 0, (ai,), '')] = {'kind': 'start', 'day': day0, 'parts': [(b, None)]}
        for ch in b['changes']:
            laws = [l for l in ch['groups'] if l not in ('unexplained', 'candidates')]
            for law in laws:
                key = (ch['from'], 1, law_order(law), law)
                items.setdefault(key, {'kind': 'law', 'day': ch['from'], 'law': law, 'parts': []})['parts'].append((b, ch))
            if 'candidates' in ch['groups']:
                items[(ch['from'], 2, (ai,), '')] = {'kind': 'candidates', 'day': ch['from'], 'parts': [(b, ch)]}
            if 'unexplained' in ch['groups']:
                items[(ch['from'], 3, (ai,), '')] = {'kind': 'unexplained', 'day': ch['from'], 'parts': [(b, ch)]}
            if not ch['groups']:
                items[(ch['from'], 4, (ai,), '')] = {'kind': 'nochange', 'day': ch['from'], 'parts': [(b, ch)]}
    return [items[k] for k in sorted(items)]


def provision_label(b: dict, u: dict) -> str:
    return f'{b["act"]["id"]} {u["label"]}'


def short_list(names: list[str], limit: int = 6) -> str:
    return ', '.join(names) if len(names) <= limit else f'{", ".join(names[:limit])} and {len(names) - limit} more'


def subject_for(parts: list[tuple[dict, list[str]]], tail: str) -> str:
    """'A-1: s. 2, s. 3 (S.C. 2019, c. 18)', shortened to counts when longer than 72 characters."""
    def full():
        return '; '.join(f'{b["act"]["id"]}: {", ".join(labels)}' for b, labels in parts)

    def counts():
        return '; '.join(f'{b["act"]["id"]}: {len(labels)} provision{"s" if len(labels) != 1 else ""}' for b, labels in parts)
    s = f'{full()} ({tail})'
    if len(s) <= 72:
        return s
    s = f'{counts()} ({tail})'
    return s if len(s) <= 72 else counts()


def change_message(item: dict, laws: dict) -> tuple[tuple[str, str], list[str], list[str], list[tuple[dict, str, dict | None]]]:
    """The author, message lines, trailers and the (act, unit key, new unit) writes of one commit."""
    kind = item['kind']
    day = item['day']
    writes = []
    listing = []
    affecting = []
    subject_parts = []
    citations = []
    evidence = {}
    consolidated = []
    for b, ch in item['parts']:
        group = item.get('law') if kind == 'law' else kind
        keys = sorted(ch['groups'].get(group, []), key=unit_order) if kind != 'nochange' else []
        consolidated.append(ch['url'])
        by_kind: dict[str, list[str]] = {}
        labels = []
        for k in keys:
            p, c = ch['prev']['units'].get(k), ch['cur']['units'].get(k)
            u = c or p
            labels.append(u['label'])
            by_kind.setdefault(change_kind(p, c), []).append(u['label'])
            affecting.append(provision_label(b, u))
            writes.append((b, k, c))
            if kind == 'law':
                citations += [t for t in ch['added'][k] if any(l == item['law'] for l, _ in parse_citation(t))]
                w = ch['why'][k]
                evidence.setdefault(w, []).append(provision_label(b, u))
            else:
                evidence.setdefault(ch['why'][k], []).append(provision_label(b, u))
        subject_parts.append((b, labels))
        for name in ('Added', 'Amended', 'Repealed', 'Removed from the consolidation'):
            if name in by_kind:
                listing.append(f'{b["act"]["id"]} ({b["act"]["short"]}), {name.lower()}: {", ".join(by_kind[name])}')
    trailers = []
    if kind == 'law':
        law = item['law']
        lm = laws[law]
        author = author_of(law)
        msg = [subject_for(subject_parts, law), '']
        if lm['title']:
            msg += [lm['title'], '']
        msg += listing + ['']
        if 'citation' in evidence:
            trailers.append('Evidence: citation of this law added to the historical note of the provision in the '
                            'version from this day')
        for w, provs in sorted(evidence.items()):
            if w == 'date only' or w.startswith('date only;'):
                msg += ['These provisions changed on this day, but their historical notes cite no new law. This law is',
                        'the only one whose citation is new in this version, so the change is credited to it by date',
                        f'only: {short_list(provs, 20)}.', '']
                for p in provs:
                    trailers.append(f'Evidence: date only for {p}')
            if 'equals an earlier version' in w:
                msg += ['The new text equals an earlier version of the provision (a reprint of older text): '
                        f'{short_list(provs, 20)}.', '']
        trailers.append(f'Kind: {lm["kind"]}')
        if lm['assented']:
            trailers.append(f'Enacted: {lm["assented"]}')
            if day < lm['assented']:
                msg += [f'Note: the version with this change applies from {day}, before the law received Royal Assent',
                        f'({lm["assented"]}). The law reaches back; the day is kept as the source gives it.', '']
                trailers.append('Date-note: in force before Royal Assent (retroactive)')
        trailers.append(f'In-force: {day}')
        for c in citations:
            trailers.append(f'Citation: {c}')
        if lm['url']:
            trailers.append(f'Source: {lm["url"]}')
    elif kind == 'candidates':
        author = PUBLISHER
        names = [c for b, ch in item['parts'] for c in ch['candidates']]
        msg = [subject_for(subject_parts, 'two laws, credited to neither'), '',
               f'These provisions changed on this day, and the laws that may have changed them are {", ".join(names)}.',
               'The historical notes do not say which law made which change, so the change is credited to neither.',
               ''] + listing + ['']
        for w, provs in sorted(evidence.items()):
            for p in provs:
                trailers.append(f'Evidence: {w} ({p})')
        trailers.append(f'In-force: {day}')
        trailers += [f'Candidate: {n}' for n in names]
    elif kind == 'unexplained':
        author = PUBLISHER
        msg = [subject_for(subject_parts, 'no amending law cited'), '',
               'The consolidated text of these provisions changed on this day, but no historical note in the version',
               'from this day cites a new law. The change is credited to no law: it is the publisher\'s.', ''] + listing + ['']
        for w, provs in sorted(evidence.items()):
            if 'equals an earlier version' in w:
                msg += ['The new text equals an earlier version of the provision (a reprint of older text): '
                        f'{short_list(provs, 20)}.', '']
        trailers.append(f'In-force: {day}')
        trailers.append('Kind: editorial (publisher)')
    else:   # nochange
        author = PUBLISHER
        b = item['parts'][0][0]
        msg = [f'{b["act"]["id"]}: new version, no change in the English text', '',
               f'The Justice Laws Website starts a new version of the {b["act"]["short"]} on this day, but its English',
               'text, including the historical notes, is the same as the version before. (The change may be in the',
               'French text only, or in material outside the text.) This commit changes no file; it marks the day.', '']
        trailers.append(f'In-force: {day}')
        trailers.append('Kind: version without a change in the English text (publisher)')
    for a in affecting:
        trailers.append(f'Affecting: {a}')
    for u in consolidated:
        trailers.append(f'Consolidated: {u}')
    return author, msg, trailers, writes


def start_message(b: dict) -> tuple[tuple[str, str], list[str], list[str]]:
    v = b['versions'][0]
    day = v['from']
    msg = [f'{b["act"]["id"]}: {b["title"]}, as consolidated on {day}', '',
           f'The text in the first point-in-time version the Justice Laws Website publishes, in force from {day}. It is',
           'the act as enacted and amended up to then; the site has no earlier versions, so the lines of this commit',
           'are credited to the publisher, not to a law. The historical note of each section lists the laws that made it.',
           '']
    trailers = [f'In-force: {day}', 'Kind: first published version (publisher)', f'Consolidated: {v["url"]}']
    return PUBLISHER, msg, trailers


def write_tables(repo: Path, built: list[dict], laws: dict):
    out = []
    for b in built:
        for ch in b['changes']:
            for law in ch['laws']:
                lm = laws[law]
                n = len(ch['groups'].get(law, []))
                out.append({'act': b['act']['id'], 'law': law, 'title': lm['title'], 'kind': lm['kind'],
                            'assented': lm['assented'], 'in_force': ch['from'], 'provisions': n,
                            'note': '' if n else 'cited only in provisions changed together with another law',
                            'source': lm['url']})
    out.sort(key=lambda r: (r['in_force'], r['act'], law_order(r['law'])))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(out[0]), lineterminator='\n')
    w.writeheader()
    w.writerows(out)
    (repo / 'laws.csv').write_text(buf.getvalue(), encoding='utf-8', newline='\n')

    for b in built:
        act = b['act']
        last = b['versions'][-1]
        counts: dict[str, int] = {}
        lastday: dict[str, str] = {}
        for ch in b['changes']:
            for keys in ch['groups'].values():
                for k in keys:
                    counts[k] = counts.get(k, 0) + 1
                    lastday[k] = ch['from']
        out2 = [f'# {b["title"]} ({act["id"]})', '',
                f'<{BASE}/eng/acts/{act["id"]}/>', '',
                f'{len(b["versions"])} point-in-time versions on the Justice Laws Website, from {b["versions"][0]["from"]} '
                f'(the latest from {last["from"]}).', '',
                '| Provision | File | Changes | Last changed |', '| --- | --- | ---: | --- |']
        for k in sorted(last['units'], key=unit_order):
            u = last['units'][k]
            out2.append(f'| {u["label"]} | [{file_name(k)}]({file_name(k)}) | {counts.get(k, 0)} | {lastday.get(k, "")} |')
        (repo / act['id'] / 'README.md').write_text('\n'.join(out2) + '\n', encoding='utf-8', newline='\n')
