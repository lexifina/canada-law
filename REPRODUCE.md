# How this history was made, and how to make it again

This file records exactly how the repository was built: the sources, the commands, the software, the decisions made
by hand, and what an AI model did and did not do. The build writes it, so it describes the build that made this
commit.

## Short version

```sh
git clone https://github.com/lexifina/canada-law && cd canada-law
pip install lxml
python -X utf8 tools/build.py --repo ../rebuilt --today 2026-10-28
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
read 2 version lists, 141 versions and 86 pages of the Annual Statutes:

| What | Where |
| --- | --- |
| Each act's point-in-time versions ("Previous Versions"), with the days each applies from and to | `https://laws-lois.justice.gc.ca/eng/acts/<id>/PITIndex.html` |
| The full English text of each version, with each section's historical note (the citations of the provisions that enacted and amended it) | `https://laws-lois.justice.gc.ca/eng/acts/<id>/<yyyymmdd>/P1TT3xt3.html`, listed with sha256 in `data/versions.json` |
| Each amending Act's title and day of Royal Assent (statutes from 2001 only; 86 of 118 laws) | `https://laws-lois.justice.gc.ca/eng/AnnualStatutes/<year>_<chapter>/` |

| Act | Title | Folder | Versions | In force from | Files today |
| --- | --- | --- | ---: | --- | ---: |
| P-8.6 | Personal Information Protection and Electronic Documents Act | `P-8.6/` | 17 | 2003-01-01 to 2025-03-04 | 76 |
| A-1 | Access to Information Act | `A-1/` | 124 | 2002-12-31 to 2026-06-14 | 175 |

The data was retrieved on 2026-10-28, at most four requests at a time and a request started at most every 0.25
seconds, with gzip, and the user agent `lexifina-watch/1.0 (+https://lexifina.com/watch; corpus@lexifina.com)`. The
site has no robots.txt (the address answers 404) and needs no login. Point-in-time versions exist only as HTML: the
XML the site publishes (`/eng/XML/<id>.xml`, and the justicecanada/laws-lois-xml repository on GitHub, whose history
begins in 2021) holds only the current consolidation.

## The build, step by step

1. `python -X utf8 scripts/canada-law/build.py` in Lexifina's own repository fetched the data into its cache and wrote
   this repository. `tools/build.py` here is the same file as `scripts/canada-law/build.py` there (git blob
   `e247d3521b142513e5b441cb380f4aeb960059c5`), with `tools/fetchlib.py` (the cached fetcher), `tools/reproduce.py`, which writes this file,
   `tools/check_repo.py` and `tools/test_repo.py`. Every later build ran with `--offline`, from the cache.
2. `python -X utf8 scripts/canada-law/check_repo.py` read every version of each act back from this repository with
   `tools/on_date.py`, on the day it took effect, and compared it file by file with the official text parsed afresh
   from the cached HTML; then it compared the whole act, word for word, with all the words of the version's text on
   the page, read without the build's parser. Result: `141 versions checked (14749 files), 0 mismatches; 141 versions word for word (3559819 words) against the whole official text, 0 mismatches`.
3. `python -X utf8 scripts/canada-law/test_repo.py --record` ran the functional smoke test against this repository
   (6 of 6 passed):
   - pass: blame names a law: P-8.6/s-007.md lines by Justice Laws Website (Department of Justice Canada), S.C. 2004, c. 15, S.C. 2015, c. 32, S.C. 2024, c. 17
   - pass: text before and after an amendment: P-8.6/s-007.md 2025-03-03 != 2025-03-04; A-1/s-013.md 2023-08-31 != 2023-09-01
   - pass: log --follow in date order: P-8.6/s-007.md 4 commits; A-1/s-013.md 14 commits; A-1/schedule-i.md 79 commits
   - pass: tags resolve, In-force on every commit: 271 tags resolve; all 147 commits carry In-force
   - pass: only the documentation commit is by Lexifina: only the documentation commit 0299cbe1f4 is by Lexifina; 104 distinct authors
   - pass: README commands run: 10 README commands ran and printed output
4. `python -X utf8 scripts/canada-law/build.py --offline --verify-rebuild` built the repository a second time from the
   same cache into a temporary folder and compared the hashes. A second build from the same cache into an empty folder gave the same history: the last law commit was `dccbf236e7abd5b4603f3c67a62bc7423c39e952` in both, and every one of the 146 law commits and 271 tags had the same hash.
5. The build was run once more to write these results into this file, and the final `main` was rebuilt again in a
   temporary folder and compared hash for hash before it was pushed.
6. `git push origin main --tags` published it to the private GitHub repository `lexifina/canada-law`.

It ran with Python 3.12.10, lxml 6.1.3 and git version 2.46.0.windows.1 on Windows 11. No network service other than the Justice Laws Website is
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
- **Changes.** Consecutive versions are compared file by file. 412 changes of a file were found.
- **Cause.** Each section's historical note lists citations: `2019, c. 18, s. 2` is section 2 of the Statutes of
  Canada 2019, chapter 18; `R.S., 1985, c. 1 (4th Supp.), s. 45(F)` a provision of the Revised Statutes' supplements;
  `SOR/2006-24` a regulation. Each is read as (law, provision) pairs. A citation of the act itself (`S.C. 2000, c. 5`
  for PIPEDA; `R.S.C. 1985, c. A-1` and the 1980-81-82-83 Act it was revised from for A-1) is not an amendment: the
  consolidators re-cite it when they rewrite a note. Tried in this order:
  1. the file's note gains citations of exactly one law in this version: that law (383 file changes);
  2. the note gains citations of two or more laws: neither; committed by the publisher naming both, labelled
     (14);
  3. the note gains no citation, and exactly one law is new in the act's notes that day: that law, by date only,
     labelled `Evidence: date only` (8);
  4. the note gains no citation, and two or more laws are new that day: neither; publisher, `Candidate:` trailers
     (0);
  5. no new citation anywhere in the version: no law; committed by the publisher and labelled
     (2).
