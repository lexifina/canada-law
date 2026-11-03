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
| 2 (2026-11-03) | `c1eb33542a50` | `0507465393c2` | I-3.3, L-2, I-21, C-44, I-2.5, E-15, P-21, C-5, C-34, B-3, F-11, H-6, E-5.6, C-8, F-7, C-42, P-4, T-13, C-52.6, O-3.01, C-36, C-11, S-26, I-1, C-24, N-22, F-27, C-29, P-1, E-2.01, C-15.1, A-0.6, A-1.3, A-1.5, A-10.1, A-10.4, A-10.5, A-10.6, A-10.7, A-11.2, A-11.3, A-11.31, A-11.4, A-11.44, A-11.5, A-11.7, A-11.9, A-11.91, A-12, A-13, A-13.4, A-13.7, A-14, A-16, A-17, A-17.5, A-18.5, A-18.8, A-2, A-2.4, A-3, A-3.7, A-5, A-6, A-8.8, A-9, B-0.5, B-1.5, B-1.7, B-2, B-3.4, B-3.6, B-4, B-5, B-5.3, B-5.5, B-6, B-6.3, B-6.4, B-8, B-8.05, B-8.2, B-8.3, B-8.4, B-8.5, B-9.01, B-9.6, B-9.8, B-9.81, B-9.82, B-9.83, B-9.84, B-9.85, B-9.851, B-9.852, B-9.853, B-9.854, B-9.855, B-9.856, B-9.857, B-9.858, B-9.859, B-9.8591, B-9.8592, B-9.8594, B-9.8595, B-9.86, B-9.87, B-9.88, B-9.89, B-9.9, C-0.2, C-0.3, C-0.4, C-0.5, C-0.6, C-0.7, C-1.2, C-1.3, C-1.4, C-1.5, C-1.6, C-1.65, C-1.66, C-1.68, C-1.7, C-1.8, C-1.9, C-10, C-10.1, C-10.10, C-10.11, C-10.13, C-10.14, C-10.15, C-10.2, C-10.3, C-10.4, C-10.5, C-10.52, C-10.54, C-10.541, C-10.55, C-10.56, C-10.58, C-10.6, C-10.65, C-10.7, C-11.001, C-11.01, C-11.1, C-11.2, C-11.4, C-11.7, C-12.3, C-13, C-13.4, C-13.7, C-14, C-15, C-15.2, C-15.21, C-15.31, C-16, C-16.5, C-16.8, C-17, C-17.15, C-17.2, C-17.3, C-17.6, C-17.8, C-18.1, C-18.3, C-18.4, C-18.7, C-19.1, C-19.3, C-2, C-20, C-21, C-21.1, C-21.3, C-21.8, C-22, C-22.4, C-23, C-23.05, C-23.2, C-23.25, C-23.3, C-23.4, C-23.7, C-24.2, C-24.5, C-25, C-25.2, C-26, C-27.2, C-27.4, C-27.5, C-27.55, C-27.6, C-27.7, C-28, C-28.5, C-28.51, C-29.4, C-29.7, C-3, C-3.4, C-3.43, C-3.45, C-3.5, C-3.55, C-3.6, C-3.65, C-3.7, C-3.75, C-3.8, C-30, C-31, C-31.3, C-31.4, C-31.5, C-31.6, C-31.7, C-31.8, C-33, C-33.3, C-33.6, C-33.7, C-34.6, C-35.3, C-36.4, C-36.45, C-36.6, C-36.65, C-36.7, C-36.75, C-36.78, C-38, C-38.7, C-4.4, C-4.8, C-41.01, C-41.5, C-43, C-44.6, C-45.2, C-45.5, C-45.6, C-45.75, C-45.9, C-47, C-47.4, C-49, C-49.6, C-49.8, C-5.2, C-5.5, C-5.7, C-5.8, C-5.85, C-5.9, C-50, C-51, C-52, C-53, C-54.011, C-55.5, C-6, C-6.1, C-6.10, C-6.15, C-6.16, C-6.18, C-6.19, C-6.2, C-6.3, C-6.4, C-6.42, C-6.45, C-6.48, C-6.5, C-6.6, C-6.65, C-6.7, C-6.85, C-6.87, C-6.9, C-6.94, C-7, C-7.2, C-7.3, C-7.5, C-7.7, C-7.75, C-7.8, C-7.9, C-7.95, C-8.3, C-8.4, C-8.5, C-8.8, D-0.5, D-1, D-1.3, D-1.5, D-1.55, D-1.57, D-1.59, D-1.6, D-1.65, D-2, D-2.5, D-2.8, D-3.8, D-3.9, D-4, E-0.6, E-0.7, E-0.8, E-0.9, E-0.93, E-1.3, E-1.4, E-1.45, E-1.5, E-1.6, E-1.7, E-10, E-11, E-12.5, E-13, E-13.7, E-14, E-14.1, E-15.5, E-16, E-17, E-18, E-18.5, E-19, E-20, E-21, E-21.5, E-22, E-22.7, E-23.01, E-3, E-3.1, E-4, E-4.5, E-4.56, E-4.6, E-5.401, E-5.8, E-6, E-6.2, E-6.4, E-8, E-9, E-9.5, F-1.2, F-1.4, F-10, F-10.6, F-11.1, F-11.2, F-11.3, F-11.4, F-11.6, F-11.64, F-11.65, F-11.66, F-11.67, F-11.7, F-11.73, F-11.75, F-11.8, F-11.9, F-12, F-13, F-14, F-15, F-17, F-2.2, F-2.27, F-2.7, F-21, F-22, F-24, F-25, F-27.3, F-27.5, F-28, F-29, F-29.2, F-29.4, F-29.6, F-3, F-3.3, F-30, F-30.2, F-30.4, F-31.2, F-31.4, F-31.46, F-31.5, F-31.55, F-31.6, F-31.7, F-32.5, F-4, F-5.5, F-5.8, F-7.3, F-7.33, F-7.35, F-7.38, F-7.5, F-7.7, F-7.8, F-8, F-8.2, F-8.4, F-8.6, F-9, G-10, G-11.2, G-11.4, G-11.55, G-11.6, G-2, G-2.3, G-2.5, G-3.3, G-3.7, G-3.8, G-4, G-5, G-5.3, G-5.7, G-6, G-7.4, G-7.6, G-9, H-0.3, H-0.5, H-1, H-2.7, H-2.71, H-3, H-3.2, H-3.3, H-3.4, H-3.5, H-3.7, H-3.76, H-3.77, H-3.8, H-4, H-5, H-5.4, H-5.67, H-5.7, H-5.8, I-11, I-11.8, I-14.6, I-14.7, I-14.85, I-15, I-16, I-17, I-17.05, I-17.3, I-18, I-18.1, I-19, I-19.3 | 482 | 482 | 482 | 29484 | 7824082 | 0 | 6/6 |
| 3 (2026-11-03) | `1536829b9dc6` | `0507465393c2` | I-19.7, I-19.8, I-2.75, I-20, I-20.4, I-20.6, I-20.7, I-20.8, I-21.5, I-21.8, I-3, I-3.31, I-3.5, I-3.51, I-3.52, I-3.53, I-3.54, I-3.55, I-4, I-5, I-5.3, I-6, I-6.7, I-7, I-7.2, I-7.4, I-7.7, I-7.85, I-7.88, I-8, I-9, I-9.2, I-9.8, J-0.3, J-0.7, J-0.8, J-0.9, J-1, J-1.5, J-2, J-2.3, J-2.5, K-0.5, K-0.65, K-0.7, K-0.8, K-6.5, K-9.5, L-1, L-10, L-4, L-4.3, L-5.2, L-5.8, L-6, L-6.2, L-6.4, L-6.5, L-6.7, L-7.3, L-7.5, L-7.7, L-8, L-8.5, M-0.1, M-0.15, M-0.2, M-0.23, M-0.25, M-0.3, M-0.5, M-0.53, M-0.54, M-0.55, M-0.56, M-0.58, M-0.6, M-0.8, M-1.5, M-10.01, M-12.01, M-12.8, M-13, M-13.4, M-13.6, M-2.1, M-3.2, M-5, M-5.8, M-6, M-7.01, M-7.6, M-8, M-8.6, M-9, N-0.5, N-1.4, N-10.5, N-10.7, N-11, N-11.2, N-11.5, N-12, N-13.6, N-14.01, N-14.2, N-14.3, N-14.4, N-15, N-15.8, N-16.2, N-16.4, N-16.45, N-16.5, N-16.56, N-16.6, N-16.62, N-16.65, N-16.7, N-16.75, N-16.77, N-16.8, N-16.85, N-17, N-2, N-2.5, N-20.8, N-20.9, N-21, N-22.4, N-22.6, N-22.7, N-23, N-23.3, N-23.6, N-23.7, N-23.8, N-24.2, N-24.5, N-26.3, N-26.5, N-27, N-27.05, N-27.1, N-27.3, N-27.5, N-27.7, N-28, N-28.1, N-28.3, N-28.5, N-28.6, N-28.7, N-28.75, N-28.8, N-3, N-3.4, N-3.7, N-4, N-4.2, N-4.3, N-4.5, N-4.6, N-5, N-7, N-7.6, N-8, N-8.6, N-9, N-9.1, N-9.2, N-9.6, O-1, O-2.4, O-2.8, O-4, O-5, O-7, O-8, O-8.3, O-9, O-9.1, O-9.2, O-9.3, O-9.5, P-0.2, P-1.3, P-10, P-11.1, P-12, P-13.2, P-13.4, P-13.6, P-14, P-14.2, P-14.6, P-14.8, P-15.3, P-15.4, P-15.44, P-15.5, P-15.6, P-15.7, P-15.8, P-16, P-16.5, P-16.8, P-16.81, P-17, P-18, P-19, P-19.3, P-19.32, P-19.45, P-19.6, P-20, P-24, P-24.501, P-24.8, P-25, P-25.2, P-25.6, P-25.7, P-26, P-27.5, P-28, P-29.5, P-29.7, P-29.71, P-31, P-31.4, P-31.5, P-31.55, P-31.6, P-31.65, P-31.7, P-31.8, P-32, P-33, P-33.01, P-33.3, P-33.35, P-33.4, P-33.6, P-34, P-35, P-36, P-38.2, P-38.8, P-4.2, P-4.3, P-4.4, P-4.6, P-4.7, P-6, P-6.7, P-7.01, P-8, P-8.3, P-9, Q-0.5, Q-1, Q-1.1, Q-1.8, R-1, R-10, R-10.6, R-11, R-12, R-12.1, R-2, R-3.2, R-3.25, R-3.3, R-4, R-4.2, R-4.4, R-4.5, R-4.6, R-4.7, R-4.9, R-5.3, R-5.4, R-5.44, R-5.5, R-5.6, R-7, R-7.2, R-7.3, R-7.36, R-7.4, R-7.7, R-8, R-8.2, R-8.5, R-8.55, R-8.6, R-9, S-1.04, S-1.1, S-1.3, S-1.5, S-10.01, S-10.1, S-10.2, S-10.4, S-10.9, S-11.5, S-12, S-12.55, S-12.8, S-13, S-13.5, S-14, S-14.3, S-14.5, S-15, S-15.2, S-15.3, S-15.34, S-15.36, S-15.4, S-15.6, S-15.7, S-15.8, S-15.9, S-16, S-18, S-19, S-19.6, S-2.5, S-2.6, S-20, S-21, S-21.5, S-22, S-22.5, S-22.7, S-23, S-23.5, S-23.7, S-24, S-25.5, S-27, S-3, S-4.3, S-6, S-6.6, S-6.7, S-6.9, S-7, S-7.2, S-8, S-8.3, S-8.35, S-8.36, S-8.4, S-8.5, S-8.7, S-8.9, S-9, T-1.3, T-1.5, T-1.6, T-1.7, T-10, T-10.2, T-10.3, T-10.4, T-10.43, T-10.47, T-10.48, T-10.49, T-10.5, T-10.6, T-11, T-11.1, T-11.2, T-11.3, T-11.5, T-14, T-15, T-16, T-18, T-18.5, T-19.01, T-19.8, T-2, T-21.5, T-3, T-3.4, T-4.2, T-6.1, T-7, U-0.4, U-0.5, U-0.6, U-1.5, U-2, U-2.2, U-2.4, U-3, U-3.2, U-3.5, U-3.7, V-1, V-1.3, V-1.4, V-1.5, V-1.6, V-1.8, V-2, V-3, W-0.8, W-1, W-10, W-11, W-11.2, W-11.3, W-11.4, W-11.5, W-11.6, W-11.8, W-12.3, W-2.5, W-3, W-4, W-5, W-6, W-6.2, W-6.4, W-6.5, W-6.75, W-6.8, W-7.8, W-8.5, W-9, Y-0.2, Y-0.6, Y-1, Y-1.5, Y-2, Y-2.01, Y-2.2, Y-3, Y-4, Y-4.3, Y-4.6, Z-0.91, Z-0.98, Z-01, Z-02, Z-040, Z-041 | 454 | 454 | 454 | 15897 | 3504066 | 0 | 6/6 |
| 4 (2026-11-03) | `43846d7d0d31` | `0507465393c2` | SI-2000-100, SI-2000-101, SI-2000-102, SI-2000-103, SI-2000-104, SI-2000-111, SI-2000-16, SI-2000-23, SI-2000-33, SI-2000-39, SI-2000-53, SI-2000-54, SI-2000-69, SI-2000-77, SI-2000-82, SI-2000-84, SI-2000-90, SI-2000-99, SI-2001-1, SI-2001-109, SI-2001-120, SI-2001-23, SI-2001-27, SI-2001-28, SI-2001-45, SI-2001-47, SI-2001-50, SI-2001-51, SI-2001-60, SI-2001-68, SI-2001-69, SI-2001-72, SI-2001-73, SI-2001-74, SI-2001-81, SI-2001-93, SI-2001-96, SI-2001-99, SI-2002-1, SI-2002-10, SI-2002-123, SI-2002-142, SI-2002-154, SI-2002-160, SI-2002-46, SI-2002-58, SI-2002-60, SI-2002-61, SI-2002-62, SI-2002-65, SI-2002-75, SI-2002-9, SI-2003-103, SI-2003-107, SI-2003-112, SI-2003-119, SI-2003-122, SI-2003-124, SI-2003-130, SI-2003-133, SI-2003-134, SI-2003-146, SI-2003-148, SI-2003-149, SI-2003-155, SI-2003-156, SI-2003-159, SI-2003-164, SI-2003-166, SI-2003-171, SI-2003-173, SI-2003-188, SI-2003-2, SI-2003-202, SI-2003-203, SI-2003-204, SI-2003-208, SI-2003-209, SI-2003-210, SI-2003-214, SI-2003-215, SI-2003-216, SI-2003-217, SI-2003-221, SI-2003-222, SI-2003-226, SI-2003-228, SI-2003-229, SI-2003-230, SI-2003-231, SI-2003-232, SI-2003-233, SI-2003-240, SI-2003-244, SI-2003-36, SI-2003-38, SI-2003-4, SI-2003-42, SI-2003-5, SI-2003-58, SI-2003-6, SI-2003-93, SI-2004-100, SI-2004-101, SI-2004-102, SI-2004-103, SI-2004-109, SI-2004-112, SI-2004-122, SI-2004-123, SI-2004-13, SI-2004-132, SI-2004-133, SI-2004-134, SI-2004-135, SI-2004-136, SI-2004-138, SI-2004-14, SI-2004-148, SI-2004-153, SI-2004-155, SI-2004-16, SI-2004-164, SI-2004-34, SI-2004-35, SI-2004-36, SI-2004-41, SI-2004-43, SI-2004-44, SI-2004-48, SI-2004-55, SI-2004-6, SI-2004-7, SI-2004-8, SI-2004-86, SI-2004-87, SI-2004-88, SI-2004-90, SI-2005-106, SI-2005-113, SI-2005-114, SI-2005-115, SI-2005-118, SI-2005-120, SI-2005-124, SI-2005-125, SI-2005-127, SI-2005-128, SI-2005-17, SI-2005-2, SI-2005-48, SI-2005-50, SI-2005-55, SI-2005-59, SI-2005-65, SI-2005-71, SI-2005-72, SI-2005-73, SI-2005-8, SI-2005-83, SI-2005-86, SI-2005-87, SI-2005-9, SI-2005-91, SI-2006-100, SI-2006-101, SI-2006-109, SI-2006-11, SI-2006-110, SI-2006-121, SI-2006-122, SI-2006-123, SI-2006-124, SI-2006-128, SI-2006-133, SI-2006-134, SI-2006-135, SI-2006-137, SI-2006-141, SI-2006-142, SI-2006-16, SI-2006-17, SI-2006-18, SI-2006-22, SI-2006-23, SI-2006-26, SI-2006-27, SI-2006-28, SI-2006-29, SI-2006-30, SI-2006-31, SI-2006-32, SI-2006-37, SI-2006-38, SI-2006-39, SI-2006-4, SI-2006-40, SI-2006-45, SI-2006-46, SI-2006-47, SI-2006-51, SI-2006-60, SI-2006-61, SI-2006-62, SI-2006-63, SI-2006-64, SI-2006-69, SI-2006-71, SI-2006-72, SI-2006-73, SI-2006-74, SI-2006-75, SI-2006-76, SI-2006-77, SI-2006-79, SI-2006-80, SI-2006-85, SI-2006-89, SI-2006-97, SI-2006-98, SI-2007-101, SI-2007-102, SI-2007-103, SI-2007-115, SI-2007-13, SI-2007-14, SI-2007-31, SI-2007-37, SI-2007-57, SI-2007-61, SI-2007-68, SI-2007-69, SI-2007-80, SI-2007-87, SI-2008-101, SI-2008-102, SI-2008-103, SI-2008-104, SI-2008-136, SI-2008-143, SI-2008-148, SI-2008-15, SI-2008-16, SI-2008-20, SI-2008-23, SI-2008-25, SI-2008-26, SI-2008-27, SI-2008-28, SI-2008-53, SI-2008-55, SI-2008-69, SI-2008-70, SI-2008-95, SI-2008-99, SI-2009-103, SI-2009-104, SI-2009-110, SI-2009-20, SI-2009-22, SI-2009-23, SI-2009-24, SI-2009-3, SI-2009-61, SI-2009-73, SI-2009-87, SI-2009-94, SI-2009-95, SI-2010-10, SI-2010-13, SI-2010-14, SI-2010-18, SI-2010-42, SI-2010-45, SI-2010-46, SI-2010-54, SI-2010-76, SI-2010-81, SI-2010-83, SI-2010-84, SI-2010-90, SI-2011-100, SI-2011-109, SI-2011-11, SI-2011-111, SI-2011-14, SI-2011-20, SI-2011-48, SI-2011-56, SI-2011-58, SI-2011-59, SI-2011-60, SI-2011-66, SI-2011-67, SI-2011-68, SI-2011-69, SI-2011-77, SI-2011-78, SI-2011-89, SI-2011-9, SI-2011-90, SI-2011-91, SI-2011-92, SI-2011-93, SI-2011-94, SI-2011-95, SI-2011-96, SI-2012-103, SI-2012-12, SI-2012-16, SI-2012-20, SI-2012-23, SI-2012-24, SI-2012-25, SI-2012-26, SI-2012-27, SI-2012-30, SI-2012-39, SI-2012-43, SI-2012-45, SI-2012-46, SI-2012-50, SI-2012-58, SI-2012-59, SI-2012-60, SI-2012-64, SI-2012-7, SI-2012-72, SI-2012-76, SI-2012-78, SI-2012-80, SI-2012-81, SI-2012-82, SI-2012-83, SI-2012-9, SI-2013-1, SI-2013-102, SI-2013-106, SI-2013-109, SI-2013-110, SI-2013-114, SI-2013-125, SI-2013-129, SI-2013-27, SI-2013-28, SI-2013-29, SI-2013-3, SI-2013-30, SI-2013-40, SI-2013-41, SI-2013-43, SI-2013-51, SI-2013-53, SI-2013-56, SI-2013-59, SI-2013-62, SI-2013-63, SI-2013-64, SI-2013-7, SI-2013-87, SI-2013-90, SI-2013-96, SI-2014-109, SI-2014-11, SI-2014-13, SI-2014-15, SI-2014-19, SI-2014-21, SI-2014-27, SI-2014-30, SI-2014-35, SI-2014-36, SI-2014-37, SI-2014-38, SI-2014-39, SI-2014-41, SI-2014-54, SI-2014-56, SI-2014-63, SI-2014-67, SI-2014-73, SI-2014-76, SI-2014-89, SI-2015-100, SI-2015-101, SI-2015-102, SI-2015-103, SI-2015-104, SI-2015-105, SI-2015-106, SI-2015-107, SI-2015-108, SI-2015-109, SI-2015-110, SI-2015-111, SI-2015-112, SI-2015-114, SI-2015-13, SI-2015-15, SI-2015-2, SI-2015-24, SI-2015-3, SI-2015-35, SI-2015-39, SI-2015-45, SI-2015-52, SI-2015-62, SI-2015-72, SI-2015-74, SI-2015-81, SI-2015-93, SI-2015-94, SI-2015-95, SI-2015-96, SI-2015-97, SI-2015-98 | 416 | 416 | 416 | 1318 | 590792 | 0 | 6/6 |
| 5 (2026-11-03) | `ef84b44af55f` | `0507465393c2` | C.R.C.,_c._10, C.R.C.,_c._100, C.R.C.,_c._101, C.R.C.,_c._1013, C.R.C.,_c._1015, C.R.C.,_c._102, C.R.C.,_c._1021, C.R.C.,_c._1022, C.R.C.,_c._1023, C.R.C.,_c._1026, C.R.C.,_c._1027, C.R.C.,_c._103, C.R.C.,_c._1033, C.R.C.,_c._1035, C.R.C.,_c._1036, C.R.C.,_c._104, C.R.C.,_c._1041, C.R.C.,_c._1044, C.R.C.,_c._1045, C.R.C.,_c._1046, C.R.C.,_c._1048, C.R.C.,_c._1049, C.R.C.,_c._105, C.R.C.,_c._1050, C.R.C.,_c._1055, C.R.C.,_c._1058, C.R.C.,_c._106, C.R.C.,_c._109, C.R.C.,_c._1105, C.R.C.,_c._1107, C.R.C.,_c._111, C.R.C.,_c._1111, C.R.C.,_c._1112, C.R.C.,_c._1114, C.R.C.,_c._112, C.R.C.,_c._1120, C.R.C.,_c._1126, C.R.C.,_c._113, C.R.C.,_c._1130, C.R.C.,_c._1134, C.R.C.,_c._114, C.R.C.,_c._1145, C.R.C.,_c._1146, C.R.C.,_c._1147, C.R.C.,_c._1148, C.R.C.,_c._115, C.R.C.,_c._1151, C.R.C.,_c._1152, C.R.C.,_c._116, C.R.C.,_c._117, C.R.C.,_c._1171, C.R.C.,_c._118, C.R.C.,_c._1182, C.R.C.,_c._1183, C.R.C.,_c._1185, C.R.C.,_c._1195, C.R.C.,_c._121, C.R.C.,_c._122, C.R.C.,_c._1225, C.R.C.,_c._123, C.R.C.,_c._1231, C.R.C.,_c._1232, C.R.C.,_c._1235, C.R.C.,_c._1236, C.R.C.,_c._1238, C.R.C.,_c._1239, C.R.C.,_c._1240, C.R.C.,_c._1241, C.R.C.,_c._1242, C.R.C.,_c._1244, C.R.C.,_c._1245, C.R.C.,_c._1246, C.R.C.,_c._1247, C.R.C.,_c._125, C.R.C.,_c._1253, C.R.C.,_c._1254, C.R.C.,_c._1264, C.R.C.,_c._1266, C.R.C.,_c._1268, C.R.C.,_c._1270, C.R.C.,_c._1274, C.R.C.,_c._128, C.R.C.,_c._1283, C.R.C.,_c._1288, C.R.C.,_c._129, C.R.C.,_c._1292, C.R.C.,_c._1295, C.R.C.,_c._1296, C.R.C.,_c._1298, C.R.C.,_c._130, C.R.C.,_c._1301, C.R.C.,_c._1302, C.R.C.,_c._1303, C.R.C.,_c._1304, C.R.C.,_c._1305, C.R.C.,_c._1306, C.R.C.,_c._1307, C.R.C.,_c._1308, C.R.C.,_c._1309, C.R.C.,_c._1310, C.R.C.,_c._1311, C.R.C.,_c._1312, C.R.C.,_c._1314, C.R.C.,_c._1315, C.R.C.,_c._1316, C.R.C.,_c._1317, C.R.C.,_c._1318, C.R.C.,_c._1319, C.R.C.,_c._1320, C.R.C.,_c._1321, C.R.C.,_c._1326, C.R.C.,_c._1328, C.R.C.,_c._133, C.R.C.,_c._1330, C.R.C.,_c._1331, C.R.C.,_c._1333, C.R.C.,_c._1335, C.R.C.,_c._1336, C.R.C.,_c._134, C.R.C.,_c._1341, C.R.C.,_c._1342, C.R.C.,_c._135, C.R.C.,_c._1352, C.R.C.,_c._1354, C.R.C.,_c._1355, C.R.C.,_c._1356, C.R.C.,_c._1357, C.R.C.,_c._1358, C.R.C.,_c._1359, C.R.C.,_c._1360, C.R.C.,_c._1365, C.R.C.,_c._1367, C.R.C.,_c._1368, C.R.C.,_c._1370, C.R.C.,_c._1375, C.R.C.,_c._1376, C.R.C.,_c._1377, C.R.C.,_c._1378, C.R.C.,_c._1379, C.R.C.,_c._1380, C.R.C.,_c._1381, C.R.C.,_c._1382, C.R.C.,_c._1384, C.R.C.,_c._1385, C.R.C.,_c._1386, C.R.C.,_c._1387, C.R.C.,_c._1388, C.R.C.,_c._1390, C.R.C.,_c._1392, C.R.C.,_c._1393, C.R.C.,_c._1394, C.R.C.,_c._14, C.R.C.,_c._140, C.R.C.,_c._1400, C.R.C.,_c._1403, C.R.C.,_c._1404, C.R.C.,_c._1405, C.R.C.,_c._1407, C.R.C.,_c._1418, C.R.C.,_c._142, C.R.C.,_c._1422, C.R.C.,_c._1424, C.R.C.,_c._1425, C.R.C.,_c._1427, C.R.C.,_c._1429, C.R.C.,_c._1430, C.R.C.,_c._1431, C.R.C.,_c._1432, C.R.C.,_c._1435, C.R.C.,_c._1436, C.R.C.,_c._1440, C.R.C.,_c._1441, C.R.C.,_c._1442, C.R.C.,_c._1448, C.R.C.,_c._1458, C.R.C.,_c._1465, C.R.C.,_c._1467, C.R.C.,_c._147, C.R.C.,_c._1472, C.R.C.,_c._1479, C.R.C.,_c._148, C.R.C.,_c._1480, C.R.C.,_c._1482, C.R.C.,_c._1486, C.R.C.,_c._1487, C.R.C.,_c._149, C.R.C.,_c._1494, C.R.C.,_c._1495, C.R.C.,_c._1496, C.R.C.,_c._1498, C.R.C.,_c._15, C.R.C.,_c._150, C.R.C.,_c._1501, C.R.C.,_c._1504, C.R.C.,_c._1509, C.R.C.,_c._1511, C.R.C.,_c._1516, C.R.C.,_c._1517, C.R.C.,_c._1518, C.R.C.,_c._152, C.R.C.,_c._1520, C.R.C.,_c._1521, C.R.C.,_c._1522, C.R.C.,_c._1523, C.R.C.,_c._1524, C.R.C.,_c._1525, C.R.C.,_c._1526, C.R.C.,_c._1527, C.R.C.,_c._1530, C.R.C.,_c._1533, C.R.C.,_c._1535, C.R.C.,_c._1537, C.R.C.,_c._1539, C.R.C.,_c._154, C.R.C.,_c._1540, C.R.C.,_c._1541, C.R.C.,_c._1547, C.R.C.,_c._1548, C.R.C.,_c._1549, C.R.C.,_c._155, C.R.C.,_c._1550, C.R.C.,_c._1551, C.R.C.,_c._1552, C.R.C.,_c._1560, C.R.C.,_c._1561, C.R.C.,_c._1563, C.R.C.,_c._1564, C.R.C.,_c._1566, C.R.C.,_c._1575, C.R.C.,_c._1578, C.R.C.,_c._1579, C.R.C.,_c._1581, C.R.C.,_c._1582, C.R.C.,_c._1584, C.R.C.,_c._1585, C.R.C.,_c._1586, C.R.C.,_c._1587, C.R.C.,_c._1588, C.R.C.,_c._1590, C.R.C.,_c._1593, C.R.C.,_c._1594, C.R.C.,_c._1596, C.R.C.,_c._1597, C.R.C.,_c._1598, C.R.C.,_c._1599, C.R.C.,_c._16, C.R.C.,_c._160, C.R.C.,_c._1600, C.R.C.,_c._1601, C.R.C.,_c._1602, C.R.C.,_c._1603, C.R.C.,_c._1604, C.R.C.,_c._1605, C.R.C.,_c._1607, C.R.C.,_c._1610, C.R.C.,_c._1611, C.R.C.,_c._162, C.R.C.,_c._1621, C.R.C.,_c._1622, C.R.C.,_c._1623, C.R.C.,_c._164, C.R.C.,_c._165, C.R.C.,_c._166, C.R.C.,_c._167, C.R.C.,_c._168, C.R.C.,_c._169, C.R.C.,_c._170, C.R.C.,_c._176, C.R.C.,_c._177, C.R.C.,_c._178, C.R.C.,_c._179, C.R.C.,_c._180, C.R.C.,_c._181, C.R.C.,_c._182, C.R.C.,_c._183, C.R.C.,_c._185, C.R.C.,_c._186, C.R.C.,_c._194, C.R.C.,_c._19552561, C.R.C.,_c._198, C.R.C.,_c._201, C.R.C.,_c._207, C.R.C.,_c._208, C.R.C.,_c._209, C.R.C.,_c._210, C.R.C.,_c._211, C.R.C.,_c._212, C.R.C.,_c._213, C.R.C.,_c._215, C.R.C.,_c._216, C.R.C.,_c._217, C.R.C.,_c._218, C.R.C.,_c._220, C.R.C.,_c._221, C.R.C.,_c._223, C.R.C.,_c._224, C.R.C.,_c._225, C.R.C.,_c._226, C.R.C.,_c._228, C.R.C.,_c._229, C.R.C.,_c._232, C.R.C.,_c._233, C.R.C.,_c._234, C.R.C.,_c._235, C.R.C.,_c._236, C.R.C.,_c._237, C.R.C.,_c._238, C.R.C.,_c._239, C.R.C.,_c._240, C.R.C.,_c._243, C.R.C.,_c._258, C.R.C.,_c._259, C.R.C.,_c._260, C.R.C.,_c._268, C.R.C.,_c._269, C.R.C.,_c._270, C.R.C.,_c._271, C.R.C.,_c._272, C.R.C.,_c._273, C.R.C.,_c._274, C.R.C.,_c._275, C.R.C.,_c._276, C.R.C.,_c._277, C.R.C.,_c._280, C.R.C.,_c._281, C.R.C.,_c._284, C.R.C.,_c._285, C.R.C.,_c._287, C.R.C.,_c._289, C.R.C.,_c._290, C.R.C.,_c._291, C.R.C.,_c._296, C.R.C.,_c._316, C.R.C.,_c._317, C.R.C.,_c._319, C.R.C.,_c._320, C.R.C.,_c._322, C.R.C.,_c._332, C.R.C.,_c._334, C.R.C.,_c._335, C.R.C.,_c._340, C.R.C.,_c._342, C.R.C.,_c._343, C.R.C.,_c._345, C.R.C.,_c._347, C.R.C.,_c._348, C.R.C.,_c._349, C.R.C.,_c._353, C.R.C.,_c._354, C.R.C.,_c._355, C.R.C.,_c._356, C.R.C.,_c._368, C.R.C.,_c._375, C.R.C.,_c._378, C.R.C.,_c._385, C.R.C.,_c._386, C.R.C.,_c._390, C.R.C.,_c._391, C.R.C.,_c._394, C.R.C.,_c._395, C.R.C.,_c._396, C.R.C.,_c._397, C.R.C.,_c._398, C.R.C.,_c._399, C.R.C.,_c._4, C.R.C.,_c._401, C.R.C.,_c._407, C.R.C.,_c._416, C.R.C.,_c._417, C.R.C.,_c._418, C.R.C.,_c._421, C.R.C.,_c._424, C.R.C.,_c._425, C.R.C.,_c._427, C.R.C.,_c._430, C.R.C.,_c._440, C.R.C.,_c._446, C.R.C.,_c._449, C.R.C.,_c._450, C.R.C.,_c._478, C.R.C.,_c._487, C.R.C.,_c._489, C.R.C.,_c._516, C.R.C.,_c._517, C.R.C.,_c._522, C.R.C.,_c._533, C.R.C.,_c._535, C.R.C.,_c._549, C.R.C.,_c._554, C.R.C.,_c._565, C.R.C.,_c._566, C.R.C.,_c._571, C.R.C.,_c._590, C.R.C.,_c._591, C.R.C.,_c._594, C.R.C.,_c._598, C.R.C.,_c._599, C.R.C.,_c._604, C.R.C.,_c._606, C.R.C.,_c._609, C.R.C.,_c._611, C.R.C.,_c._612, C.R.C.,_c._613, C.R.C.,_c._616, C.R.C.,_c._623, C.R.C.,_c._625, C.R.C.,_c._632, C.R.C.,_c._640, C.R.C.,_c._645, C.R.C.,_c._648, C.R.C.,_c._654, C.R.C.,_c._657, C.R.C.,_c._658, C.R.C.,_c._659, C.R.C.,_c._660, C.R.C.,_c._664, C.R.C.,_c._666, C.R.C.,_c._669, C.R.C.,_c._670, C.R.C.,_c._671, C.R.C.,_c._672, C.R.C.,_c._675, C.R.C.,_c._676, C.R.C.,_c._679, C.R.C.,_c._681, C.R.C.,_c._682, C.R.C.,_c._686, C.R.C.,_c._687, C.R.C.,_c._688, C.R.C.,_c._689, C.R.C.,_c._690, C.R.C.,_c._691, C.R.C.,_c._692, C.R.C.,_c._698, C.R.C.,_c._707, C.R.C.,_c._708, C.R.C.,_c._709, C.R.C.,_c._710, C.R.C.,_c._712, C.R.C.,_c._713, C.R.C.,_c._716, C.R.C.,_c._719, C.R.C.,_c._721, C.R.C.,_c._722, C.R.C.,_c._730, C.R.C.,_c._731, C.R.C.,_c._732, C.R.C.,_c._734, C.R.C.,_c._735, C.R.C.,_c._736, C.R.C.,_c._739, C.R.C.,_c._743, C.R.C.,_c._75, C.R.C.,_c._751, C.R.C.,_c._752, C.R.C.,_c._754, C.R.C.,_c._755, C.R.C.,_c._756, C.R.C.,_c._757, C.R.C.,_c._758, C.R.C.,_c._759, C.R.C.,_c._762, C.R.C.,_c._763, C.R.C.,_c._767, C.R.C.,_c._768, C.R.C.,_c._77, C.R.C.,_c._770, C.R.C.,_c._771, C.R.C.,_c._772, C.R.C.,_c._773, C.R.C.,_c._778, C.R.C.,_c._78, C.R.C.,_c._780, C.R.C.,_c._785, C.R.C.,_c._786, C.R.C.,_c._79, C.R.C.,_c._790, C.R.C.,_c._791, C.R.C.,_c._793, C.R.C.,_c._794, C.R.C.,_c._795, C.R.C.,_c._797, C.R.C.,_c._799, C.R.C.,_c._80, C.R.C.,_c._802, C.R.C.,_c._803, C.R.C.,_c._81, C.R.C.,_c._811, C.R.C.,_c._812 | 489 | 489 | 489 | 3656 | 1406383 | 0 | 6/6 |
| 6 (2026-11-03) | `f164f99437ef` | `0507465393c2` | C.R.C.,_c._818, C.R.C.,_c._82, C.R.C.,_c._828, C.R.C.,_c._829, C.R.C.,_c._83, C.R.C.,_c._836, C.R.C.,_c._837, C.R.C.,_c._84, C.R.C.,_c._847, C.R.C.,_c._854, C.R.C.,_c._864, C.R.C.,_c._868, C.R.C.,_c._869, C.R.C.,_c._87, C.R.C.,_c._879, C.R.C.,_c._88, C.R.C.,_c._880, C.R.C.,_c._886, C.R.C.,_c._887, C.R.C.,_c._889, C.R.C.,_c._89, C.R.C.,_c._890, C.R.C.,_c._90, C.R.C.,_c._91, C.R.C.,_c._910, C.R.C.,_c._911, C.R.C.,_c._915, C.R.C.,_c._92, C.R.C.,_c._923, C.R.C.,_c._924, C.R.C.,_c._927, C.R.C.,_c._929, C.R.C.,_c._93, C.R.C.,_c._930, C.R.C.,_c._931, C.R.C.,_c._932, C.R.C.,_c._933, C.R.C.,_c._934, C.R.C.,_c._945, C.R.C.,_c._946, C.R.C.,_c._948, C.R.C.,_c._949, C.R.C.,_c._95, C.R.C.,_c._950, C.R.C.,_c._952, C.R.C.,_c._953, C.R.C.,_c._954, C.R.C.,_c._956, C.R.C.,_c._957, C.R.C.,_c._959, C.R.C.,_c._96, C.R.C.,_c._960, C.R.C.,_c._961, C.R.C.,_c._966, C.R.C.,_c._967, C.R.C.,_c._968, C.R.C.,_c._969, C.R.C.,_c._970, C.R.C.,_c._971, C.R.C.,_c._972, C.R.C.,_c._98, C.R.C.,_c._982, C.R.C.,_c._984, C.R.C.,_c._985, C.R.C.,_c._986, C.R.C.,_c._987, C.R.C.,_c._99, C.R.C.,_c._990, C.R.C.,_c._991, C.R.C.,_c._992, SI-2015-99, SI-2016-18, SI-2016-19, SI-2016-20, SI-2016-21, SI-2016-29, SI-2016-31, SI-2016-32, SI-2016-34, SI-2016-39, SI-2016-40, SI-2016-43, SI-2016-44, SI-2016-46, SI-2016-48, SI-2016-49, SI-2016-55, SI-2016-63, SI-2016-71, SI-2016-8, SI-2017-10, SI-2017-11, SI-2017-12, SI-2017-15, SI-2017-17, SI-2017-24, SI-2017-25, SI-2017-29, SI-2017-30, SI-2017-35, SI-2017-36, SI-2017-4, SI-2017-40, SI-2017-41, SI-2017-45, SI-2017-46, SI-2017-49, SI-2017-5, SI-2017-50, SI-2017-55, SI-2017-56, SI-2017-6, SI-2017-61, SI-2017-64, SI-2017-7, SI-2017-71, SI-2017-72, SI-2017-74, SI-2017-75, SI-2017-76, SI-2017-77, SI-2017-78, SI-2017-79, SI-2017-8, SI-2017-9, SI-2018-102, SI-2018-103, SI-2018-104, SI-2018-105, SI-2018-106, SI-2018-107, SI-2018-112, SI-2018-13, SI-2018-14, SI-2018-16, SI-2018-17, SI-2018-20, SI-2018-30, SI-2018-33, SI-2018-34, SI-2018-40, SI-2018-43, SI-2018-44, SI-2018-51, SI-2018-55, SI-2018-58, SI-2018-59, SI-2018-60, SI-2018-61, SI-2018-62, SI-2018-63, SI-2018-66, SI-2018-67, SI-2018-68, SI-2018-69, SI-2018-70, SI-2018-71, SI-2018-72, SI-2018-73, SI-2018-74, SI-2018-75, SI-2018-76, SI-2018-77, SI-2018-78, SI-2018-79, SI-2018-80, SI-2018-86, SI-2018-88, SI-2018-89, SI-2018-90, SI-2018-91, SI-2019-10, SI-2019-105, SI-2019-107, SI-2019-108, SI-2019-114, SI-2019-115, SI-2019-116, SI-2019-117, SI-2019-118, SI-2019-119, SI-2019-12, SI-2019-120, SI-2019-121, SI-2019-122, SI-2019-123, SI-2019-124, SI-2019-125, SI-2019-126, SI-2019-127, SI-2019-128, SI-2019-129, SI-2019-13, SI-2019-130, SI-2019-131, SI-2019-132, SI-2019-133, SI-2019-134, SI-2019-22, SI-2019-23, SI-2019-24, SI-2019-29, SI-2019-33, SI-2019-51, SI-2019-52, SI-2019-56, SI-2019-57, SI-2019-59, SI-2019-60, SI-2019-61, SI-2019-63, SI-2019-65, SI-2019-66, SI-2019-68, SI-2019-69, SI-2019-72, SI-2019-75, SI-2019-89, SI-2020-12, SI-2020-23, SI-2020-24, SI-2020-25, SI-2020-28, SI-2020-29, SI-2020-30, SI-2020-37, SI-2020-41, SI-2020-50, SI-2020-53, SI-2020-54, SI-2020-61, SI-2020-65, SI-2020-67, SI-2020-70, SI-2020-77, SI-2021-17, SI-2021-18, SI-2021-19, SI-2021-2, SI-2021-20, SI-2021-21, SI-2021-22, SI-2021-23, SI-2021-24, SI-2021-32, SI-2021-33, SI-2021-37, SI-2021-38, SI-2021-41, SI-2021-43, SI-2021-44, SI-2021-45, SI-2021-49, SI-2021-5, SI-2021-50, SI-2021-51, SI-2021-58, SI-2021-59, SI-2021-6, SI-2021-75, SI-2021-76, SI-2021-77, SI-2021-78, SI-2021-79, SI-2021-8, SI-2021-80, SI-2021-81, SI-2021-82, SI-2021-83, SI-2021-84, SI-2021-85, SI-2021-86, SI-2021-87, SI-2021-88, SI-2021-89, SI-2021-9, SI-2021-90, SI-2021-91, SI-2021-92, SI-2021-93, SI-2021-94, SI-2021-95, SI-2021-96, SI-2021-97, SI-2021-98, SI-2022-10, SI-2022-11, SI-2022-18, SI-2022-2, SI-2022-21, SI-2022-23, SI-2022-25, SI-2022-26, SI-2022-27, SI-2022-3, SI-2022-31, SI-2022-32, SI-2022-34, SI-2022-4, SI-2022-42, SI-2022-43, SI-2022-47, SI-2022-5, SI-2022-52, SI-2022-53, SI-2022-6, SI-2022-7, SI-2023-13, SI-2023-15, SI-2023-16, SI-2023-18, SI-2023-23, SI-2023-24, SI-2023-35, SI-2023-36, SI-2023-37, SI-2023-38, SI-2023-39, SI-2023-40, SI-2023-41, SI-2023-42, SI-2023-43, SI-2023-44, SI-2023-45, SI-2023-46, SI-2023-47, SI-2023-48, SI-2023-49, SI-2023-5, SI-2023-50, SI-2023-51, SI-2023-52, SI-2023-53, SI-2023-54, SI-2023-57, SI-2023-6, SI-2023-63, SI-2023-66, SI-2023-67, SI-2023-7, SI-2023-71, SI-2023-72, SI-2023-73, SI-2023-74, SI-2023-75, SI-2023-76, SI-2024-1, SI-2024-14, SI-2024-15, SI-2024-17, SI-2024-18, SI-2024-19, SI-2024-20, SI-2024-22, SI-2024-29, SI-2024-34, SI-2024-35, SI-2024-36, SI-2024-4, SI-2024-47, SI-2024-48, SI-2024-5, SI-2024-51, SI-2024-52, SI-2024-57, SI-2024-58, SI-2024-6, SI-2024-61, SI-2024-62, SI-2024-65, SI-2024-66, SI-2024-67, SI-2024-7, SI-2025-103, SI-2025-109, SI-2025-110, SI-2025-111, SI-2025-113, SI-2025-114, SI-2025-115, SI-2025-116, SI-2025-117, SI-2025-118, SI-2025-119, SI-2025-120, SI-2025-121, SI-2025-122, SI-2025-123, SI-2025-124, SI-2025-125, SI-2025-126, SI-2025-127, SI-2025-13, SI-2025-130, SI-2025-131, SI-2025-132, SI-2025-133, SI-2025-14, SI-2025-15, SI-2025-16, SI-2025-17, SI-2025-18, SI-2025-19, SI-2025-20, SI-2025-31, SI-2025-32, SI-2025-33, SI-2025-34, SI-2025-35, SI-2025-36, SI-2025-37, SI-2025-38, SI-2025-39, SI-2025-40, SI-2025-41, SI-2025-42, SI-2025-43, SI-2025-44, SI-2025-45, SI-2025-46, SI-2025-47, SI-2025-48, SI-2025-49, SI-2025-50, SI-2025-51, SI-2025-52, SI-2025-53, SI-2025-54, SI-2025-55, SI-2025-60, SI-2025-7, SI-2025-74, SI-2025-75, SI-2025-76, SI-2025-77, SI-2025-78, SI-2025-79, SI-2025-80, SI-2025-81, SI-2025-82, SI-2025-83, SI-2025-84, SI-2025-85, SI-2025-89, SI-2025-90, SI-2025-91, SI-2025-92, SI-2025-96, SI-2026-1, SI-2026-10, SI-2026-11, SI-2026-12, SI-2026-13, SI-2026-15, SI-2026-16, SI-2026-17, SI-2026-2, SI-2026-22, SI-2026-23, SI-2026-27, SI-2026-28, SI-2026-29, SI-2026-3, SI-2026-34, SI-2026-40, SI-2026-41, SI-2026-42, SI-2026-43, SI-2026-5, SI-2026-50, SI-2026-52, SI-2026-55, SI-2026-57, SI-2026-7, SI-2026-8, SI-2026-9, SI-45-7421, SI-76-31, SI-77-174, SI-78-162, SI-78-165, SI-78-179, SI-78-57, SI-78-65, SI-78-75, SI-79-10, SI-79-19, SI-79-2, SI-79-39, SI-79-40, SI-79-7, SI-79-72, SI-79-73, SI-80-108, SI-80-11, SI-80-114, SI-80-117, SI-80-125, SI-80-127 | 499 | 499 | 499 | 1920 | 1147966 | 0 | 6/6 |

