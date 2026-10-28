# Canada: law history

This repository will hold the legislation of Canada (CA) as a history: one file per provision and one commit per law taking effect, dated by the day it took force, with the law that made each change as the commit author. It follows the shared design of [lexifina/global-law](https://github.com/lexifina/global-law), which places it at `ca/` in the world tree.

**Status:** no law yet. This first commit records where the law of Canada can be read and what a build would need.

**Can it be built?** Ready to build: an official source has past versions by date and an API or bulk download.

**This commit is a placeholder.** The first real build must replace this history from scratch and force-push. It must never append law commits on top of it: they are dated by when each law took effect, often decades earlier, so dates in `main` would run backwards and break every on-date lookup. Builders should refuse to append when the root commit is this placeholder (its subject ends "sources, before any law").

**Official sources**

- [CanLII](https://www.canlii.org): Point-in-time federal and provincial statutes since 2009 with a compare view. The API needs a key and returns metadata only (5,000 requests a day).
- [Justice Laws Website](https://laws-lois.justice.gc.ca): Point-in-time acts from 2003 and regulations from 2006, with in-force ranges per section. Official since 2009.
- [Ontario e-Laws](https://www.ontario.ca/laws): Point-in-time from 1 January 2004. History tables were discontinued.
- [BC Laws](https://www.bclaws.gov.bc.ca): Open CiviX API with XML and point-in-time documents. The best sub-national API found.
- [LégisQuébec](https://www.legisquebec.gouv.qc.ca)
- [Manitoba Laws](https://web2.gov.mb.ca/laws)

**Existing open projects to check first**

- [legalize-ca](https://github.com/sandole/legalize-ca): Federal Acts, one dated commit per amendment.

These are volunteer projects. Reconcile any of them against the official text before relying on it: a transcription is not the law (c3e/grundgesetz, for example, differs from the official gazette in 43 article texts on 20 July 2017).

All sources, with their status, are in [SOURCES.md](SOURCES.md). How these files were made is in [REPRODUCE.md](REPRODUCE.md).

This repository describes sources; it is not legal advice and holds no legal text yet.
