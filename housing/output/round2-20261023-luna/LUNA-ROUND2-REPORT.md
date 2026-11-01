# Luna round-two crawl audit

**Run:** `round2-20261023-luna`  
**Replay:** `round2-20261023-luna-replay`  
**Parser:** `round2.2`  
**Outcome:** bounded collection completed; verification remains incomplete.

## Collection result

The live run used the approved ceiling of 180 HTTP requests and collected 2,179 distinct listing URLs, 295 preferred exact-price candidates, 53 project-range overlaps, and 40 detail pages. These are listing-URL observations, not a count of unique dwellings. The four categories yielded 764 used houses, 800 used condos, 407 new houses, and 208 new-condo records. New condos had 198 project-level records; a project range is not an individual unit price.

Discovered route counts were 24 for used houses, 24 for used condos, 24 for new houses, and 18 for new condos. Osaka has 24 wards, so the new-condo route set did not cover six wards. The bounded run also recorded 22 listing attempts as `budget_exhausted`; those pages were not fetched. Missing routes and budget exhaustion do not mean zero inventory. The run summary reports 135 parsed listing pages, four successful discovery pages, and 40 successful details.

The acquisition log contains 180 responses with `fetched_at`; all 180 corresponding raw files exist and their SHA-256 values match the acquisition manifest. The runner uses a sequential fetch path and applies a discovered `Crawl-delay` when it exceeds the configured 3-second minimum. The recorded response-completion gaps range from 29.266 to 30.896 seconds. These are completion times, not request-start timestamps, so they do not independently prove exact start-to-start spacing.

## Offline replay

The replay was created in a fresh output folder with the requested 180/3/40/2 bounds. It ran from the original acquisitions and raw files; the runner reported `cache_replay` and **zero network requests** throughout.

The replay reproduces the live data exactly:

- 2,179 CSV rows and database observations, with identical listing URL sets and row contents;
- all observation payloads and `observed_at` timestamps;
- 40 detail records, including payloads and `fetched_at` timestamps;
- page status/timestamp records and acquisition status/timestamp/hash fields.

The detailed parity and raw-hash results are saved in `../round2-20261023-luna-replay/LUNA-ROUND2-AUDIT.json`. The audit script is alongside that file as `../round2-20261023-luna-replay/audit_replay.py`.

## Baseline protection scope

An older saved manifest exists at `../recrawl-20261013-20261013T133145677Z/inspection/baseline-protection-manifest.json`. Of its 64 listed files, 62 currently match the recorded lengths and hashes; the current `crawl_round2.py` and `crawl_round2_parse.py` differ from that older snapshot. That manifest covers the earlier pilot database, source files, and legacy cache entries. It does **not** contain the hash baseline for the prior 65-file Luna set. Therefore this audit makes no unchanged claim for that 65-file set.

## Limits

This was a bounded sample of discovered public routes, not a complete inventory. Listing fields and detail claims remain seller-advertised source statements; they were not checked against registries, management records, inspections, hazard maps, lenders, or government records. `verification_incomplete` is the runner's final state. Do not infer that a listing disappeared because it was not observed, or that an advertised property is legally, technically, or financially suitable.
