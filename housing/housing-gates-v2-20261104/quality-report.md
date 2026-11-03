# Quality report

Offline evaluation; no network requests. Counts are unique URLs unless stated.

```json
{
  "raw_row_count": 11463,
  "unique_url_count": 11463,
  "duplicate_row_count": 0,
  "divergent_duplicate_urls": 0,
  "conflict_urls": 126,
  "availability": {
    "active": 4787,
    "not_found": 7,
    "not_checked": 6668,
    "unverified": 1
  },
  "advertised_risks": {
    "private_road_claim": 40,
    "setback_claim": 20,
    "terrace_claim": 9,
    "tenanted_claim": 39,
    "no_rebuild_claim": 2,
    "leasehold_claim": 6
  },
  "dispositions": {
    "out_of_scope": 9394,
    "review_required": 1751,
    "scope_review": 7,
    "project_queue": 309,
    "unavailable": 2
  },
  "gates": {
    "G1:FAIL": 9394,
    "G2:REVIEW": 11463,
    "G3:NOT_EVALUATED": 11463,
    "G4:NOT_EVALUATED": 11463,
    "G5:NOT_EVALUATED": 11463,
    "G1:REVIEW": 2069
  },
  "baseline_exact_unique": 1754,
  "in_scope_unique": 1753,
  "baseline_only": 1,
  "in_scope_only": 0
}
```

- Catalog and link-check source dates are retained in evidence; this is not a current market crawl.
- Six new-condo routes were missing from source coverage.
- Private financial criteria remain under review.
- Views overlap; dispositions alone are mutually exclusive.
- Baseline exact-price counts differ from scope when evidence, project classification, price parsing, conflicts, or location are uncertain.