Batch 1:

- C-46 (Criminal Code): 36 versions, 2020-07-01 to 2026-07-18; 30 from consolidations in the XML repository, 6 rebuilt between two of them from the provisions' in-force days (8 commits carry Dated-by).
- Commits: 1 first version (publisher), 38 by 32 amending laws, 9 credited to neither of two laws (Candidate trailers), 1 with no amending law cited (s. 183, 2026, publisher).
- Two versions were re-issued by the publisher with a different text on the same day (2025-01-01, 2026-03-26); the later text is used.
- Checks on the appended repository: every version file by file, 0 mismatches (59,714 files); every consolidation word for word, 0 mismatches (14,582,505 words); P-8.6 and A-1 rechecked against their point-in-time pages, 141 versions, 0 mismatches file by file (14,749 files) and word for word (3,559,819 words); tools/test_repo.py 6 of 6.
- Corrections: none. No version main already held was changed; P-8.6 and A-1 get no new versions from the XML repository (it holds none after their last In-force day).

Batch 2:

- Breadth pass: 482 Acts (I-3.3 to I-19.3), each as one version, its current consolidation, dated by its lastAmendedDate: the oldest version available in this record for now.
- 46 of them are one file for the whole text (the reader could not split them): L-2, E-15, F-11, E-5.6, C-24, A-10.6, A-2.4, A-5, B-5.3, B-5.5, B-9.8594, B-9.8595, C-0.4, C-1.8, C-10.4, C-10.54, C-10.56, C-15.2, C-15.21, C-17.6, C-21.3, C-24.2, C-31.7, C-36.75, C-36.78, C-38.7, C-4.4, C-47.4, C-49, C-55.5, C-6.16, C-6.19, D-0.5, D-1.65, E-22, E-4.6, E-9.5, F-11.8, F-12, F-25, F-3, F-5.8, G-11.6, H-1, H-5.8, I-17.3.
- Checks on the appended repository: 482 versions file by file, 0 mismatches (29484 files); 482 word for word, 0 mismatches (7824082 words); tools/test_repo.py 6 of 6. Held back for now: 18.

