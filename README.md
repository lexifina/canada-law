# Canadian federal law, change by change

Federal Acts of Canada as a git repository: each amending law is one commit, credited to that law and dated the day its
change took effect, at noon in Ottawa. The text is the English consolidated text published by the Department of Justice
Canada. The record grows Act by Act; the Acts it holds and the period each covers are in [`ACTS.md`](ACTS.md).

- **PIPEDA (P-8.6) and the Access to Information Act (A-1)**: every point-in-time version on the
  [Justice Laws Website](https://laws-lois.justice.gc.ca) since 2002-2003.
- **The Criminal Code (C-46)**: every consolidated version in Justice Canada's XML repository of the consolidated Acts
  and regulations, [justicecanada/laws-lois-xml](https://github.com/justicecanada/laws-lois-xml), whose history begins
  in February 2021.
- **Every other Act, then every regulation**: first its current consolidation alone, from the same repository, dated
  the day of its last amendment in force (its `lastAmendedDate`), committed by the publisher and labelled "oldest
  version available" (`Record:` trailer). Its earlier versions, from the XML repository's history (2021 on), then
  follow behind it as labelled correction commits (`Kind: correction`, `Corrects: <act> <from>..<to>`, one per
  version, oldest first, each holding that version's whole act), and one more correction restores the text in force
  now at the tip (`Supersedes:` the current-text commit). `tools/on_date.py` and the shared correction reader both
  read each version on its days. A version is credited to the amending law its historical notes name, where one law
  explains every file it changed; otherwise to the publisher, with `Candidate:` trailers. An
  Act whose text the reader cannot split into sections is one file, `text.md`, holding the whole text in the same
  line format (`Layout: one file for the whole text`). [`ACTS.md`](ACTS.md) says which is which.

This is not an official version (see [Licence](#licence)).

## The questions, as git commands

| Question | Command |
| --- | --- |
| What did PIPEDA s. 7 say on 1 January 2020? | `python tools/on_date.py 2020-01-01 P-8.6 7` |
| The whole Access to Information Act as it stood on 1 January 2010 | `python tools/on_date.py 2010-01-01 A-1` |
| Schedule I of the Access to Information Act on 1 January 2005 | `python tools/on_date.py 2005-01-01 A-1 schedule-i` |
| What did s. 320.14 of the Criminal Code say on 1 January 2024? | `python tools/on_date.py 2024-01-01 C-46 320.14` |
| Which law wrote each line of PIPEDA s. 7? | `git blame P-8.6/s-007.md` |
| Every change to s. 13 of the Access to Information Act, with the law and the day | `git log --follow A-1/s-013.md` |
| Every change to the Criminal Code since 2021, with the law and the day | `git log --format="%(trailers:key=In-force,valueonly,separator=) %an %s" -- C-46` |
| Everything one law changed | `git show --stat sc/2024-c16` |
| What changed in PIPEDA on one day | `git show --stat P-8.6/2015-06-18` |
| The amending laws with all their dates | [`laws.csv`](laws.csv) |
| Changes where two laws were possible (credited to neither) | `git log --grep="credited to neither"` |
| Changes credited by date only | `git log --grep="Evidence: date only"` |
| Laws that amended the Access to Information Act in 2019 | `git log --format="%an %s" --since=2019-01-01T00:00:00-05:00 --until=2019-12-31T23:59:59-05:00 -- A-1` |

## The dates, and which one we use

A Canadian Act has the day it received Royal Assent (`Enacted:`) and the day or days its provisions came into force
(`In-force:`); a regulation has the day it was registered. **Commits are dated the day the change took effect**, at noon
in Ottawa (Eastern time, UTC-5, or UTC-4 in daylight time): the day Justice Canada gives as the start of the version the
change produced. On the Justice Laws Website that is the "From" day of a point-in-time version; in the XML it is the
version's `lastAmendedDate` (for every version of P-8.6 and A-1 since 2021 the two agree, and the texts are identical).
Royal Assent is in the commit message for statutes from 2001. `tools/on_date.py` reads the `In-force:` trailer, not
the commit date, so it does not depend on the reader's time zone.

The XML repository is a series of snapshots of the whole consolidation, days or weeks apart, so two versions of an Act
can fall between two snapshots. Every provision in the XML carries the day it came into force in its current form;
a provision that changed between two snapshots is dated by that day when it falls after the earlier snapshot's version,
and those commits say so in a `Dated-by:` trailer.

A law can take effect in steps: S.C. 2019, c. 18 changed the Access to Information Act on 2019-06-21 and again on
2020-06-21. Each step is its own commit, with its own tag (`sc/2019-c18/2020-06-21`).

The history only grows: each new Act is added on top of what was already published, as one block of its own commits
in the order its changes took effect. So the commit order across Acts is not the order of the days; the `In-force:`
trailer is, and `tools/on_date.py`, `git log -- <act>` and `git blame` read each Act on its own. With raw git over the
whole tree, `git rev-list --before=<day>` is exact only for the first two Acts.

In PowerShell, `git show $(...):path` is split into two arguments; use
`$r = git rev-list -1 A-1/2019-06-21; git show "$($r):A-1/s-002.md"`.

## What "author" means

The author of a commit is the law that made the change: `S.C. 2019, c. 18` (Statutes of Canada 2019, chapter 18),
or a regulation such as `SOR/2019-84`, with an address ending `@laws-lois.invalid`, which
cannot exist, so `git blame` names the law. The committer is always `Lexifina`.

The evidence is the consolidation's own historical notes. Under each section Justice Canada lists the citations of the
provisions that enacted and amended it ("2019, c. 18, s. 2"). A changed section is credited to the law whose citation is
new in its note in the version from that day. A citation of the Act itself is not an amendment: the consolidators
re-cite the enacting Act whenever they rewrite a note. Three further rules, each labelled in the commit:

- a section that changed with no new citation in its note, on a day when exactly one law is new in the Act's notes, is
  credited to that law by date only (`Evidence: date only`);
- where a note gains citations of two laws on one day, or a section changed with no new citation on a day two laws are
  new, the change is committed by the publisher, `Justice Laws Website (Department of Justice Canada)`, labelled
  "credited to neither", with each law in a `Candidate:` trailer;
- a change no new citation explains at all (an editorial note, an institution removed without a citation) is the
  publisher's, labelled "no amending law cited".

The first version of each Act is the Act as amended up to then. The source has nothing earlier, so those lines are
credited to the publisher. The historical note at the foot of each file still names the laws that made them.

Blame credits whole lines. A subsection rewritten by one law and then touched by another is credited to the later one;
use `git log -p --word-diff` to see each law's words.

## How it is checked

Every version of each Act is read back from git, with `tools/on_date.py`, on the day it took effect, and compared with
the official text: file by file with the text parsed from the version, and word for word with all the words of the
version's text, read independently of the parser. `tools/test_repo.py` checks that the commands above work. The results
are in [`REPRODUCE.md`](REPRODUCE.md).

## Files

Each Act is a folder named by its consolidated number (`P-8.6/`, `A-1/`, `C-46/`). Each section is one file, named by
its number with the whole part padded to three digits: `P-8.6/s-007.md` is section 7, `P-8.6/s-004.01.md` section 4.01.
Inside a file:

- the headings of the Part, Division and subheadings that begin with the section are `##`, `###` and `####` lines;
- `Marginal note: ...` lines are the marginal notes;
- each subsection is one line; paragraphs, subparagraphs, clauses and definitions are list items, one level deeper for
  each level;
- the last block is the historical note: `History:` and one citation per line.

`intro.md` holds the title, chapter, assent and long title; `schedule-<n>.md` each schedule (one line per row of a
table), and `schedule-form-<n>.md` each form. A repealed section stays, as the consolidation prints it:
`[Repealed, 2015, c. 32, s. 6]`. Each folder's `README.md` lists its provisions and how often each changed.

## What it does not show

- Versions the sources do not hold: for P-8.6 and A-1 nothing before 2003-01-01 and 2002-12-31; for the other Acts
  nothing before their first version in the XML repository (2021 or later).
- The French text, which is equally authoritative. A change to the French version alone shows here only as a new
  citation marked `(F)` in a note.
- Which of two laws of the same day made a change (above).
- Amendments not yet in force, and the "Related Provisions" (transitional provisions of amending Acts) published
  separately: only the consolidated text of each version is recorded.
- Fee amounts adjusted automatically under the Service Fees Act, which the consolidated text does not show.
- For the Acts and regulations added in the breadth pass, any version but the current one, for now (see
  [`ACTS.md`](ACTS.md)); and anything not yet added.

## How it is built

`tools/build.py` writes the history of P-8.6 and A-1. Each further Act is added from the XML repository on top of
the published history by `tools/append.py` (with `tools/xmlsource.py`), with the same parser, the same rules and the
same commit messages (`tools/lawtext.py`), and checked by `tools/check_xml.py`; the method, the checks and
the decisions made by hand are in [`REPRODUCE.md`](REPRODUCE.md). [`corpus.json`](corpus.json) describes the corpus for tools that read several of Lexifina's law repositories.

## Licence

The text of the Acts is reproduced under the Reproduction of Federal Law Order, SI/97-5: "Anyone may, without charge or
request for permission, reproduce enactments and consolidations of enactments of the Government of Canada, and
decisions and reasons for decisions of federally-constituted courts and administrative tribunals, provided due diligence
is exercised in ensuring the accuracy of the materials reproduced and the reproduction is not represented as an
official version." Sources: the Justice Laws Website, https://laws-lois.justice.gc.ca, and Justice Canada's XML
repository of the consolidated Acts and regulations, https://github.com/justicecanada/laws-lois-xml, Department of
Justice Canada. The XML repository is published under the Open Government Licence - Canada: contains information
licensed under the Open Government Licence - Canada.

**This is not an official version,** and it is not made in affiliation with or with the endorsement of the Government
of Canada. The official consolidation is on the Justice Laws Website; for all purposes of interpreting and applying
the law, the Department of Justice refers users to the Acts as passed by Parliament and the regulations as registered.
The history, commit messages, tables and tools are released under [CC0 1.0](LICENSE).