- **Date.** The day the version applies from on the site ("From 2019-06-21 to 2024-08-18", which each version's page
  repeats; the build checks that both agree and that the versions follow each other without a gap). For the version a
  law produced, that is the day the law's provisions took effect.
- **Commits.** One commit per amending law per day (130 commits by 103 laws), covering every act of the record
  it changed that day; one for the first version of each act (2); 12 for changes with two candidate
  laws; 2 for changes nothing explains; 0 for versions with no change in the English text. They are in
  the order they took effect, then one for this documentation.
  - The author is the amending law, `S.C. 2019, c. 18` or a regulation such as `SOR/2019-84`, at an address
    ending `@laws-lois.invalid` (`sc-2019-c18@laws-lois.invalid`), which cannot exist. The first version of each act is
    credited to the publisher, `Justice Laws Website (Department of Justice Canada)`: it is the act as amended up to
    then, and the site publishes no earlier version. Publisher commits are labelled in the subject.
  - Author and committer dates are noon in Ottawa on the day the change took effect: UTC-5, or UTC-4 in daylight time
    (from the second Sunday in March to the first Sunday in November since 2007; from the first Sunday in April to the
    last Sunday in October before), written into the code because the build machine has no time-zone database. The
    committer is `Lexifina <canada-law@lexifina.com>`. 0 commits are before 1970.
  - Trailers: `Evidence:`, `Kind:`, `Enacted:` (Royal Assent, statutes from 2001), `In-force:`, `Citation:` (each
    citation the law added to a note, one per line), `Source:` (the Annual Statute), `Affecting:` (one line per
    provision, `A-1 s. 2`), `Candidate:` and `Consolidated:` (the exact version page the text came from).
  - Tags: each act's days (`A-1/2019-06-21`) and each amending law (`sc/2019-c18`; a law that took effect on several
    days has one tag per day, `sc/2010-c23/2014-07-01`); 271 in all.
- **Documentation commit.** Dated 2026-10-28, the day the data was retrieved, not the day of the run, so a later rebuild
  of the same data gives the same hash. It carries `In-force: 2026-10-28` and `Kind: documentation`.

Changes credited by date only:

- P-8.6 2014-07-01: s. 12 -> S.C. 2010, c. 23
- P-8.6 2014-07-01: s. 12.2 -> S.C. 2010, c. 23
- P-8.6 2014-07-01: s. 20 -> S.C. 2010, c. 23
- A-1 2007-03-01: s. 68 -> S.C. 2006, c. 9
- A-1 2007-03-01: s. 70 -> S.C. 2006, c. 9
- A-1 2007-09-01: s. 3 -> S.C. 2006, c. 9
- A-1 2007-09-01: s. 77 -> S.C. 2006, c. 9
- A-1 2020-06-21: s. 72 -> S.C. 2019, c. 18

Changes whose note gains citations of two or more laws (credited to neither):

- P-8.6 2007-04-15: s. 9 (candidates: S.C. 2005, c. 46, S.C. 2006, c. 9)
- A-1 2003-12-12: Schedule I (candidates: SOR/2003-423, SOR/2003-428, SOR/2003-435, SOR/2003-440)
- A-1 2004-04-01: Schedule I (candidates: S.C. 2003, c. 22, SOR/2004-24)
- A-1 2005-10-05: Schedule I (candidates: S.C. 2005, c. 34, S.C. 2005, c. 35)
- A-1 2005-10-05: Schedule II (candidates: S.C. 2005, c. 34, S.C. 2005, c. 35)
- A-1 2006-02-06: Schedule I (candidates: SOR/2006-24, SOR/2006-28, SOR/2006-34)
- A-1 2007-04-15: s. 16.4 (candidates: S.C. 2005, c. 46, S.C. 2006, c. 9)
- A-1 2007-04-15: s. 16.5 (candidates: S.C. 2005, c. 46, S.C. 2006, c. 9)
- A-1 2007-04-15: Schedule I (candidates: S.C. 2005, c. 46, S.C. 2006, c. 9)
- A-1 2008-06-01: Schedule I (candidates: SOR/2008-130, SOR/2008-135)
- A-1 2013-04-01: Schedule I (candidates: S.C. 2012, c. 19, S.C. 2012, c. 31)
- A-1 2013-06-19: Schedule I (candidates: S.C. 2013, c. 14, S.C. 2013, c. 24)
- A-1 2014-04-01: Schedule I (candidates: S.C. 2012, c. 19, S.C. 2014, c. 2)
- A-1 2014-11-01: Schedule I (candidates: S.C. 2013, c. 40, S.C. 2014, c. 20)

Changes with no new citation in their note, on a day two or more laws are new (credited to neither):

- none

Changes nothing explains (publisher):

- P-8.6 2009-06-01: s. 72
- A-1 2013-06-01: Schedule I

Changes whose new text equals an earlier version of the same file (labelled as a reprint of older text):

- none

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

This repository was built on 2026-10-28 in **Claude Code**, Anthropic's coding tool, by the model **Claude Opus 5.5**
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