Batch 3:

- Breadth pass: 454 Acts (I-19.7 to Z-041), each as one version, its current consolidation, dated by its lastAmendedDate: the oldest version available in this record for now.
- 73 of them are one file for the whole text (the reader could not split them): I-6, J-0.8, K-9.5, L-4, M-0.1, M-0.25, M-0.3, M-12.01, M-3.2, N-12, N-16.4, N-16.62, N-2.5, N-27, N-27.1, N-27.3, N-28, N-7, P-1.3, P-14, P-15.6, P-15.7, P-15.8, P-16.8, P-18, P-19.3, P-27.5, P-29.7, P-29.71, P-31.5, P-31.65, P-33, P-33.6, P-35, P-4.3, P-8.3, P-9, Q-1, R-3.3, R-7.36, S-1.04, S-10.2, S-11.5, S-12.8, S-13, S-15.34, S-15.9, S-27, S-7.2, S-9, T-10.47, T-11, T-15, U-3.5, U-3.7, V-1.4, V-3, W-11.8, W-12.3, W-6.2 and more.
- Checks on the appended repository: 454 versions file by file, 0 mismatches (15897 files); 454 word for word, 0 mismatches (3504066 words); tools/test_repo.py 6 of 6. Held back for now: 32.

Batch 4:

- Breadth pass: 416 regulations (SI-2000-100 to SI-2015-98), each as one version, its current consolidation, dated by its lastAmendedDate: the oldest version available in this record for now.
- 89 of them are one file for the whole text (the reader could not split them): SI-2002-123, SI-2002-142, SI-2002-46, SI-2002-58, SI-2003-107, SI-2003-130, SI-2003-148, SI-2003-149, SI-2003-156, SI-2003-244, SI-2003-38, SI-2003-58, SI-2004-109, SI-2004-122, SI-2004-132, SI-2004-134, SI-2004-153, SI-2004-34, SI-2005-113, SI-2005-120, SI-2005-124, SI-2005-17, SI-2006-141, SI-2006-142, SI-2006-23, SI-2006-28, SI-2006-31, SI-2006-32, SI-2006-37, SI-2006-38, SI-2006-39, SI-2006-4, SI-2006-40, SI-2006-98, SI-2007-101, SI-2007-102, SI-2007-103, SI-2007-68, SI-2007-69, SI-2007-80, SI-2008-102, SI-2008-103, SI-2008-104, SI-2008-136, SI-2008-15, SI-2008-16, SI-2008-20, SI-2008-26, SI-2008-27, SI-2008-53, SI-2008-55, SI-2009-104, SI-2010-18, SI-2010-83, SI-2010-84, SI-2011-109, SI-2011-111, SI-2011-48, SI-2011-58, SI-2011-9 and more.
- Checks on the appended repository: 416 versions file by file, 0 mismatches (1318 files); 416 word for word, 0 mismatches (590792 words); tools/test_repo.py 6 of 6. Held back for now: 616.

