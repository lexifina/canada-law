# How this history was made, and how to make it again

This file records how the repository was built: the sources, the commands, the software, the decisions made by hand,
and what an AI model did and did not do.

The history only grows. The first build (2026-10-28) wrote PIPEDA (P-8.6) and the Access to Information Act (A-1) from
the Justice Laws Website's point-in-time versions. Each later batch of Acts from Justice Canada's XML repository was
appended on top of the published `main` as new commits, followed by a new documentation commit; nothing published was
rewritten, re-sorted or re-dated, and no tag was moved.

## Short version

```sh
git clone https://github.com/lexifina/canada-law && cd canada-law
pip install lxml
git clone https://github.com/justicecanada/laws-lois-xml ../laws-lois-xml
# the first two Acts, from the Justice Laws Website:
python -X utf8 tools/build.py --repo ../rebuilt --today 2026-10-28
```

Each later batch is appended to the published head it names below, from the XML repository read up to the commit it
names, by the method described under "the Acts from the XML repository". With the same head and the same XML commit
the append gives the same commits with the same hashes: author dates are noon in Ottawa on the in-force day, committer
dates the published head's committer time plus one second per appended commit. The tools:

```sh
python -X utf8 tools/append.py --xml ../laws-lois-xml --upto <XML commit> --repo ../rebuilt --acts <ids>     --today <day> --docs-date <day> --docs <documentation folder> --titles data/law-titles.json
python -X utf8 tools/check_xml.py --xml ../laws-lois-xml --repo ../rebuilt --acts <ids> --today <day>
```

`tools/lawtext.py` is the parser, the rules and the commit messages (from 2026-11-02 the part of `tools/build.py` that
reads a version and writes the commits; `tools/build.py` is the first build's script as it was on 2026-10-28);
`tools/xmlsource.py` reads the versions from the XML repository; `tools/append.py` appends; `tools/check_xml.py` checks
the appended Acts; `tools/check_repo.py` checks P-8.6 and A-1 against the point-in-time pages (it needs those pages,
which `tools/build.py` reads).

## Sources

All legal text and all information about versions and amending laws come from the Department of Justice Canada.
Nothing was typed in, summarised or rewritten.

| What | Source |
| --- | --- |
| P-8.6 and A-1: each point-in-time version ("Previous Versions"), with the days it applies from and to, and its full English text with each section's historical note | Justice Laws Website, `https://laws-lois.justice.gc.ca/eng/acts/<id>/PITIndex.html` and `.../<id>/<yyyymmdd>/P1TT3xt3.html` |
| The other Acts: every state of the Act's XML file in the history of Justice Canada's XML repository of the consolidated Acts and regulations, each a consolidated version, with the day it applies from (`lims:lastAmendedDate`), each provision's in-force day (`lims:inforce-start-date`) and each section's historical note | [justicecanada/laws-lois-xml](https://github.com/justicecanada/laws-lois-xml), `eng/acts/<id>.xml`; each commit names the exact file in its `Consolidated:` trailer |
| The layout of the text: the repository's own transform to HTML, a modified copy of the one that makes the Justice Laws Website's pages | `xslt/LIMS2HTML.xsl` in the same repository |
| Each amending Act's title and day of Royal Assent (statutes from 2001) | the Annual Statutes on the Justice Laws Website, `https://laws-lois.justice.gc.ca/eng/AnnualStatutes/<year>_<chapter>/` (listed in `data/law-titles.json`); where there is none, the Annual Statute's XML in `annual-statutes-lois-annuelles/en/` of the XML repository |

## The batches

Each batch was appended to the published head named here, read the XML repository up to the commit named, and was checked before it was published.

| Batch | Appended to | XML repository read up to | Acts | Commits | New tags | Versions checked | Files | Words | Mismatches | Smoke test |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 (2026-11-02) | `f5b5dc1dc665` | `0507465393c2` | C-46 | 49 | 69 | 36 | 59714 | 14582505 | 0 | 6/6 |

Batch 1:

- C-46 (Criminal Code): 36 versions, 2020-07-01 to 2026-07-18; 30 from consolidations in the XML repository, 6 rebuilt between two of them from the provisions' in-force days (8 commits carry Dated-by).
- Commits: 1 first version (publisher), 38 by 32 amending laws, 9 credited to neither of two laws (Candidate trailers), 1 with no amending law cited (s. 183, 2026, publisher).
- Two versions were re-issued by the publisher with a different text on the same day (2025-01-01, 2026-03-26); the later text is used.
- Checks on the appended repository: every version file by file, 0 mismatches (59,714 files); every consolidation word for word, 0 mismatches (14,582,505 words); P-8.6 and A-1 rechecked against their point-in-time pages, 141 versions, 0 mismatches file by file (14,749 files) and word for word (3,559,819 words); tools/test_repo.py 6 of 6.
- Corrections: none. No version main already held was changed; P-8.6 and A-1 get no new versions from the XML repository (it holds none after their last In-force day).

## How the text and the commits are derived: P-8.6 and A-1 (first build, 2026-10-28)

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
    last Sunday in October before). The
    committer is `Lexifina <canada-law@lexifina.com>`. 0 commits are before 1970.
  - Trailers: `Evidence:`, `Kind:`, `Enacted:` (Royal Assent, statutes from 2001), `In-force:`, `Citation:` (each
    citation the law added to a note, one per line), `Source:` (the Annual Statute), `Affecting:` (one line per
    provision, `A-1 s. 2`), `Candidate:` and `Consolidated:` (the exact version page the text came from).
  - Tags: each act's days (`A-1/2019-06-21`) and each amending law (`sc/2019-c18`; a law that took effect on several
    days has one tag per day, `sc/2010-c23/2014-07-01`); 271 in all.
