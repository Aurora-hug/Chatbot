# CMRFU chatbot — initial source-backed evaluation set

This is a **first, formative test set** for the proposal's AI-assisted website search prototype. It contains **72 English questions**: 60 source-backed retrieval questions, four requests that need clarification, and eight that require a controlled fallback. The fixed split is 48 development cases and 24 holdout cases. Questions cover junior and senior bylaws, document discovery, 2026 dates/fixtures, and venue hire. No production chatbot or client acceptance is claimed here.

## Files

- [data/sources.json](data/sources.json): ten candidate source pages/documents with their exact URLs, document types, and access/approval status.
- [data/eval_v1.jsonl](data/eval_v1.jsonl): one labeled test question per line, with a short **paraphrased** gold answer, source ID, clause/section locator, expected response behavior, and split.
- [data/build_seed.py](data/build_seed.py): deterministic generator for the checked-in JSONL.
- [scripts/validate_dataset.py](scripts/validate_dataset.py): integrity and coverage checks.
- [scripts/fetch_sources.py](scripts/fetch_sources.py): optional, rate-limited source fetcher/extractor for a local development corpus.

Run:

```bash
python data/build_seed.py
python scripts/validate_dataset.py
python -m pip install PyMuPDF
python scripts/fetch_sources.py
```

The fetcher checks robots.txt, fetches only the ten listed HTTPS sources, limits file size, waits between requests, and skips inaccessible sources. Extracted text and the fetch report go into the ignored `corpus/` directory. It does **not** try to work around a 403 or access anything behind a login. In the initial research environment, several `cmrfu.co.nz` pages returned 403; some labels therefore use indexed excerpts of those official pages. The two bylaw PDFs and stadium pages were available for direct reading. A 403 or a robots restriction should be reported to the client and not bypassed.

## Provenance and approval

Source snapshot: **29 September 2026 (NZ time)**. The junior/senior PDFs are linked by CMRFU's [Forms & Documents](https://www.cmrfu.co.nz/forms-and-documents) page. CMRFU's Venue Hire navigation links to [Navigation Homes Stadium](https://www.navigationhomesstadium.co.nz/); that linked domain is included as a **candidate**, subject to explicit client approval. `access: indexed_excerpt` means a search-index rendering of an official page was checked, but a direct fetch was blocked; those labels require a manual recheck before a formal benchmark. All ten sources are marked `pending_confirmation`, because public visibility alone does not establish the client's approved retrieval collection.

The labels are short factual summaries, not copied pages or a legal/eligibility opinion. Time-dependent dates, capacities and contact details may change. Before formal evaluation, the team should obtain an approved source list, archive/version the source collection with hashes and retrieval timestamps, recheck indexed-only rows against the live source or a client-provided copy, and have a second reviewer verify answers and locators.

## Evaluation protocol

Index **only client-approved sources**. Use development rows for retrieval tuning and error analysis. Keep holdout rows untouched until an evaluation pass. For each answerable question, check whether the expected source appears in the top-k retrieved results, whether the answer is supported by the cited clause or section, whether the link opens, and whether the response avoids adding ungrounded interpretations. For clarification and fallback rows, check that the system refrains from inventing facts, booking a transaction, or deciding individual eligibility. Report counts by topic and behavior, source-validity failures, latency, and concrete failure examples. The proposal's 85% end-to-end success and five-second response targets are **final** targets on a client-agreed evaluation set, not a claimed result of this seed set.

The short answers and queries were authored from observed source content, not gathered from actual CMRFU user traffic. Extend them with client-approved realistic questions, hard negatives, paraphrases from independent reviewers, and source-version regression checks. Keep any new row traceable to its original clause, page, or page section.
