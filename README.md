# Canadian federal law, change by change

Two federal Acts of Canada as a git repository: the Personal Information Protection and Electronic Documents Act
(PIPEDA, S.C. 2000, c. 5, consolidated number P-8.6) and the Access to Information Act (R.S.C. 1985, c. A-1). Each
amending law is one commit, credited to that law and dated the day its change took effect, at noon in Ottawa. The text
is the English consolidated text published by the Department of Justice Canada on the
[Justice Laws Website](https://laws-lois.justice.gc.ca), in each of its point-in-time versions since 2002-2003.

This is not an official version (see [Licence](#licence)).

## The questions, as git commands

| Question | Command |
| --- | --- |
| What did PIPEDA s. 7 say on 1 January 2020? | `python tools/on_date.py 2020-01-01 P-8.6 7` |
| The whole Access to Information Act as it stood on 1 January 2010 | `python tools/on_date.py 2010-01-01 A-1` |
| Schedule I of the Access to Information Act on 1 January 2005 | `python tools/on_date.py 2005-01-01 A-1 schedule-i` |
| Which law wrote each line of PIPEDA s. 7? | `git blame P-8.6/s-007.md` |
| Every change to s. 13 of the Access to Information Act, with the law and the day | `git log --follow A-1/s-013.md` |
| Everything one law changed (both Acts) | `git show --stat sc/2024-c16` |
| What changed in PIPEDA on one day | `git show --stat P-8.6/2015-06-18` |
| The amending laws with all their dates | [`laws.csv`](laws.csv) |
| Changes where two laws were possible (credited to neither) | `git log --grep="credited to neither"` |
| Changes credited by date only | `git log --grep="Evidence: date only"` |
| Laws that amended the Access to Information Act in 2019 | `git log --format="%an %s" --since=2019-01-01T00:00:00-05:00 --until=2019-12-31T23:59:59-05:00 -- A-1` |

## The dates, and which one we use

A Canadian Act has the day it received Royal Assent (`Enacted:`) and the day or days its provisions came into force
(`In-force:`); a regulation has the day it was registered. **Commits are dated the day the change took effect**, at noon
in Ottawa (Eastern time, UTC-5, or UTC-4 in daylight time): that is the day the Justice Laws Website gives as the start
of the version the change produced ("From 2019-06-21 to 2024-08-18"). Royal Assent is in the commit message for
statutes from 2001. `tools/on_date.py` reads the `In-force:` trailer, not the commit date, so it does not depend on the
reader's time zone; with raw git, give a full time, `--before="2019-06-21T23:59:59-04:00"`.

A law can take effect in steps: S.C. 2019, c. 18 changed the Access to Information Act on 2019-06-21 and again on
2020-06-21. Each step is its own commit, with its own tag (`sc/2019-c18/2020-06-21`).

In PowerShell, `git show $(...):path` is split into two arguments; use
`$r = git rev-list -1 A-1/2019-06-21; git show "$($r):A-1/s-002.md"`. After a rebuild of this repository, fetch with
`git fetch --force --tags`, because git does not overwrite tags you already have.

## What "author" means

The author of a commit is the law that made the change: `S.C. 2019, c. 18` (Statutes of Canada 2019, chapter 18),
or a regulation such as `SOR/2019-84`, with an address ending `@laws-lois.invalid`, which
cannot exist, so `git blame` names the law. The committer is always `Lexifina`.

The evidence is the consolidation's own historical notes. Under each section the site lists the citations of the
provisions that enacted and amended it ("2019, c. 18, s. 2"). A changed section is credited to the law whose citation is
new in its note in the version from that day. A citation of the Act itself is not an amendment: the consolidators
re-cite the enacting Act whenever they rewrite a note. Three further rules, each labelled in the commit:

- a section that changed with no new citation in its note, on a day when exactly one law is new in the Act's notes, is
  credited to that law by date only (`Evidence: date only`);
- where a note gains citations of two laws on one day (often Schedule I, the list of government institutions, when
  several orders add institutions on the same day), or a section changed with no new citation on a day two laws are
  new, the change is committed by the publisher, `Justice Laws Website (Department of Justice Canada)`, labelled
  "credited to neither", with each law in a `Candidate:` trailer;
- a change no new citation explains at all (an editorial note, an institution removed without a citation) is the
  publisher's, labelled "no amending law cited".

The first version of each Act (2003-01-01 for PIPEDA, 2002-12-31 for the Access to Information Act) is the Act as
amended up to then. The site publishes nothing earlier, so those lines are credited to the publisher. The historical
note at the foot of each file still names the laws that made them.

Blame credits whole lines. A subsection rewritten by one law and then touched by another is credited to the later one;
use `git log -p --word-diff` to see each law's words.

## How it is checked

`tools/check_repo.py` reads every version of each Act back from git, with `tools/on_date.py`, on the day it took effect,
and compares it with the official text: file by file with the text parsed from the site's page, and word for word with
all the words of the page's text, read independently of the parser. `tools/test_repo.py` checks that the commands above
work. The results are in [`REPRODUCE.md`](REPRODUCE.md).

## Files

Each Act is a folder named by its consolidated number (`P-8.6/`, `A-1/`). Each section is one file, named by its
number with the whole part padded to three digits: `P-8.6/s-007.md` is section 7, `P-8.6/s-004.01.md` section 4.01.
Inside a file:

- the headings of the Part, Division and subheadings that begin with the section are `##`, `###` and `####` lines;
- `Marginal note: ...` lines are the marginal notes;
- each subsection is one line; paragraphs, subparagraphs, clauses and definitions are list items, one level deeper for
  each level;
- the last block is the historical note: `History:` and one citation per line.

`intro.md` holds the title, chapter, assent and long title; `schedule-<n>.md` each schedule (one line per row of a
table). A repealed section stays, as the site prints it: `[Repealed, 2015, c. 32, s. 6]`. Each folder's `README.md`
lists its provisions and how often each changed.

## What it does not show

- Versions the site does not publish: nothing before 2002-12-31 (A-1) or 2003-01-01 (PIPEDA).
- The French text, which is equally authoritative. A change to the French version alone shows here only as a new
  citation marked `(F)` in a note.
- Which of two laws of the same day made a change (above).
- Amendments not yet in force, and the "Related Provisions" (transitional provisions of amending Acts) the site lists
  separately: only the consolidated text of each version is recorded.
- Fee amounts adjusted automatically under the Service Fees Act, which the consolidated text does not show.
- Any other Act. The same build works for any Act on the site: add it to `ACTS` in `tools/build.py`.

## How it is built

`tools/build.py` reads the Justice Laws Website and writes this repository from scratch; the same data gives the same
hashes. Every step, the software, the decisions made by hand and what an AI model did are in
[`REPRODUCE.md`](REPRODUCE.md). [`corpus.json`](corpus.json) describes the corpus for tools that read several of
Lexifina's law repositories. `data/versions.json` lists every source page with its sha256.

## Licence

The text of the Acts is reproduced under the Reproduction of Federal Law Order, SI/97-5: "Anyone may, without charge or
request for permission, reproduce enactments and consolidations of enactments of the Government of Canada, and
decisions and reasons for decisions of federally-constituted courts and administrative tribunals, provided due diligence
is exercised in ensuring the accuracy of the materials reproduced and the reproduction is not represented as an
official version." Source: Justice Laws Website, https://laws-lois.justice.gc.ca, Department of Justice Canada.

**This is not an official version,** and it is not made in affiliation with or with the endorsement of the Government
of Canada. The official consolidation is on the Justice Laws Website; for all purposes of interpreting and applying
the law, the Department of Justice refers users to the Acts as passed by Parliament and the regulations as registered.
The history, commit messages, tables and tools are released under [CC0 1.0](LICENSE).