Batch 5:

- Breadth pass: 489 regulations (C.R.C.,_c._10 to C.R.C.,_c._812), each as one version, its current consolidation, dated by its lastAmendedDate: the oldest version available in this record for now.
- 133 of them are one file for the whole text (the reader could not split them): C.R.C.,_c._100, C.R.C.,_c._1013, C.R.C.,_c._1015, C.R.C.,_c._1023, C.R.C.,_c._1035, C.R.C.,_c._1041, C.R.C.,_c._1044, C.R.C.,_c._1105, C.R.C.,_c._1111, C.R.C.,_c._1114, C.R.C.,_c._1120, C.R.C.,_c._1126, C.R.C.,_c._1130, C.R.C.,_c._1134, C.R.C.,_c._1145, C.R.C.,_c._1146, C.R.C.,_c._1147, C.R.C.,_c._1151, C.R.C.,_c._1183, C.R.C.,_c._1236, C.R.C.,_c._1238, C.R.C.,_c._1240, C.R.C.,_c._1246, C.R.C.,_c._1253, C.R.C.,_c._1264, C.R.C.,_c._1266, C.R.C.,_c._1268, C.R.C.,_c._1270, C.R.C.,_c._1274, C.R.C.,_c._1283, C.R.C.,_c._1288, C.R.C.,_c._1296, C.R.C.,_c._1298, C.R.C.,_c._1314, C.R.C.,_c._1341, C.R.C.,_c._1342, C.R.C.,_c._1358, C.R.C.,_c._1359, C.R.C.,_c._1360, C.R.C.,_c._1367, C.R.C.,_c._1375, C.R.C.,_c._1376, C.R.C.,_c._1377, C.R.C.,_c._1378, C.R.C.,_c._1379, C.R.C.,_c._1380, C.R.C.,_c._1381, C.R.C.,_c._1382, C.R.C.,_c._1392, C.R.C.,_c._1393, C.R.C.,_c._1394, C.R.C.,_c._1400, C.R.C.,_c._1403, C.R.C.,_c._1404, C.R.C.,_c._1405, C.R.C.,_c._1407, C.R.C.,_c._1418, C.R.C.,_c._142, C.R.C.,_c._1422, C.R.C.,_c._1424 and more.
- Checks on the appended repository: 489 versions file by file, 0 mismatches (3656 files); 489 word for word, 0 mismatches (1406383 words); tools/test_repo.py 6 of 6. Held back for now: 60.

