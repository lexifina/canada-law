"""Writes data/versions.json, corpus.json and REPRODUCE.md into the Canadian law repository, from the facts of the build
that made it. Called by build.py; kept apart so the record of how the repository was made reads as one document.

The results of the checks (check_repo.py, test_repo.py and the rebuild that compares hashes) are read from
verification.json next to this file, which check_repo.py, `test_repo.py --record` and `build.py --verify-rebuild` write.
They describe the build before the one that writes this file, from the same data; a rebuild with the same data and the
same verification.json gives the same hashes."""
from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent

DEFAULT_REACH = {
    'rule': 'presumption against retrospectivity; immediate application to procedure',
    'meaning': 'an enactment is presumed not to apply to facts completed before it came into force, or to interfere '
               'with vested rights, unless Parliament says so expressly or by necessary implication; procedural '
               'provisions apply immediately to pending matters; a repeal does not affect rights acquired or '
               'proceedings begun under the repealed enactment; in criminal law, no one may be found guilty of an act '
               'that was not an offence when committed, and a person found guilty is entitled to the lesser '
               'punishment where it was varied between the offence and sentencing',
    'authority': 'Interpretation Act, R.S.C. 1985, c. I-21, s. 43 (effect of repeal) and s. 44 (repeal and '
                 'substitution); Canadian Charter of Rights and Freedoms, s. 11(g) and 11(i); R. v. Dineley, 2012 SCC '
                 '58, [2012] 3 S.C.R. 272; Tran v. Canada (Public Safety and Emergency Preparedness), 2017 SCC 50, '
                 '[2017] 2 S.C.R. 289',
    'decided_here': False,
}


def write_manifest(repo: Path, built: list[dict], laws: dict, today: str):
    """Every source page the text comes from, with its sha256, so a rebuild can show it read the same bytes; and
    corpus.json, which describes the corpus for tools that read several of Lexifina's law repositories."""
    out = {'built': today, 'source': 'https://laws-lois.justice.gc.ca', 'acts': [{
        'id': b['act']['id'], 'title': b['title'], 'short': b['act']['short'],
        'versions': [{'from': v['from'], 'to': v['to'], 'laws': next((ch['laws'] for ch in b['changes']
                                                                       if ch['from'] == v['from']), []),
                      'html': v['url'], 'sha256': v['sha256']} for v in b['versions']],
    } for b in built], 'laws': [laws[k] for k in laws]}
    (repo / 'data').mkdir(exist_ok=True)
    (repo / 'data' / 'versions.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8',
                                                 newline='\n')
    first = min(b['versions'][0]['from'] for b in built)
    last = max(v['from'] for b in built for v in b['versions'] if v['from'] <= today)
    corpus = {
        'corpus': 'ca/federal/acts',
        'name': 'Canadian federal law: ' + ' and '.join(f'{b["title"]} ({b["act"]["id"]})' for b in built),
        'acts': [b['act']['id'] for b in built],
        'history_from': first,
        'built': today,
        'dates': {
            'commit': 'in-force',
            'other_trailers': ['Enacted'],
            'time': '12:00 America/Toronto (Ottawa; UTC-5, UTC-4 in daylight time)',
        },
        'scope': {
            'trailer': 'Applies',
            'when_absent': 'this corpus records no scope notes (no commit carries Applies:); the absence is not a '
                           'statement that the change reaches every case',
            'default_reach': DEFAULT_REACH,
        },
        'tool': 'tools/on_date.py',
        'in_force_trailer': 'In-force',
        'record_to': last,
        'citation': {
            'file': r'([A-Z]-[0-9.]+)/s-0*([0-9]+(?:\.[0-9]+)*)\.md',
            'cites': r'([Ss]ections?|[Ss]ubsections?|[Pp]aragraphs?|ss?\.) ?{n}([^0-9.]|\.[^0-9]|$)',
        },
        'label': 'Canada (federal)',
        'language': 'en',
        'checked_on': today,
        'history': 'in-force',
        'record_note': f'Checked against the official source on {today}: every point-in-time version, file by file and '
                       'word for word. English text only.',
        'path_pattern': '<act id>/s-<section, whole part padded to 3 digits>.md; <act id>/schedule-<n>.md; '
                        '<act id>/intro.md',
    }
    (repo / 'corpus.json').write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + '\n', encoding='utf-8',
                                      newline='\n')