- **Documentation commit.** Dated 2026-10-28, the day of the source data, not the day of the run, so a later rebuild
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

## How the text and the commits are derived: the Acts from the XML repository

Everything below is done deterministically, with the parser, the rules and the commit messages of `tools/build.py`
above.

- **Versions.** Every commit of the XML repository that changed the Act's file is a state of it. A state is a
  consolidated version; the day it applies from is its root element's `lims:lastAmendedDate` (the `pit-date` beside
  it can be later, when a version changes nothing in the English text). A later state with the same day and the same
  text is the same version; with the same day and a different text, the later state stands (listed below); a state
  dated before the one before it is not used (listed below). For every state of P-8.6 and A-1 since 2021 the day is
  the "From" day of the point-in-time version on the Justice Laws Website, and the text, through the steps below, is
  identical, file for file, to that version in this repository (23 versions of A-1, 3 of P-8.6, 0 differences).
- **Versions between two states.** States are days or weeks apart, so an Act can have more than one version between
  two of them. Each provision in the XML carries the day it came into force in its current form
  (`lims:inforce-start-date`, on the provision and each of its parts). A file that changed between two states is
  dated by the latest such day in its section and the headings before it, when that day falls after the earlier
  state's version and before the later one's; the version of that day is rebuilt from the earlier state with the
  files changed by then. Its commits carry `Dated-by:`. Tried on A-1 with every second (and every third) state left
  out: of 21 (18) versions, 19 (15) were identical to the published point-in-time versions, and 2 (3) differed in
  one file each, where a file changed twice between the states kept.
- **Text.** The XML goes through the repository's transform (`xslt/LIMS2HTML.xsl`) to HTML, and the HTML through
  `build.read_version`, the parser of the point-in-time pages. Where the transform differs from the site's pages in
  layout, it is put right: the chapter line (`R.S.C., 1985`, `S.C. 2000`, not `R.S.C, 1985`, `S.C 2000`, and no
  unofficial consolidated number after an annual chapter), the day of assent written in full (`2000-04-13`), the list
  that holds a section with subsections marked as a section, no full stop after a historical note, and the
  "Related Provisions" and "Amendments Not in Force" schedules and the list of recent amending Acts left out (the
  point-in-time text has none of them). The rest is as the transform makes it.
- **Notes.** Historical notes of the older Acts also cite the Revised Statutes of 1970 (`R.S., c. B-2, s. 1`), list
  several citations in one item separated by `;`, or hold an editorial note (`[NOTE: Application provisions are not
  included in the consolidated text; ...]`). These are read as citations of `R.S.C. 1970, c. ...`, as separate
  citations, and as no citation. A schedule labelled other than `SCHEDULE <n>` (`SCHEDULE TO PART XX.1`, `FORM 5.0031`)
  is `schedule-to-part-xx.1.md`, `schedule-form-5.0031.md`; such files are ordered schedules to a Part, then other
  schedules, then forms, by number.
- **Causes, dates and messages** as above, per Act: the first version is committed by the publisher; then one commit
  per amending law per day, then the changes with two candidate laws and those nothing explains. The `Consolidated:`
  trailer names the exact file in the XML repository's history (`.../blob/<commit>/eng/acts/<id>.xml`).