Batch 6:

- Breadth pass: 499 regulations (C.R.C.,_c._818 to SI-80-127), each as one version, its current consolidation, dated by its lastAmendedDate: the oldest version available in this record for now.
- 136 of them are one file for the whole text (the reader could not split them): C.R.C.,_c._854, C.R.C.,_c._869, C.R.C.,_c._889, C.R.C.,_c._890, C.R.C.,_c._910, C.R.C.,_c._911, C.R.C.,_c._915, C.R.C.,_c._923, C.R.C.,_c._924, C.R.C.,_c._927, C.R.C.,_c._929, C.R.C.,_c._930, C.R.C.,_c._931, C.R.C.,_c._932, C.R.C.,_c._933, C.R.C.,_c._934, C.R.C.,_c._945, C.R.C.,_c._957, C.R.C.,_c._96, C.R.C.,_c._961, C.R.C.,_c._986, SI-2016-19, SI-2016-20, SI-2016-29, SI-2016-43, SI-2017-11, SI-2017-12, SI-2017-15, SI-2017-4, SI-2017-45, SI-2017-46, SI-2017-6, SI-2017-7, SI-2017-8, SI-2017-9, SI-2018-103, SI-2018-104, SI-2018-105, SI-2018-13, SI-2018-14, SI-2018-16, SI-2018-34, SI-2018-51, SI-2018-58, SI-2018-59, SI-2018-60, SI-2018-61, SI-2018-62, SI-2018-63, SI-2018-67, SI-2018-68, SI-2018-70, SI-2018-73, SI-2018-75, SI-2018-76, SI-2018-77, SI-2018-78, SI-2018-79, SI-2018-80, SI-2018-86 and more.
- Checks on the appended repository: 499 versions file by file, 0 mismatches (1920 files); 499 word for word, 0 mismatches (1147966 words); tools/test_repo.py 6 of 6. Held back for now: 61.

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
10. **Breadth first (2026-11-02).** Every Act and regulation not yet in the record is first added as its current
    consolidation alone, in blocks of 500, labelled "oldest version available"; its earlier versions follow later, as
    labelled commits behind it. An Act the reader cannot split into sections is published as one file, `text.md`, rather
    than held back; it is checked word for word like the others.
11. **Order of the Acts:** the most-cited Acts first (Criminal Code, Income Tax Act, Canada Labour Code, Bank Act, ...),
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