def write_reproduce(repo: Path, built: list[dict], laws: dict, log: list[dict], tags: dict, requests: list[dict],
                    today: str):
    blob = subprocess.run(['git', 'hash-object', str(HERE / 'build.py')], capture_output=True, text=True).stdout.strip()
    pyv = subprocess.run(['python', '--version'], capture_output=True, text=True).stdout.strip()
    gitv = subprocess.run(['git', '--version'], capture_output=True, text=True).stdout.strip()
    try:
        import lxml.etree
        lxmlv = '.'.join(str(x) for x in lxml.etree.LXML_VERSION[:3])
    except Exception:
        lxmlv = '?'
    ver = json.loads((HERE / 'verification.json').read_text(encoding='utf-8')) if (HERE / 'verification.json').exists() else {}
    files = {r['file'] for r in requests if r['file'].exists()}
    days = sorted({dt.date.fromtimestamp(f.stat().st_mtime).isoformat() for f in files})
    urls = {r['url'] for r in requests}
    n_index = sum(1 for u in urls if u.endswith('PITIndex.html'))
    n_versions = sum(1 for u in urls if u.endswith('P1TT3xt3.html'))
    n_annual = sum(1 for u in urls if '/AnnualStatutes/' in u)
    n_law = sum(1 for c in log if c['kind'] == 'law')
    n_cand = sum(1 for c in log if c['kind'] == 'candidates')
    n_unexp = sum(1 for c in log if c['kind'] == 'unexplained')
    n_none = sum(1 for c in log if c['kind'] == 'nochange')
    n_start = sum(1 for c in log if c['kind'] == 'start')
    n_clamped = sum(1 for c in log if c['clamped'])
    n_laws = len({c['law'] for c in log if c['kind'] == 'law'})
    why: dict[str, int] = {}
    listed: dict[str, list[str]] = {}
    for b in built:
        for ch in b['changes']:
            for k, w in ch['why'].items():
                base = w.split(';')[0]
                why[base] = why.get(base, 0) + 1
                lab = (ch['cur']['units'].get(k) or ch['prev']['units'][k])['label']
                if base != 'citation':
                    who = ''
                    if base == 'date only':
                        who = f' -> {ch["laws"][0]}'
                    elif ch['candidates'] and base != 'no new citation in its note or anywhere in the version':
                        who = f' (candidates: {", ".join(ch["new"][k] and sorted(ch["new"][k]) or ch["laws"])})'
                    listed.setdefault(base, []).append(f'{b["act"]["id"]} {ch["from"]}: {lab}{who}')
                if 'equals an earlier version' in w:
                    listed.setdefault('reprint', []).append(f'{b["act"]["id"]} {ch["from"]}: {lab}')
    n_changes = sum(why.values())
    rows = '\n'.join(
        f'| {b["act"]["id"]} | {b["title"]} | `{b["act"]["id"]}/` | {len(b["versions"])} | '
        f'{b["versions"][0]["from"]} to {b["versions"][-1]["from"]} | {len(b["versions"][-1]["units"])} |' for b in built)
    retrieved = ', '.join(days) if days else today
    chk = ver.get('check', {})
    det = ver.get('rebuild', {})
    smoke = ver.get('smoke', {})
    check_line = (f'`{chk["versions"]} versions checked ({chk["files"]} files), {chk["mismatches"]} mismatches; '
                  f'{chk["wordcheck"]} versions word for word ({chk["words"]} words) against the whole official text, '
                  f'{chk["word_mismatches"]} mismatches`' if chk else '(not yet run)')
    rebuild_line = (f'A second build from the same cache into an empty folder gave the same history: the last law commit '
                    f'was `{det["history_tip"]}` in both, and every one of the {det["commits"]} law commits and {det["tags"]} '
                    f'tags had the same hash.' if det.get('identical') else '(not yet run)')
    smoke_lines = ('\n'.join(f'   - {"pass" if r["ok"] else "FAIL"}: {r["test"]}: {r["detail"]}' for r in smoke['results'])
                   if smoke else '   (not yet run)')
    smoke_head = f'{smoke["passed"]} of {smoke["total"]} passed' if smoke else 'not yet run'
    titled = sum(1 for k in laws if laws[k]['title'])

    def items(w):
        return '\n'.join(f'- {x}' for x in listed.get(w, [])) or '- none'

    text = f"""# How this history was made, and how to make it again

This file records exactly how the repository was built: the sources, the commands, the software, the decisions made
by hand, and what an AI model did and did not do. The build writes it, so it describes the build that made this
commit.

## Short version

```sh
git clone https://github.com/lexifina/canada-law && cd canada-law
pip install lxml
python -X utf8 tools/build.py --repo ../rebuilt --today {today}
git -C ../rebuilt rev-parse main        # the same hash as this repository's main
python -X utf8 tools/check_repo.py --repo ../rebuilt --no-record
python -X utf8 tools/test_repo.py --repo ../rebuilt
```

`tools/build.py` needs Python 3.12 or later with `lxml`, and git. It reads the Justice Laws Website (or its own cache,
`.cache/` next to the script) and writes this repository into `--repo`, which must be empty or a git repository. With
the same data and the same `--today` it gives the same commits with the same hashes. `data/versions.json` lists every
version page it read with the sha256 of the HTML, so a rebuild can show it read the same bytes; the site may change
its pages, and then the hashes change too.

## Sources

All legal text and all information about versions and amending laws come from the **Justice Laws Website**
(laws-lois.justice.gc.ca) of the Department of Justice Canada. Nothing was typed in, summarised or rewritten. The build
read {n_index} version lists, {n_versions} versions and {n_annual} pages of the Annual Statutes:

| What | Where |
| --- | --- |
| Each act's point-in-time versions ("Previous Versions"), with the days each applies from and to | `https://laws-lois.justice.gc.ca/eng/acts/<id>/PITIndex.html` |
| The full English text of each version, with each section's historical note (the citations of the provisions that enacted and amended it) | `https://laws-lois.justice.gc.ca/eng/acts/<id>/<yyyymmdd>/P1TT3xt3.html`, listed with sha256 in `data/versions.json` |
| Each amending Act's title and day of Royal Assent (statutes from 2001 only; {titled} of {len(laws)} laws) | `https://laws-lois.justice.gc.ca/eng/AnnualStatutes/<year>_<chapter>/` |

| Act | Title | Folder | Versions | In force from | Files today |
| --- | --- | --- | ---: | --- | ---: |
{rows}

The data was retrieved on {retrieved}, at most four requests at a time and a request started at most every 0.25
seconds, with gzip, and the user agent `lexifina-watch/1.0 (+https://lexifina.com/watch; corpus@lexifina.com)`. The
site has no robots.txt (the address answers 404) and needs no login. Point-in-time versions exist only as HTML: the
XML the site publishes (`/eng/XML/<id>.xml`, and the justicecanada/laws-lois-xml repository on GitHub, whose history
begins in 2021) holds only the current consolidation.

## The build, step by step

1. `python -X utf8 scripts/canada-law/build.py` in Lexifina's own repository fetched the data into its cache and wrote
   this repository. `tools/build.py` here is the same file as `scripts/canada-law/build.py` there (git blob
   `{blob}`), with `tools/fetchlib.py` (the cached fetcher), `tools/reproduce.py`, which writes this file,
   `tools/check_repo.py` and `tools/test_repo.py`. Every later build ran with `--offline`, from the cache.
2. `python -X utf8 scripts/canada-law/check_repo.py` read every version of each act back from this repository with
   `tools/on_date.py`, on the day it took effect, and compared it file by file with the official text parsed afresh
   from the cached HTML; then it compared the whole act, word for word, with all the words of the version's text on
   the page, read without the build's parser. Result: {check_line}.
3. `python -X utf8 scripts/canada-law/test_repo.py --record` ran the functional smoke test against this repository
   ({smoke_head}):
{smoke_lines}
4. `python -X utf8 scripts/canada-law/build.py --offline --verify-rebuild` built the repository a second time from the
   same cache into a temporary folder and compared the hashes. {rebuild_line}
5. The build was run once more to write these results into this file, and the final `main` was rebuilt again in a
   temporary folder and compared hash for hash before it was pushed.
6. `git push origin main --tags` published it to the private GitHub repository `lexifina/canada-law`.

It ran with {pyv}, lxml {lxmlv} and {gitv} on Windows 11. No network service other than the Justice Laws Website is
involved.

## How the text and the commits are derived

Everything below is done by `tools/build.py`, deterministically.

- **Text.** Each act is a folder named by its consolidated number (`P-8.6/`, `A-1/`). Each section is one file named
  after the site's section anchor, its whole part padded to three digits: `s-4.01` is `P-8.6/s-004.01.md`; a group the
  site prints as one ("52 to 57 [Amendments]") is `s-052-to-057.md`. The headings (Part, Division, subheading) that
  begin with a section are `##`, `###` and `####` lines at the top of its file, by the heading's level on the page.
  The marginal note is a line `Marginal note: ...`; each subsection is one line beginning with the section number or
  the subsection's number; each paragraph, subparagraph, clause and definition is a list item, one level deeper for
  each level of nesting; the words that continue a subsection after its paragraphs are a line of their own. Tables
  are one line per row, cells separated by ` | `. The section's historical note is the last block: a line `History:`
  and one list item per citation, as the page lists them. `intro.md` holds the title, the chapter, the day of assent,
  the long title and the enacting words; `schedule-<n>.md` each schedule.
- **Normalised.** Only white space (runs of spaces, line breaks, tabs, no-break and other Unicode spaces become one
  space) and soft hyphens (removed). Text shown only to screen readers is left out ("Footnote", "Return to footnote");
  the label "Marginal note:" is kept as the line's prefix. The definition-term index (`dt`, the term each definition
  repeats) and the line naming the version's dates are left out. French words the English page prints (the French
  term after each definition, the French names of institutions in the schedules) are kept, as printed.
- **Changes.** Consecutive versions are compared file by file. {n_changes} changes of a file were found.
- **Cause.** Each section's historical note lists citations: `2019, c. 18, s. 2` is section 2 of the Statutes of
  Canada 2019, chapter 18; `R.S., 1985, c. 1 (4th Supp.), s. 45(F)` a provision of the Revised Statutes' supplements;
  `SOR/2006-24` a regulation. Each is read as (law, provision) pairs. A citation of the act itself (`S.C. 2000, c. 5`
  for PIPEDA; `R.S.C. 1985, c. A-1` and the 1980-81-82-83 Act it was revised from for A-1) is not an amendment: the
  consolidators re-cite it when they rewrite a note. Tried in this order:
  1. the file's note gains citations of exactly one law in this version: that law ({why.get('citation', 0)} file changes);
  2. the note gains citations of two or more laws: neither; committed by the publisher naming both, labelled
     ({why.get('the note gains citations of two or more laws', 0)});
  3. the note gains no citation, and exactly one law is new in the act's notes that day: that law, by date only,
     labelled `Evidence: date only` ({why.get('date only', 0)});
  4. the note gains no citation, and two or more laws are new that day: neither; publisher, `Candidate:` trailers
     ({why.get('no new citation in its note; two or more laws are new that day', 0)});
  5. no new citation anywhere in the version: no law; committed by the publisher and labelled
     ({why.get('no new citation in its note or anywhere in the version', 0)}).
- **Date.** The day the version applies from on the site ("From 2019-06-21 to 2024-08-18", which each version's page
  repeats; the build checks that both agree and that the versions follow each other without a gap). For the version a
  law produced, that is the day the law's provisions took effect.
- **Commits.** One commit per amending law per day ({n_law} commits by {n_laws} laws), covering every act of the record
  it changed that day; one for the first version of each act ({n_start}); {n_cand} for changes with two candidate
  laws; {n_unexp} for changes nothing explains; {n_none} for versions with no change in the English text. They are in
  the order they took effect, then one for this documentation.
  - The author is the amending law, `S.C. 2019, c. 18` or a regulation such as `SOR/2019-84`, at an address
    ending `@laws-lois.invalid` (`sc-2019-c18@laws-lois.invalid`), which cannot exist. The first version of each act is
    credited to the publisher, `Justice Laws Website (Department of Justice Canada)`: it is the act as amended up to
    then, and the site publishes no earlier version. Publisher commits are labelled in the subject.
  - Author and committer dates are noon in Ottawa on the day the change took effect: UTC-5, or UTC-4 in daylight time
    (from the second Sunday in March to the first Sunday in November since 2007; from the first Sunday in April to the
    last Sunday in October before), written into the code because the build machine has no time-zone database. The
    committer is `Lexifina <canada-law@lexifina.com>`. {n_clamped} commits are before 1970.
  - Trailers: `Evidence:`, `Kind:`, `Enacted:` (Royal Assent, statutes from 2001), `In-force:`, `Citation:` (each
    citation the law added to a note, one per line), `Source:` (the Annual Statute), `Affecting:` (one line per
    provision, `A-1 s. 2`), `Candidate:` and `Consolidated:` (the exact version page the text came from).
  - Tags: each act's days (`A-1/2019-06-21`) and each amending law (`sc/2019-c18`; a law that took effect on several
    days has one tag per day, `sc/2010-c23/2014-07-01`); {len(tags)} in all.
- **Documentation commit.** Dated {today}, the day the data was retrieved, not the day of the run, so a later rebuild
  of the same data gives the same hash. It carries `In-force: {today}` and `Kind: documentation`.

Changes credited by date only:

{items('date only')}

Changes whose note gains citations of two or more laws (credited to neither):

{items('the note gains citations of two or more laws')}

Changes with no new citation in their note, on a day two or more laws are new (credited to neither):

{items('no new citation in its note; two or more laws are new that day')}

Changes nothing explains (publisher):

{items('no new citation in its note or anywhere in the version')}

Changes whose new text equals an earlier version of the same file (labelled as a reprint of older text):

{items('reprint')}

## Decisions made by hand

These choices were made when the tool was written, after looking at the data. They are in the code.

1. **The acts.** The Constitution Acts are not in the site's point-in-time consolidation (they are a separate
   collection with no previous versions), so the record holds two federal Acts with real amendment histories: the
   Personal Information Protection and Electronic Documents Act (S.C. 2000, c. 5), and the Access to Information Act
   (R.S.C. 1985, c. A-1), which is amended often, by Acts and by orders adding institutions to its schedules.
2. **The historical note is the evidence.** The consolidated text names, in each section's note, the provisions that
   enacted and amended it. A change is credited to a law only when that law's citation is new in the note of the
   changed section in that version, or by date only (labelled) when it is the only law new that day.
3. **Two laws in one note are not separated.** Where a note gains citations of two laws on one day (often Schedule I
   of A-1, where several orders add institutions on the same day), the amending texts were not parsed to divide the
   change. It is committed by the publisher, naming both.
4. **The site's version days are the in-force days.** The amending laws' commencement provisions were not parsed.
5. **The record starts with the first point-in-time version** (2003-01-01 for PIPEDA, 2002-12-31 for A-1), credited
   to the publisher.
6. **English only.** Both languages are equally authoritative; this record holds the English text. A change to the
   French version alone shows here only as a new citation in a note, marked `(F)`.

## What an AI model did

This repository was built on {today} in **Claude Code**, Anthropic's coding tool, by the model **Claude Opus 5.5**
(model id `claude-opus-5-5`), working from a brief by the user at Lexifina: a private "git for law" repository for
Canada to the same standard as Lexifina's other corpora.

The model:

- **Researched the source:** the Justice Laws Website's point-in-time pages, the shape of their HTML and historical
  notes, the Reproduction of Federal Law Order, the site's notices, and the site's XML.
- **Wrote all the code and text in this repository:** `tools/build.py`, `tools/fetchlib.py`, `tools/reproduce.py`,
  `tools/check_repo.py`, `tools/test_repo.py`, `tools/on_date.py`, the README, this file and the licence, and chose
  the design described in them.
- **Ran the commands above** and checked the results.

The model did **not**:

- **Write or edit any legal text.** Every word of every provision, every date and every law's title is copied by the
  script from the Justice Laws Website.
- **Take part in building the history.** No AI model is called when the history is built or checked.

The user decided what was in scope and decides whether the repository is ever made public. The work was not reviewed
line by line by a lawyer. This is not an official version: for all purposes of interpreting and applying the law, the
Department of Justice refers users to the original and amending Acts as passed by Parliament and the regulations as
registered.

## Prior art

- [justicecanada/laws-lois-xml](https://github.com/justicecanada/laws-lois-xml): the Department of Justice's own XML of
  the current consolidation, in git since 2021, one commit per site update (not per law, and not dated by when law took
  effect).
- [sandole/legalize-ca](https://github.com/sandole/legalize-ca): Canadian federal Acts as Markdown, one file per Act,
  one dated commit per amendment. Not read for this build and no code copied; this repository instead keeps one file
  per section and credits each change to the law its historical note cites.
- Lexifina's other corpora, whose rules this one follows (Estonia, Liechtenstein, Luxembourg, Slovakia, Swiss federal
  law, the Grundgesetz, UK legislation and the US Code).
"""
    (repo / 'REPRODUCE.md').write_text(text, encoding='utf-8', newline='\n')