- **Titles of the amending Acts** and their days of assent: as for P-8.6 and A-1, each statute's Annual Statutes page
  on the Justice Laws Website (`https://laws-lois.justice.gc.ca/eng/AnnualStatutes/<year>_<chapter>/`, its title and
  "Assented to" day), listed in `data/law-titles.json`; where there is none, the Annual Statute in the XML repository
  (`annual-statutes-lois-annuelles/en/`, its short title, else its long title, and the day of assent; each listed
  below). The two can differ: for 5 of the 72 statutes of P-8.6 and A-1 in both, the page's title is the long title
  where the XML gives the short title.
- **Order and dates.** Each Act is one block on top of what was published: its first version, then its changes in the
  order they took effect. Author dates are noon in Ottawa on the in-force day, as above. Committer dates are the
  published head's committer time plus one second per commit.
- **Tags.** `<act>/<day>` for each day of each Act, and `<law>/<day>` for each amending law and day (an existing tag
  of a law, `sc/2019-c18`, is never moved, and a law that has a bare tag gets no day tags beside it). No published
  tag was moved or deleted.
- **Checks.** File by file: every version (states and rebuilt versions), read back from git with `tools/on_date.py` on
  its day, is exactly the files the parser makes from it. Word for word: for every state, the whole Act printed by
  `tools/on_date.py`, with its markdown marks removed, has the same words in the same order as all the text of the
  state's HTML, read without the parser (the definition-term index, text only for screen readers and the version's
  date line left out, as for the point-in-time pages).

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
7. **Append only.** From 2026-11-02 the published history is never rewritten: each further Act is added on top, as
   one block, and each batch ends with its own documentation commit. Anything that would change a version `main`
   already holds is a correction; it is not published by an append, and is listed here instead.
8. **The other Acts come from the XML repository.** The Justice Laws Website publishes point-in-time versions only as
   HTML pages, one per version; Justice Canada's XML repository holds every consolidation since February 2021 in its
   git history. Its states are the versions of the other Acts, so their record begins with the version in force in
   early 2021 (or when the Act first appears there).
9. **The provisions' own in-force days** date a change between two states; this is the only date the record infers,
   and those commits say so (`Dated-by:`).
10. **Order of the Acts:** the most-cited Acts first (Criminal Code, Income Tax Act, Canada Labour Code, Bank Act, ...),
    then all other Acts, then the regulations.

## What an AI model did

The first build (2026-10-28) and each append were made in **Claude Code**, Anthropic's coding tool, by the model
**Claude Opus 5.5** (model id `claude-opus-5-5`), working from briefs by the user at Lexifina.

The model:

- **Researched the sources:** the Justice Laws Website's point-in-time pages, Justice Canada's XML repository and its
  transform, the shape of the historical notes, the Reproduction of Federal Law Order and the Open Government Licence -
  Canada.
- **Wrote all the code and text in this repository:** the tools, the README, this file and the licence, and chose
  the design described in them; and checked, on P-8.6 and A-1, that the XML gives the same text and the same days as
  the point-in-time pages.
- **Ran the commands above** and checked the results.

The model did **not**:

- **Write or edit any legal text.** Every word of every provision, every date and every law's title is copied by the
  scripts from Justice Canada's publications.
- **Take part in building the history.** No AI model is called when the history is built or checked.

The user decided what was in scope and decides whether the repository is ever made public. The work was not reviewed
line by line by a lawyer. This is not an official version: for all purposes of interpreting and applying the law, the
Department of Justice refers users to the original and amending Acts as passed by Parliament and the regulations as
registered.

## Prior art

- [justicecanada/laws-lois-xml](https://github.com/justicecanada/laws-lois-xml): the Department of Justice's own XML of
  the consolidation, in git since 2021, one commit per update of the consolidation (not per law, and not dated by when
  law took effect). The source of every Act here other than P-8.6 and A-1.
- [sandole/legalize-ca](https://github.com/sandole/legalize-ca): Canadian federal Acts as Markdown, one file per Act,
  one dated commit per amendment. Not read for this build and no code copied; this repository instead keeps one file
  per section and credits each change to the law its historical note cites.
- Lexifina's other corpora, whose rules this one follows (Estonia, Liechtenstein, Luxembourg, Slovakia, Swiss federal
  law, the Grundgesetz, UK legislation and the US Code).
